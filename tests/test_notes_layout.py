from datetime import date
from AxNotes.notebook import Notebook


def test_init_creates_minimal_notes_layout(tmp_path):
    notebook = Notebook(tmp_path)
    notebook.initialize()
    assert (tmp_path / "notes").is_dir()
    assert (tmp_path / ".AxNotes" / "metadata").is_dir()
    assert (tmp_path / "AxNotes.toml").is_file()
    assert not (tmp_path / "daily").exists()
    assert not (tmp_path / "projects").exists()
    assert not (tmp_path / "templates").exists()
    assert not (tmp_path / ".AxNotes" / "index.sqlite3").exists()


def test_new_note_file_lives_under_notes_and_is_clean(tmp_path):
    notebook = Notebook(tmp_path)
    notebook.initialize()
    path = notebook.append("Clean Markdown", day=date(2026, 11, 2))
    assert path == tmp_path / "notes" / "2026-11-02.md"
    text = path.read_text(encoding="utf-8")
    assert "- Clean Markdown" in text
    assert "<!--" not in text


def test_config_declares_notes_and_metadata_locations(tmp_path):
    notebook = Notebook(tmp_path)
    notebook.initialize()
    config = (tmp_path / "AxNotes.toml").read_text(encoding="utf-8")
    assert 'notes_directory = "notes"' in config
    assert 'directory = ".AxNotes/metadata"' in config
