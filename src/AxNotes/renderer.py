from .models import TASK_MARKERS, Entry, EntryType, TaskState

DISPLAY_MARKERS = {
    EntryType.NOTE: " - ",
    EntryType.IMPORTANT: " ! ",
    EntryType.QUESTION: " ? ",
    EntryType.DECISION: " ! ",
    EntryType.EVENT: " @ ",
}


def marker_for(entry: Entry) -> str:
    if entry.entry_type is EntryType.TASK:
        return TASK_MARKERS[entry.task_state or TaskState.OPEN]
    return DISPLAY_MARKERS[entry.entry_type]


def render_entry(entry: Entry) -> str:
    return f"{marker_for(entry)} {entry.text}"
