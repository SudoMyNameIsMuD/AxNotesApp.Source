import textwrap

from .models import TASK_MARKERS, Entry, EntryType, TaskState

DISPLAY_MARKERS = {
    EntryType.NOTE: " - ",
    EntryType.IMPORTANT: " ! ",
    EntryType.QUESTION: " ? ",
    EntryType.DECISION: " ! ",
    EntryType.EVENT: " @ ",
}

DISPLAY_WIDTH = 80


def marker_for(entry: Entry) -> str:
    if entry.entry_type is EntryType.TASK:
        return TASK_MARKERS[entry.task_state or TaskState.OPEN]
    return DISPLAY_MARKERS[entry.entry_type]


def _render_wrapped(prefix: str, text: str, width: int = DISPLAY_WIDTH) -> str:
    if not text:
        return prefix.rstrip()
    available = max(10, width - len(prefix))
    wrapped = textwrap.wrap(
        text,
        width=available,
        break_long_words=False,
        break_on_hyphens=False,
        drop_whitespace=False,
    )
    if not wrapped:
        return prefix.rstrip()
    lines = [f"{prefix}{wrapped[0]}"]
    for chunk in wrapped[1:]:
        lines.append(f"{' ' * len(prefix)}{chunk}")
    return "\n".join(lines)


def render_entry(entry: Entry) -> str:
    prefix = f"{marker_for(entry)} "
    return _render_wrapped(prefix, entry.text)


def render_detail(detail: str) -> str:
    prefix = "     › "
    return _render_wrapped(prefix, detail)
