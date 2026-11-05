from datetime import date

import pytest

from AxNotes.cli import capture_inline_entry
from AxNotes.interaction import normalize_detail, normalize_entry
from AxNotes.models import TASK_MARKERS, EntryType, TaskState
from AxNotes.notebook import Notebook


@pytest.mark.parametrize(
    ("raw", "entry_type", "text", "task_state", "markdown"),
    [
        (
            "[ Follow up with John Doe",
            EntryType.TASK,
            "Follow up with John Doe",
            TaskState.OPEN,
            "[ ] Follow up with John Doe",
        ),
        (
            "[ ] Follow up with John Doe",
            EntryType.TASK,
            "Follow up with John Doe",
            TaskState.OPEN,
            "[ ] Follow up with John Doe",
        ),
        (
            "[/] Follow up with John Doe",
            EntryType.TASK,
            "Follow up with John Doe",
            TaskState.IN_PROGRESS,
            "[/] Follow up with John Doe",
        ),
        (
            "Follow up with John Doe [/]",
            EntryType.TASK,
            "Follow up with John Doe",
            TaskState.IN_PROGRESS,
            "[/] Follow up with John Doe",
        ),
        (
            "Follow up with John Doe [x",
            EntryType.TASK,
            "Follow up with John Doe",
            TaskState.DONE,
            "[x] Follow up with John Doe",
        ),
        (
            "[x] Follow up with John Doe",
            EntryType.TASK,
            "Follow up with John Doe",
            TaskState.DONE,
            "[x] Follow up with John Doe",
        ),
        (
            "Follow up with John Doe [>",
            EntryType.TASK,
            "Follow up with John Doe",
            TaskState.MIGRATED,
            "[>] Follow up with John Doe",
        ),
        (
            "[>] Follow up with John Doe",
            EntryType.TASK,
            "Follow up with John Doe",
            TaskState.MIGRATED,
            "[>] Follow up with John Doe",
        ),
        (
            "Follow up with John Doe [-",
            EntryType.TASK,
            "Follow up with John Doe",
            TaskState.CANCELED,
            "[-] Follow up with John Doe",
        ),
        (
            "[-] Follow up with John Doe",
            EntryType.TASK,
            "Follow up with John Doe",
            TaskState.CANCELED,
            "[-] Follow up with John Doe",
        ),
        (
            "? Does John Doe need the report?",
            EntryType.QUESTION,
            "Does John Doe need the report?",
            None,
            "? Does John Doe need the report?",
        ),
        (
            "Does John Doe need the report ? ",
            EntryType.QUESTION,
            "Does John Doe need the report",
            None,
            "? Does John Doe need the report",
        ),
        (
            "! John Doe needs the report",
            EntryType.IMPORTANT,
            "John Doe needs the report",
            None,
            "! John Doe needs the report",
        ),
        (
            "John Doe needs the report !",
            EntryType.IMPORTANT,
            "John Doe needs the report",
            None,
            "! John Doe needs the report",
        ),
        (
            "@ Meeting with John Doe",
            EntryType.EVENT,
            "Meeting with John Doe",
            None,
            "@ Meeting with John Doe",
        ),
        (
            "Meeting with John Doe @",
            EntryType.EVENT,
            "Meeting with John Doe",
            None,
            "@ Meeting with John Doe",
        ),
        ("> Confirm the due date", None, "Confirm the due date", None, "  › Confirm the due date"),
        ("Confirm the due date >", None, "Confirm the due date", None, "  › Confirm the due date"),
    ],
)
def test_quick_entry_normalization_and_canonical_markdown(
    tmp_path, raw, entry_type, text, task_state, markdown
):
    normalized_type, normalized_text, normalized_state = (
        normalize_entry(raw)
        if entry_type
        else (
            None,
            normalize_detail(raw),
            None,
        )
    )
    assert (normalized_type, normalized_text, normalized_state) == (entry_type, text, task_state)

    notebook = Notebook(tmp_path)
    notebook.initialize()
    capture_inline_entry(notebook, raw)
    stored = notebook.note_path(date.today()).read_text(encoding="utf-8")
    assert markdown in stored.splitlines()


