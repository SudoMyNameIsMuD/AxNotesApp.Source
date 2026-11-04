import sqlite3
from datetime import date
from uuid import UUID

from AxNotes.fingerprints import fingerprint_entry
from AxNotes.index import rebuild, search
from AxNotes.interaction import normalize_detail, normalize_entry
from AxNotes.metadata import MetadataEntry, MetadataFile, write_metadata
from AxNotes.models import Entry, EntryType, TaskState
from AxNotes.notebook import Notebook
from AxNotes.renderer import render_entry


def notebook(tmp_path):
    value = Notebook(tmp_path)
    value.initialize()
    return value


def test_init_new_layout(tmp_path):
    value = notebook(tmp_path)
    assert value.notes_dir.is_dir()
    assert value.metadata_dir.is_dir()
    assert not (tmp_path / "daily").exists()


def test_clean_capture_and_render(tmp_path):
    value = notebook(tmp_path)
    day = date.today()
    value.append("Normal note", day=day)
    value.append("Task", EntryType.TASK, day, TaskState.OPEN)
    value.append_detail("Detail", day)
    raw = value.note_path(day).read_text(encoding="utf-8")
    assert "<!--" not in raw
    rendered = value.render_day(day, render_entry)
    assert " -  Normal note" in rendered
    assert "[ ] Task" in rendered
    assert "     › Detail" in rendered


def test_interaction_shortcuts():
    assert normalize_entry("[ task") == (EntryType.TASK, "task", TaskState.OPEN)
    assert normalize_entry("task [x") == (EntryType.TASK, "task", TaskState.DONE)
    assert normalize_entry("important !")[0] is EntryType.IMPORTANT
    assert normalize_entry("question ?")[0] is EntryType.QUESTION
    assert normalize_detail("> detail") == "detail"


def test_index_uses_notes_and_searches(tmp_path):
    value = notebook(tmp_path)
    value.append("Find me", day=date.today())
    assert rebuild(value) == 1
    assert search(value, "Find me")[0]["text"] == "Find me"


def test_sqlite_connection_is_released(tmp_path):
    value = notebook(tmp_path)
    value.append("Needle", day=date.today())
    assert search(value, "Needle")
    value.index_path.unlink()
    assert not value.index_path.exists()


def test_rebuild_from_markdown_and_metadata_preserves_identity(tmp_path):
    value = notebook(tmp_path)
    day = date(2026, 11, 4)
    value.append("Keep me", day=day)
    sidecar = value.metadata_path_for_note(value.note_path(day))
    fingerprints = fingerprint_entry(Entry(EntryType.NOTE, "Keep me"))
    identity = UUID("12345678-1234-5678-1234-567812345678")
    write_metadata(
        sidecar,
        MetadataFile(
            schema_version=1,
            entries=(
                MetadataEntry(
                    id=identity,
                    source=f"notes/{day.isoformat()}.md",
                    source_date=day,
                    ordinal=1,
                    fingerprints={
                        "full": fingerprints.full,
                        "content": fingerprints.content,
                        "parent": fingerprints.parent,
                        "text": fingerprints.text,
                    },
                ),
            ),
        ),
    )

    value.index_path.unlink(missing_ok=True)
    count = rebuild(value)
    assert count == 1
    with sqlite3.connect(value.index_path) as db:
        row = db.execute("SELECT id, text FROM entries WHERE source_file=?", (f"notes/{day.isoformat()}.md",)).fetchone()
    assert row[0] == str(identity)
    assert row[1] == "Keep me"
