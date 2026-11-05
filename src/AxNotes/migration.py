import os
import re
import shutil
import sqlite3
import uuid
from datetime import date, datetime
from pathlib import Path
from uuid import UUID, uuid4

from .fingerprints import fingerprint_entry
from .metadata import (
    MetadataEntry,
    MetadataFile,
    load_metadata,
    write_metadata,
)
from .models import Entry
from .notebook import Notebook
from .parser import parse_file
from .single_file import NotebookRecord, atomic_write_text, parse_notebook, render_notebook


class MigrationError(Exception):
    """Raised when a notebook cannot be safely migrated."""


def _backup(notebook: Notebook) -> tuple[Path, Path]:
    notes_backup = notebook.root / "notes.pre-single-file-backup"
    if notes_backup.exists():
        raise MigrationError(
            f"Migration backup already exists: {notes_backup.name}. "
            "Preserve or rename it before retrying."
        )

    backup_root = notebook.state_dir / "backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    backup_path = backup_root / (
        "single-file-migration-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    )
    if backup_path.exists():
        raise MigrationError("A migration backup with the generated name already exists.")

    staging_id = uuid.uuid4().hex
    notes_staging = notebook.root / f".notes-backup-{staging_id}"
    archive_staging = backup_root / f".migration-backup-{staging_id}"
    try:
        shutil.copytree(notebook.notes_dir, notes_staging)
        archive_staging.mkdir()
        if notebook.metadata_dir.exists():
            shutil.copytree(notebook.metadata_dir, archive_staging / "metadata")
        shutil.copy2(notebook.root / "AxNotes.toml", archive_staging / "AxNotes.toml")
        os.replace(notes_staging, notes_backup)
        os.replace(archive_staging, backup_path)
    except BaseException:
        if notes_staging.exists():
            shutil.rmtree(notes_staging)
        if archive_staging.exists():
            shutil.rmtree(archive_staging)
        if notes_backup.exists() and not backup_path.exists():
            shutil.rmtree(notes_backup)
        raise
    return notes_backup, backup_path


def _read_sources(
    notebook: Notebook,
) -> list[tuple[date, Path, list[Entry], dict[int, UUID]]]:
    try:
        note_paths = sorted(
            notebook.notes_dir.glob("*.md"),
            key=lambda path: datetime.strptime(path.stem, notebook.config.date_format).date(),
        )
    except ValueError as error:
        raise MigrationError(
            f"Every Markdown filename under notes/ must be a valid date: {error}"
        ) from error
    if not note_paths:
        raise MigrationError("There are no dated Markdown files to migrate.")

    result = []
    seen_ids = set()
    for path in note_paths:
        day = datetime.strptime(path.stem, notebook.config.date_format).date()
        entries = parse_file(path)
        relative = path.relative_to(notebook.root).as_posix()
        metadata_path = notebook.metadata_dir / Path(relative).with_suffix(".json")
        identities: dict[int, UUID] = {}
        if metadata_path.exists():
            metadata = load_metadata(metadata_path)
            for item in metadata.entries:
                if item.source != relative or item.source_date != day:
                    raise MigrationError(f"Metadata source or date does not match {relative}.")
                if item.ordinal > len(entries):
                    raise MigrationError(f"Metadata has an unmatched entry in {metadata_path}.")
                fingerprint = fingerprint_entry(entries[item.ordinal - 1])
                actual = {
                    "full": fingerprint.full,
                    "content": fingerprint.content,
                    "parent": fingerprint.parent,
                    "text": fingerprint.text,
                }
                if item.fingerprints != actual:
                    raise MigrationError(
                        f"Metadata is stale for entry {item.ordinal} in {relative}; "
                        "synchronize the notebook before migration."
                    )
                if item.id in seen_ids:
                    raise MigrationError(f"Duplicate durable identity found in {relative}.")
                identities[item.ordinal] = item.id
                seen_ids.add(item.id)
            if len(identities) != len(entries):
                raise MigrationError(f"Metadata entry count does not match {relative}.")
        result.append((day, path, entries, identities))
    return result


def _metadata_for(records: list[NotebookRecord], identities: list[UUID]) -> MetadataFile:
    entries = []
    for record, identity in zip(records, identities, strict=True):
        if record.day is None:
            raise MigrationError("Migration validation failed: an entry has no day.")
        fingerprints = fingerprint_entry(record.entry)
        entries.append(
            MetadataEntry(
                id=identity,
                source="notebook.md",
                source_date=record.day,
                ordinal=record.ordinal,
                fingerprints={
                    "full": fingerprints.full,
                    "content": fingerprints.content,
                    "parent": fingerprints.parent,
                    "text": fingerprints.text,
                },
            )
        )
    return MetadataFile(schema_version=1, entries=tuple(entries))


