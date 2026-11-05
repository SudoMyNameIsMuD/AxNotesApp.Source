from .models import EntryType, TaskState

COMMANDS = ("today", "week", "search", "reindex", "sync", "help", "quit")

LEADING_TASK_MARKERS = (
    ("[ ]", TaskState.OPEN),
    ("[/]", TaskState.IN_PROGRESS),
    ("[/", TaskState.IN_PROGRESS),
    ("[x]", TaskState.DONE),
    ("[X]", TaskState.DONE),
    ("[x", TaskState.DONE),
    ("[X", TaskState.DONE),
    ("[>]", TaskState.MIGRATED),
    ("[>", TaskState.MIGRATED),
    ("[-]", TaskState.CANCELED),
    ("[-", TaskState.CANCELED),
    ("[", TaskState.OPEN),
)
TRAILING_TASK_MARKERS = (
    ("[ ]", TaskState.OPEN),
    ("[/]", TaskState.IN_PROGRESS),
    ("[/", TaskState.IN_PROGRESS),
    ("[x]", TaskState.DONE),
    ("[X]", TaskState.DONE),
    ("[x", TaskState.DONE),
    ("[X", TaskState.DONE),
    ("[>]", TaskState.MIGRATED),
    ("[>", TaskState.MIGRATED),
    ("[-]", TaskState.CANCELED),
    ("[-", TaskState.CANCELED),
)
TYPE_MARKERS = {
    "!": EntryType.IMPORTANT,
    "?": EntryType.QUESTION,
    "@": EntryType.EVENT,
}


def _strip_trailing_marker(value: str, marker: str) -> str | None:
    if not value.endswith(marker):
        return None
    marker_start = len(value) - len(marker)
    if marker_start == 0 or not value[marker_start - 1].isspace():
        return None
    return value[:marker_start].rstrip()


def normalize_entry(raw: str) -> tuple[EntryType, str, TaskState | None]:
    value = raw.strip()
    if not value or value == "-":
        raise ValueError("Entry text cannot be empty.")

    task_state = None
    for marker, state in LEADING_TASK_MARKERS:
        if value.startswith(marker):
            task_state = state
            value = value[len(marker) :].lstrip()
            break

    for marker, state in TRAILING_TASK_MARKERS:
        text = _strip_trailing_marker(value, marker)
        if text is not None:
            if task_state is None:
                task_state = state
            value = text
            break

    if task_state is not None:
        if not value:
            raise ValueError("Task text cannot be empty.")
        return EntryType.TASK, value, task_state

    for marker, entry_type in TYPE_MARKERS.items():
        if value.startswith(marker):
            text = value[len(marker) :].strip()
            if not text:
                raise ValueError("Entry text cannot be empty.")
            return entry_type, text, None

        text = _strip_trailing_marker(value, marker)
        if text is not None:
            if not text:
                raise ValueError("Entry text cannot be empty.")
            return entry_type, text, None

    if value == ">":
        raise ValueError("Supporting detail text cannot be empty.")
    return EntryType.NOTE, value, None


def normalize_detail(raw: str) -> str | None:
    value = raw.strip()
    if not value:
        return None
    if value == ">":
        raise ValueError("Supporting detail text cannot be empty.")
    if value.startswith(">"):
        text = value[1:].strip()
        if not text:
            raise ValueError("Supporting detail text cannot be empty.")
        return text

    text = _strip_trailing_marker(value, ">")
    if text is not None:
        if not text:
            raise ValueError("Supporting detail text cannot be empty.")
        return text
    return None
