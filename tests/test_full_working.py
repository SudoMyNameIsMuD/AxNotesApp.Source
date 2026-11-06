import sqlite3
from datetime import date, timedelta
from uuid import UUID

from AxNotes.cli import interactive
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
    value.append("Open task", EntryType.TASK, day, TaskState.OPEN)
    value.append_detail("Supporting detail", day)
    raw = value.note_path(day).read_text(encoding="utf-8")
    assert "<!--" not in raw
    rendered = value.render_day(day, render_entry)
    assert " -  Normal note" in rendered
    assert "[ ] Open task" in rendered
    assert "     › Supporting detail" in rendered


def test_quick_entry_notation_normalizes_existing_shortcuts():
    assert normalize_entry("[ Open task") == (EntryType.TASK, "Open task", TaskState.OPEN)
    assert normalize_entry("Completed task [x") == (
        EntryType.TASK,
        "Completed task",
        TaskState.DONE,
    )
    assert normalize_entry("Important entry !")[0] is EntryType.IMPORTANT
    assert normalize_entry("Question ?")[0] is EntryType.QUESTION
    assert normalize_detail("> Supporting detail") == "Supporting detail"


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


def test_inline_capture_writes_one_markdown_entry_and_renders_default_today_view(tmp_path):
    value = notebook(tmp_path)
    outputs = []
    raw_inputs = iter(["hello", "/quit"])
    interactive(value, input_fn=lambda prompt="- ": next(raw_inputs), output_fn=outputs.append)

    lines = value.note_path(date.today()).read_text(encoding="utf-8").splitlines()
    entry_lines = [line for line in lines if line.startswith(("- ", "! ", "? "))]
    assert len(entry_lines) == 1
    assert entry_lines[0].endswith("hello")
    rendered_outputs = [item for item in outputs if "hello" in item]
    assert len(rendered_outputs) == 1
    assert " -  hello" in rendered_outputs[0]


def test_inline_capture_prints_validation_errors(tmp_path):
    value = notebook(tmp_path)
    outputs = []
    raw_inputs = iter(["-", "/quit"])
    interactive(value, input_fn=lambda prompt="- ": next(raw_inputs), output_fn=outputs.append)

    assert any("Entry text cannot be empty." in item for item in outputs)


def test_commands_render_inline_then_return_to_prompt(tmp_path):
    value = notebook(tmp_path)
    value.append("Visible note", day=date.today())
    outputs = []
    raw_inputs = iter(["/today", "/quit"])
    interactive(value, input_fn=lambda prompt="- ": next(raw_inputs), output_fn=outputs.append)

    assert any("Visible note" in item for item in outputs)
    assert outputs[-1] == "AxNotes closed."


def test_rendered_views_wrap_entries_and_details_under_text(tmp_path):
    value = notebook(tmp_path)
    day = date.today()
    value.append("This is a very long note that should wrap across multiple lines while staying aligned under the entry text.", day=day)
    value.append_detail("This is a very long detail that should wrap beneath the detail marker without collapsing the alignment.", day=day)

    rendered = value.render_day(day, render_entry)
    lines = rendered.splitlines()
    assert any(line.startswith(" -  This is a very long note") for line in lines)
    assert any(line.startswith("    staying aligned under the entry text.") for line in lines)
    assert any("This is a very long detail" in line for line in lines)
    assert any(line.startswith("       without collapsing the alignment.") for line in lines)


def test_capture_rerenders_the_last_week_view(tmp_path):
    value = notebook(tmp_path)
    today = date.today()
    value.append("Earlier this week", day=today - timedelta(days=1))
    outputs = []
    raw_inputs = iter(["/week", "New week entry", "/quit"])
    interactive(value, input_fn=lambda prompt="- ": next(raw_inputs), output_fn=outputs.append)

    rendered_outputs = [item for item in outputs if "Earlier this week" in item]
    assert len(rendered_outputs) == 2
    assert all("New week entry" in item for item in rendered_outputs[1:])


def test_lastweek_and_month_views_render_recent_ranges(tmp_path):
    value = notebook(tmp_path)
    today = date.today()
    last_week = today - timedelta(days=today.weekday() + 7)
    value.append("Last weekend note", day=last_week)
    value.append("This month note", day=today.replace(day=1))

    last_week_view = value.render_lastweek(today, render_entry)
    month_view = value.render_month(today, render_entry)

    assert "Last weekend note" in last_week_view
    assert "# LAST WEEK |" in last_week_view
    assert "This month note" in month_view
    assert "# MONTH |" in month_view


def test_help_and_index_commands_use_standardized_terminology(tmp_path):
    value = notebook(tmp_path)
    outputs = []
    raw_inputs = iter(["/help", "/reindex", "/sync", "/quit"])
    interactive(value, input_fn=lambda prompt="- ": next(raw_inputs), output_fn=outputs.append)

    help_output = next(item for item in outputs if item.startswith("\nCommands"))
    assert "/reindex   Rebuild the derived index" in help_output
    assert (
        "/sync      Refresh the derived index from authoritative Markdown and metadata sidecars"
        in help_output
    )
    assert "/markdown  Open notebook.md in the default Markdown app" in help_output
    assert "/lastweek  Show last week's entries" in help_output
    assert "/month     Show this month's entries" in help_output
    assert "Derived index rebuilt: 0 entries" in outputs
    assert "Derived index synchronized." in outputs


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
