from datetime import date

from AxNotes.index import rebuild, search
from AxNotes.interaction import normalize_detail, normalize_entry
from AxNotes.models import EntryType, TaskState
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
