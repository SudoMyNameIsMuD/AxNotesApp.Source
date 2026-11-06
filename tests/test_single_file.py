import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from uuid import UUID

import pytest

from AxNotes.cli import capture_inline_entry, interactive, main
from AxNotes.locks import file_lock
from AxNotes.index import rebuild, search
from AxNotes.index import sync as sync_index
from AxNotes.metadata import load_metadata
from AxNotes.migration import MigrationError, migrate_single_file
from AxNotes.models import EntryType, TaskState
from AxNotes.notebook import Notebook


def initialized_notebook(path):
    notebook = Notebook(path)
    notebook.initialize()
    return notebook


def test_file_lock_serializes_parallel_writers(tmp_path):
    lock_path = tmp_path / "serial.lock"
    events = []

    def worker(name):
        with file_lock(lock_path):
            events.append(f"start:{name}")
            time.sleep(0.05)
            events.append(f"finish:{name}")

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(worker, ["alpha", "beta"]))

    assert events[0].startswith("start:")
    assert events[1].startswith("finish:")
    assert events[2].startswith("start:")
    assert events[3].startswith("finish:")


def test_migration_preserves_entries_details_uuids_and_backup(tmp_path):
    notebook = initialized_notebook(tmp_path)
    first_day = date(2026, 11, 4)
    second_day = date(2026, 11, 5)
    notebook.append("First note", day=first_day)
    notebook.append("Open task", EntryType.TASK, first_day, TaskState.OPEN)
    notebook.append_detail("Task detail", first_day)
    notebook.append("In-progress task", EntryType.TASK, first_day, TaskState.IN_PROGRESS)
    notebook.append("Completed task", EntryType.TASK, first_day, TaskState.DONE)
    notebook.append("Migrated task", EntryType.TASK, first_day, TaskState.MIGRATED)
    notebook.append("Canceled task", EntryType.TASK, first_day, TaskState.CANCELED)
    notebook.append("Question", EntryType.QUESTION, first_day)
    notebook.append("Important entry", EntryType.IMPORTANT, first_day)
    notebook.append("Event", EntryType.EVENT, first_day)
    notebook.append("Second note", day=second_day)
    notebook.ensure_note(date(2026, 11, 3))
    notebook.sync_metadata()

    db = sqlite3.connect(notebook.index_path)
    with db:
        original_ids = {row[1]: row[0] for row in db.execute("SELECT id, text FROM entries")}
    db.close()

    count, notes_backup, metadata_backup = migrate_single_file(notebook)

    assert count == 10
    assert notes_backup == tmp_path / "notes.pre-single-file-backup"
    assert notes_backup.is_dir()
    assert notebook.notes_dir.is_dir()
    assert (metadata_backup / "metadata").is_dir()
    assert (metadata_backup / "AxNotes.toml").is_file()
    assert (tmp_path / "notebook.md").is_file()
    assert 'format = "single-file"' in (tmp_path / "AxNotes.toml").read_text(encoding="utf-8")
    migrated_markdown = (tmp_path / "notebook.md").read_text(encoding="utf-8")
    assert "##### General Notes" in migrated_markdown
    assert "#### TUESDAY | 03NOV26" in migrated_markdown

    metadata = load_metadata(notebook.single_file_metadata_path)
    assert len(metadata.entries) == 10
    assert {item.id for item in metadata.entries} == {
        UUID(value) for value in original_ids.values()
    }
    assert notebook.entries_for_day(first_day)[1].details == ["Task detail"]

    db = sqlite3.connect(notebook.index_path)
    with db:
        migrated_rows = db.execute("SELECT id, text FROM entries").fetchall()
    db.close()
    assert {text: identity for identity, text in migrated_rows} == original_ids
    assert search(notebook, "First note")


def test_single_file_capture_writes_atomically_and_syncs_metadata(tmp_path):
    notebook = initialized_notebook(tmp_path)
    notebook.single_file_path.write_text(
        "# AxNotes Notebook\n\n## 2026\n\n### November\n\n"
        "#### Thursday | 05NOV26\n\n##### General Notes\n- Existing note\n",
        encoding="utf-8",
    )
    config = (tmp_path / "AxNotes.toml").read_text(encoding="utf-8")
    (tmp_path / "AxNotes.toml").write_text(
        config.replace('version = "0.1"', 'version = "0.1"\nformat = "single-file"'),
        encoding="utf-8",
    )

    notebook.append("New note", day=date(2026, 11, 5))
    notebook.append_detail("New detail", day=date(2026, 11, 5))
    notebook.sync_metadata()

    entries = notebook.entries_for_day(date(2026, 11, 5))
    assert [entry.text for entry in entries] == ["Existing note", "New note"]
    assert entries[1].details == ["New detail"]
    metadata = load_metadata(notebook.single_file_metadata_path)
    assert len(metadata.entries) == 2
    assert rebuild(notebook) == 2


