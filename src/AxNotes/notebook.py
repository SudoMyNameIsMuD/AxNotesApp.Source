from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from uuid import UUID

from .config import DEFAULT_CONFIG, Config
from .fingerprints import fingerprint_entry
from .locks import file_lock, notebook_lock_path
from .metadata import (
    MetadataEntry,
    MetadataFile,
    MetadataNotFoundError,
    load_metadata,
    write_metadata,
)
from .models import TASK_MARKERS, Entry, EntryType, TaskState
from .parser import parse_file
from .reconcile import reconcile
from .renderer import render_detail, render_entry
from .single_file import append_to_notebook, parse_notebook

STORAGE_PREFIXES = {
    EntryType.NOTE: "-",
    EntryType.IMPORTANT: "!",
    EntryType.QUESTION: "?",
    EntryType.DECISION: "!",
    EntryType.EVENT: "@",
}


@dataclass(slots=True)
class Notebook:
    root: Path

    @property
    def config(self):
        return Config.load(self.root)

    @property
    def notes_dir(self):
        return self.root / self.config.notes_directory

    @property
    def state_dir(self):
        return self.root / ".AxNotes"

    @property
    def metadata_dir(self):
        return self.root / self.config.metadata_directory

    @property
    def index_path(self):
        return self.state_dir / "index.sqlite3"

    @property
    def single_file_path(self):
        return self.root / "notebook.md"

    @property
    def single_file_metadata_path(self):
        return self.metadata_dir / "notebook.json"

    @property
    def lock_path(self):
        return notebook_lock_path(self.root)

    @property
    def uses_single_file(self):
        return self.config.format == "single-file"

    def metadata_path_for_source(self, source: str | Path) -> Path:
        relative = Path(str(source).replace("\\", "/"))
        target = self.metadata_dir / relative.with_suffix(".json")
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def metadata_path_for_note(self, note_path: Path) -> Path:
        source = str(note_path.relative_to(self.root)).replace("\\", "/")
        return self.metadata_path_for_source(source)

    def load_metadata_for_note(self, note_path: Path) -> MetadataFile:
        sidecar = self.metadata_path_for_note(note_path)
        if not sidecar.exists():
            return MetadataFile(schema_version=1, entries=())
        try:
            return load_metadata(sidecar)
        except MetadataNotFoundError:
            return MetadataFile(schema_version=1, entries=())

    def reconcile_note_file(self, note_path: Path):
        source = str(note_path.relative_to(self.root)).replace("\\", "/")
        entries = parse_file(note_path)
        prior = self.load_metadata_for_note(note_path)
        previous = [{"id": item.id, "fingerprints": item.fingerprints} for item in prior.entries]
        current = [
            {
                "id": None,
                "entry_type": entry.entry_type,
                "text": entry.text,
                "task_state": entry.task_state,
                "details": entry.details,
                "fingerprints": fingerprint_entry(entry),
            }
            for entry in entries
        ]
        result = reconcile(previous, current)

        resolved_entries = []
        for match in result.matches:
            entry = entries[match.new_index]
            fingerprint = fingerprint_entry(entry)
            identity = match.new_identity if match.new_identity is not None else UUID(int=0)
            if isinstance(identity, UUID):
                entry_id = identity
            else:
                entry_id = UUID(str(identity))
            resolved_entries.append(
                MetadataEntry(
                    id=entry_id,
                    source=source,
                    source_date=date.fromisoformat(note_path.stem) if note_path.stem.count("-") == 2 else date.today(),
                    ordinal=match.new_index + 1,
                    fingerprints={
                        "full": fingerprint.full,
                        "content": fingerprint.content,
                        "parent": fingerprint.parent,
                        "text": fingerprint.text,
                    },
                )
            )

        sidecar = self.metadata_path_for_note(note_path)
        write_metadata(sidecar, MetadataFile(schema_version=1, entries=tuple(resolved_entries)))
        return result

    def sync_metadata(self):
        with file_lock(self.lock_path):
            if self.uses_single_file:
                self.reconcile_single_file()
                from . import index
                index.sync(self)
                return

            for note_path in sorted(self.notes_dir.glob("*.md")):
                self.reconcile_note_file(note_path)

            from . import index

            index.sync(self)

    def reconcile_single_file(self):
        records = parse_notebook(
            self.single_file_path.read_text(encoding="utf-8"),
            self.config.heading_format,
        )
        prior = (
            load_metadata(self.single_file_metadata_path)
            if self.single_file_metadata_path.exists()
            else MetadataFile(schema_version=1, entries=())
        )
        previous = [{"id": item.id, "fingerprints": item.fingerprints} for item in prior.entries]
        current = []
        for record in records:
            if record.day is None:
                raise ValueError(
                    f"Entry on line {record.line_number} is not under a valid day heading."
                )
            current.append(
                {
                    "id": None,
                    "entry_type": record.entry.entry_type,
                    "text": record.entry.text,
                    "task_state": record.entry.task_state,
                    "details": record.entry.details,
                    "fingerprints": fingerprint_entry(record.entry),
                }
            )
        result = reconcile(previous, current)

        resolved_entries = []
        for match in result.matches:
            record = records[match.new_index]
            fingerprint = fingerprint_entry(record.entry)
            identity = match.new_identity
            entry_id = identity if isinstance(identity, UUID) else UUID(str(identity))
            resolved_entries.append(
                MetadataEntry(
                    id=entry_id,
                    source="notebook.md",
                    source_date=record.day,
                    ordinal=record.ordinal,
                    fingerprints={
                        "full": fingerprint.full,
                        "content": fingerprint.content,
                        "parent": fingerprint.parent,
                        "text": fingerprint.text,
                    },
                )
            )
        write_metadata(
            self.single_file_metadata_path,
            MetadataFile(schema_version=1, entries=tuple(resolved_entries)),
        )
        return result

    def initialize(self):
        self.root.mkdir(parents=True, exist_ok=True)
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        config = self.root / "AxNotes.toml"
        if not config.exists():
            config.write_text(DEFAULT_CONFIG, encoding="utf-8", newline="\n")

    def validate(self):
        if not (self.root / "AxNotes.toml").exists():
            raise FileNotFoundError("AxNotes notebook not found. Run 'AxNotes init' first.")

    def note_path(self, day: date):
        return self.notes_dir / f"{day.strftime(self.config.date_format)}.md"

    def heading(self, day: date):
        return f"# {day.strftime(self.config.heading_format).upper()}"

    def ensure_note(self, day: date):
        if self.uses_single_file:
            if not self.single_file_path.exists():
                from .single_file import atomic_write_text

                atomic_write_text(self.single_file_path, "# AxNotes Notebook\n")
            return self.single_file_path
        path = self.note_path(day)
        if not path.exists():
            path.write_text(
                f"---\ntype: daily\ndate: {day.isoformat()}\n---\n\n{self.heading(day)}\n\n",
                encoding="utf-8",
                newline="\n",
            )
        return path

    def append(self, text: str, entry_type=EntryType.NOTE, day=None, task_state=TaskState.OPEN):
        clean = " ".join(text.strip().splitlines()).strip()
        if not clean or (entry_type is EntryType.NOTE and clean == "-"):
            raise ValueError("Entry text cannot be empty.")
        day = day or date.today()
        prefix = TASK_MARKERS[task_state] if entry_type is EntryType.TASK else STORAGE_PREFIXES[entry_type]
        path = self.ensure_note(day)
        if self.uses_single_file:
            append_to_notebook(
                path,
                day,
                f"{prefix} {clean}",
                self.config.heading_format,
            )
            return path
        with file_lock(self.lock_path):
            with path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(f"{prefix} {clean}\n")
        return path

    def append_detail(self, text: str, day=None):
        clean = " ".join(text.strip().splitlines()).strip()
        if not clean:
            raise ValueError("Detail text cannot be empty.")
        day = day or date.today()
        path = self.ensure_note(day)
        if self.uses_single_file:
            append_to_notebook(path, day, f"  › {clean}", self.config.heading_format)
            return path
        with file_lock(self.lock_path):
            with path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(f"  › {clean}\n")
        return path

    def entries_for_day(self, day: date) -> list[Entry]:
        if self.uses_single_file:
            text = self.single_file_path.read_text(encoding="utf-8")
            return [
                record.entry
                for record in parse_notebook(text, self.config.heading_format)
                if record.day == day
            ]
        path = self.note_path(day)
        return parse_file(path) if path.exists() else []

    def render_day(self, day: date, render_entry) -> str:
        lines = [self.heading(day), ""]
        for entry in self.entries_for_day(day):
            lines.append(render_entry(entry))
            lines.extend(render_detail(detail) for detail in entry.details)
        return "\n".join(lines).rstrip()

    def render_week(self, day: date, render_entry) -> str:
        start = day - timedelta(days=day.weekday())
        end = start + timedelta(days=6)
        lines = [f"# WEEK | {start.strftime('%d%b%y').upper()}–{end.strftime('%d%b%y').upper()}"]
        for offset in range(7):
            current = start + timedelta(days=offset)
            entries = self.entries_for_day(current)
            if not entries:
                continue
            lines.extend(["", f"## {current.strftime('%A | %d%b%y').upper()}"])
            for entry in entries:
                lines.append(render_entry(entry))
                lines.extend(render_detail(detail) for detail in entry.details)
        if len(lines) == 1:
            lines.extend(["", "No entries this week."])
        return "\n".join(lines)
