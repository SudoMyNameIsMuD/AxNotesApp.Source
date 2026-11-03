from dataclasses import dataclass, field
from enum import StrEnum


class EntryType(StrEnum):
    NOTE = "note"
    TASK = "task"
    IMPORTANT = "important"
    QUESTION = "question"
    DECISION = "decision"
    EVENT = "event"


class TaskState(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    MIGRATED = "migrated"
    CANCELED = "canceled"


TASK_MARKERS = {
    TaskState.OPEN: "[ ]",
    TaskState.IN_PROGRESS: "[/]",
    TaskState.DONE: "[x]",
    TaskState.MIGRATED: "[>]",
    TaskState.CANCELED: "[-]",
}


@dataclass(slots=True)
class Entry:
    entry_type: EntryType
    text: str
    task_state: TaskState | None = None
    details: list[str] = field(default_factory=list)