def test_single_file_interactive_capture_renders_in_cli(tmp_path):
    notebook = initialized_notebook(tmp_path)
    config = (tmp_path / "AxNotes.toml").read_text(encoding="utf-8")
    (tmp_path / "AxNotes.toml").write_text(
        config.replace('version = "0.1"', 'version = "0.1"\nformat = "single-file"'),
        encoding="utf-8",
    )
    outputs = []
    raw_inputs = iter(["Visible in CLI", "/quit"])

    assert (
        interactive(
            notebook,
            input_fn=lambda prompt="- ": next(raw_inputs),
            output_fn=outputs.append,
        )
        == 0
    )

    rendered_outputs = [output for output in outputs if "Visible in CLI" in output]
    assert len(rendered_outputs) == 1
    assert " -  Visible in CLI" in rendered_outputs[0]


def test_single_file_inserts_entries_under_their_date_in_chronological_order(tmp_path):
    notebook = initialized_notebook(tmp_path)
    notebook.single_file_path.write_text(
        "# AxNotes Notebook\n\n"
        "## 2026\n\n### November\n\n"
        "#### Thursday | 05NOV26\n\n##### General Notes\n- Later entry\n",
        encoding="utf-8",
    )
    config = (tmp_path / "AxNotes.toml").read_text(encoding="utf-8")
    (tmp_path / "AxNotes.toml").write_text(
        config.replace('version = "0.1"', 'version = "0.1"\nformat = "single-file"'),
        encoding="utf-8",
    )

    notebook.append("Earlier entry", day=date(2026, 11, 4))
    notebook.append("Other year entry", day=date(2025, 12, 31))

    content = notebook.single_file_path.read_text(encoding="utf-8")
    assert content.index("#### WEDNESDAY | 04NOV26") < content.index("#### Thursday | 05NOV26")
    assert content.index("## 2025") < content.index("## 2026")
    assert [entry.text for entry in notebook.entries_for_day(date(2026, 11, 4))] == [
        "Earlier entry"
    ]


def test_migration_refuses_existing_backup_without_touching_notebook(tmp_path):
    notebook = initialized_notebook(tmp_path)
    notebook.append("Keep me", day=date(2026, 11, 4))
    notes_backup = tmp_path / "notes.pre-single-file-backup"
    notes_backup.mkdir()

    with pytest.raises(MigrationError, match="backup already exists"):
        migrate_single_file(notebook)

    assert not notebook.single_file_path.exists()
    assert notebook.note_path(date(2026, 11, 4)).is_file()


def test_migration_command_is_explicit_and_reports_backups(tmp_path, monkeypatch, capsys):
    notebook = initialized_notebook(tmp_path)
    notebook.append("Migrate me", day=date(2026, 11, 4))
    monkeypatch.chdir(tmp_path)

    assert main(["migrate", "single-file"]) == 0

    output = capsys.readouterr().out
    assert "AxNotes migrated 1 entry to notebook.md." in output
    assert "notes.pre-single-file-backup" in output


def test_failed_index_rebuild_rolls_back_migration_installation(tmp_path, monkeypatch):
    notebook = initialized_notebook(tmp_path)
    notebook.append("Keep me", day=date(2026, 11, 4))

    def fail_rebuild(_notebook):
        raise OSError("simulated index failure")

    monkeypatch.setattr("AxNotes.index.rebuild", fail_rebuild)
    with pytest.raises(OSError, match="simulated index failure"):
        migrate_single_file(notebook)

    assert not notebook.single_file_path.exists()
    assert not notebook.single_file_metadata_path.exists()
    assert notebook.config.format == "daily-files"
    assert (tmp_path / "notes.pre-single-file-backup").is_dir()


def test_supporting_detail_capture_synchronizes_metadata_and_index(tmp_path, monkeypatch):
    notebook = initialized_notebook(tmp_path)
    day = date(2026, 11, 4)
    notebook.append("Parent entry", day=day)
    notebook.sync_metadata()
    sidecar = notebook.metadata_path_for_note(notebook.note_path(day))
    before = load_metadata(sidecar).entries[0]
    sync_calls = []

    def tracked_sync(value):
        sync_calls.append(value.root)
        sync_index(value)

    monkeypatch.setattr("AxNotes.index.sync", tracked_sync)
    capture_inline_entry(notebook, "Supporting information >", day=day)

    after = load_metadata(sidecar).entries[0]
    assert sync_calls == [tmp_path]
    assert after.id == before.id
    assert after.fingerprints["full"] != before.fingerprints["full"]