@pytest.mark.parametrize(
    ("raw", "task_state", "markdown"),
    [
        ("[ Follow up with John Doe", TaskState.OPEN, "[ ] Follow up with John Doe"),
        ("[ ] Follow up with John Doe", TaskState.OPEN, "[ ] Follow up with John Doe"),
        ("[/ Follow up with John Doe", TaskState.IN_PROGRESS, "[/] Follow up with John Doe"),
        ("[/] Follow up with John Doe", TaskState.IN_PROGRESS, "[/] Follow up with John Doe"),
        ("Follow up with John Doe [/ ", TaskState.IN_PROGRESS, "[/] Follow up with John Doe"),
        ("Follow up with John Doe [/] ", TaskState.IN_PROGRESS, "[/] Follow up with John Doe"),
        ("[x Follow up with John Doe", TaskState.DONE, "[x] Follow up with John Doe"),
        ("[x] Follow up with John Doe", TaskState.DONE, "[x] Follow up with John Doe"),
        ("Follow up with John Doe [x", TaskState.DONE, "[x] Follow up with John Doe"),
        ("Follow up with John Doe [x]", TaskState.DONE, "[x] Follow up with John Doe"),
        ("[> Follow up with John Doe", TaskState.MIGRATED, "[>] Follow up with John Doe"),
        ("[>] Follow up with John Doe", TaskState.MIGRATED, "[>] Follow up with John Doe"),
        ("Follow up with John Doe [>", TaskState.MIGRATED, "[>] Follow up with John Doe"),
        ("Follow up with John Doe [>]", TaskState.MIGRATED, "[>] Follow up with John Doe"),
        ("[- Follow up with John Doe", TaskState.CANCELED, "[-] Follow up with John Doe"),
        ("[-] Follow up with John Doe", TaskState.CANCELED, "[-] Follow up with John Doe"),
        ("Follow up with John Doe [-", TaskState.CANCELED, "[-] Follow up with John Doe"),
        ("Follow up with John Doe [-]", TaskState.CANCELED, "[-] Follow up with John Doe"),
    ],
)
def test_task_shortcuts_normalize_to_canonical_markdown(tmp_path, raw, task_state, markdown):
    entry_type, text, normalized_state = normalize_entry(raw)
    assert entry_type is EntryType.TASK
    assert text == "Follow up with John Doe"
    assert normalized_state is task_state

    notebook = Notebook(tmp_path)
    notebook.initialize()
    capture_inline_entry(notebook, raw)
    stored = notebook.note_path(date.today()).read_text(encoding="utf-8")
    assert stored.splitlines().count(markdown) == 1


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "-",
        "[",
        "[x",
        "[/",
        "[>",
        "[-",
        "!",
        "?",
        "@",
        ">",
    ],
)
def test_empty_quick_entry_notation_is_rejected(raw):
    if raw == ">":
        with pytest.raises(ValueError, match="Supporting detail text cannot be empty"):
            normalize_detail(raw)
    else:
        with pytest.raises(ValueError):
            normalize_entry(raw)


@pytest.mark.parametrize("raw", ["[", "[x", "[/", "[>", "[-", "!", "?", "@", ">"])
def test_empty_markers_do_not_create_entries(tmp_path, raw):
    notebook = Notebook(tmp_path)
    notebook.initialize()

    with pytest.raises(ValueError):
        capture_inline_entry(notebook, raw)

    assert not list(notebook.notes_dir.glob("*.md"))


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "  Follow up with John Doe [x  ",
            (EntryType.TASK, "Follow up with John Doe", TaskState.DONE),
        ),
        (
            "  ! Keep [x and ? inside text  ",
            (EntryType.IMPORTANT, "Keep [x and ? inside text", None),
        ),
        (
            "Does John Doe need the report?",
            (EntryType.NOTE, "Does John Doe need the report?", None),
        ),
        ("Call John Doe at 5pm!", (EntryType.NOTE, "Call John Doe at 5pm!", None)),
    ],
)
def test_normalization_preserves_whitespace_boundaries_and_meaningful_punctuation(raw, expected):
    assert normalize_entry(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "Follow up with John Doe [x",
        "Follow up with John Doe [/]",
        "Follow up with John Doe [>",
        "John Doe needs the report !",
        "Meeting with John Doe @",
        "Confirm the due date >",
        "Does John Doe need the report?",
    ],
)
def test_repeated_normalization_is_stable(raw):
    supporting_detail = normalize_detail(raw)
    if supporting_detail is not None:
        assert normalize_detail(f"> {supporting_detail}") == supporting_detail
        return

    entry_type, text, task_state = normalize_entry(raw)
    if entry_type is EntryType.TASK:
        marker = TASK_MARKERS[task_state]
    elif entry_type is EntryType.NOTE:
        marker = ""
    else:
        marker = {
            EntryType.IMPORTANT: "!",
            EntryType.QUESTION: "?",
            EntryType.EVENT: "@",
        }[entry_type]
    canonical_input = f"{marker} {text}" if marker else text
    assert normalize_entry(canonical_input) == (entry_type, text, task_state)