def _single_file_config(original: str) -> str:
    lines = original.splitlines()
    notebook_start = next(
        (index for index, line in enumerate(lines) if line.strip() == "[notebook]"),
        None,
    )
    if notebook_start is None:
        raise MigrationError("AxNotes.toml is missing its [notebook] section.")
    notebook_end = next(
        (
            index
            for index in range(notebook_start + 1, len(lines))
            if lines[index].lstrip().startswith("[")
        ),
        len(lines),
    )
    format_line = next(
        (
            index
            for index in range(notebook_start + 1, notebook_end)
            if re.match(r"\s*format\s*=", lines[index])
        ),
        None,
    )
    if format_line is None:
        lines.insert(notebook_start + 1, 'format = "single-file"')
    else:
        lines[format_line] = 'format = "single-file"'
    return "\n".join(lines).rstrip() + "\n"


def migrate_single_file(notebook: Notebook) -> tuple[int, Path, Path]:
    notebook.validate()
    if notebook.config.format == "single-file" or notebook.single_file_path.exists():
        raise MigrationError("This notebook already uses the single-file format.")
    if not notebook.notes_dir.is_dir():
        raise MigrationError("The v0.1 notes/ directory does not exist.")
    if notebook.index_path.is_file() is False and notebook.index_path.exists():
        raise MigrationError("The derived index path is not a regular file.")
    if notebook.single_file_metadata_path.exists():
        raise MigrationError(
            "A notebook.json metadata sidecar already exists; refusing to overwrite it."
        )

    source_files = _read_sources(notebook)
    records: list[NotebookRecord] = []
    identities: list[UUID] = []
    for day, _, entries, source_identities in source_files:
        for ordinal, entry in enumerate(entries, start=1):
            records.append(NotebookRecord(entry, day, 0, len(records) + 1))
            identities.append(
                source_identities[ordinal] if ordinal in source_identities else uuid4()
            )

    source_days = [day for day, _, _, _ in source_files]
    markdown = render_notebook(records, source_days, notebook.config.heading_format)
    parsed_destination = parse_notebook(markdown, notebook.config.heading_format)
    if len(parsed_destination) != len(records):
        raise MigrationError("Migration validation failed: entry counts do not match.")
    if any(
        record.day != parsed.day or record.entry != parsed.entry
        for record, parsed in zip(records, parsed_destination, strict=True)
    ):
        raise MigrationError(
            "Migration validation failed: entries, dates, or supporting details changed."
        )

    destination_metadata = _metadata_for(records, identities)
    MetadataFile.from_json(destination_metadata.to_json())
    notes_backup, metadata_backup = _backup(notebook)

    staging = notebook.root / f".single-file-migration-{uuid.uuid4().hex}"
    staging.mkdir()
    staged_markdown = staging / "notebook.md"
    staged_metadata = staging / "notebook.json"
    notebook_path = notebook.single_file_path
    metadata_path = notebook.single_file_metadata_path
    original_config = (notebook.root / "AxNotes.toml").read_text(encoding="utf-8")
    staged_config = _single_file_config(original_config)
    installed_notebook = False
    installed_metadata = False
    switched_config = False
    try:
        atomic_write_text(staged_markdown, markdown)
        write_metadata(staged_metadata, destination_metadata)
        if len(
            parse_notebook(
                staged_markdown.read_text(encoding="utf-8"), notebook.config.heading_format
            )
        ) != len(records):
            raise MigrationError("Staged notebook validation failed.")
        if load_metadata(staged_metadata) != destination_metadata:
            raise MigrationError("Staged metadata validation failed.")

        os.replace(staged_markdown, notebook_path)
        installed_notebook = True
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staged_metadata, metadata_path)
        installed_metadata = True
        atomic_write_text(notebook.root / "AxNotes.toml", staged_config)
        switched_config = True

        from .index import rebuild

        indexed_count = rebuild(notebook)
        if indexed_count != len(records):
            raise MigrationError(
                "Migration validation failed: derived index entry count does not match."
            )
        db = sqlite3.connect(notebook.index_path)
        with db:
            indexed_identities = db.execute(
                "SELECT id, ordinal FROM entries ORDER BY ordinal"
            ).fetchall()
        db.close()
        expected_identities = [
            (str(identity), ordinal) for ordinal, identity in enumerate(identities, start=1)
        ]
        if indexed_identities != expected_identities:
            raise MigrationError(
                "Migration validation failed: derived index identities do not match."
            )
    except BaseException:
        if switched_config:
            atomic_write_text(notebook.root / "AxNotes.toml", original_config)
        if installed_metadata:
            metadata_path.unlink(missing_ok=True)
        if installed_notebook:
            notebook_path.unlink(missing_ok=True)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)

    return len(records), notes_backup, metadata_backup
