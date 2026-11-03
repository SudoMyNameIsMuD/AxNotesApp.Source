import re
from pathlib import Path
from .models import Entry, EntryType, TaskState

TASK_RE = re.compile(r"^\[(?P<state>[ /xX>\-])\]\s+(?P<text>.*)$")
TYPE_RE = re.compile(r"^(?P<marker>[!?@])\s+(?P<text>.*)$")
NOTE_RE = re.compile(r"^-\s+(?P<text>.*)$")
DETAIL_RE = re.compile(r"^\s{2,}›\s+(?P<text>.*)$")
STATE = {" ": TaskState.OPEN, "/": TaskState.IN_PROGRESS, "x": TaskState.DONE,
         "X": TaskState.DONE, ">": TaskState.MIGRATED, "-": TaskState.CANCELED}
TYPES = {"!": EntryType.IMPORTANT, "?": EntryType.QUESTION, "@": EntryType.EVENT}


def parse_markdown(text: str) -> list[Entry]:
    entries: list[Entry] = []
    fence = None
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            fence = None if fence == marker else marker
            continue
        if fence:
            continue
        detail = DETAIL_RE.match(line)
        if detail and entries:
            entries[-1].details.append(detail.group("text").rstrip())
            continue
        task = TASK_RE.match(line)
        if task:
            entries.append(Entry(EntryType.TASK, task.group("text").rstrip(), STATE[task.group("state")]))
            continue
        typed = TYPE_RE.match(line)
        if typed:
            entries.append(Entry(TYPES[typed.group("marker")], typed.group("text").rstrip()))
            continue
        note = NOTE_RE.match(line)
        if note and note.group("text").strip() not in {"", "-"}:
            entries.append(Entry(EntryType.NOTE, note.group("text").rstrip()))
    return entries


def parse_file(path: Path) -> list[Entry]:
    return parse_markdown(path.read_text(encoding="utf-8"))
