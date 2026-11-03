from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from .config import Config, DEFAULT_CONFIG
from .models import Entry, EntryType, TaskState, TASK_MARKERS
from .parser import parse_file

STORAGE_PREFIXES = {
    EntryType.NOTE: "-",
    EntryType.IMPORTANT: "!",
    EntryType.QUESTION: "?",
    EntryType.DECISION: "!",
    EntryType.EVENT: "@",
}


@dataclass(slots=True)
class Notebook:
    root: Path

    @property
    def config(self):
        return Config.load(self.root)

    @property
    def notes_dir(self):
        return self.root / self.config.notes_directory

    @property
    def state_dir(self):
        return self.root / ".AxNotes"

    @property
    def metadata_dir(self):
        return self.root / self.config.metadata_directory

    @property
    def index_path(self):
        return self.state_dir / "index.sqlite3"

    def initialize(self):
        self.root.mkdir(parents=True, exist_ok=True)
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        config = self.root / "AxNotes.toml"
        if not config.exists():
            config.write_text(DEFAULT_CONFIG, encoding="utf-8", newline="\n")

    def validate(self):
        if not (self.root / "AxNotes.toml").exists():
            raise FileNotFoundError("AxNotes notebook not found. Run 'AxNotes init' first.")

    def note_path(self, day: date):
        return self.notes_dir / f"{day.strftime(self.config.date_format)}.md"

    def heading(self, day: date):
        return f"# {day.strftime(self.config.heading_format).upper()}"

    def ensure_note(self, day: date):
        path = self.note_path(day)
        if not path.exists():
            path.write_text(
                f"---\ntype: daily\ndate: {day.isoformat()}\n---\n\n{self.heading(day)}\n\n",
                encoding="utf-8",
                newline="\n",
            )
        return path

    def append(self, text: str, entry_type=EntryType.NOTE, day=None, task_state=TaskState.OPEN):
        clean = " ".join(text.strip().splitlines()).strip()
        if not clean or (entry_type is EntryType.NOTE and clean == "-"):
            raise ValueError("Entry text cannot be empty.")
        day = day or date.today()
        prefix = TASK_MARKERS[task_state] if entry_type is EntryType.TASK else STORAGE_PREFIXES[entry_type]
        path = self.ensure_note(day)
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(f"{prefix} {clean}\n")
        return path

    def append_detail(self, text: str, day=None):
        clean = " ".join(text.strip().splitlines()).strip()
        if not clean:
            raise ValueError("Detail text cannot be empty.")
        path = self.ensure_note(day or date.today())
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(f"  › {clean}\n")
        return path

    def entries_for_day(self, day: date) -> list[Entry]:
        path = self.note_path(day)
        return parse_file(path) if path.exists() else []

    def render_day(self, day: date, render_entry) -> str:
        lines = [self.heading(day), ""]
        for entry in self.entries_for_day(day):
            lines.append(render_entry(entry))
            lines.extend(f"     › {detail}" for detail in entry.details)
        return "\n".join(lines).rstrip()

    def render_week(self, day: date, render_entry) -> str:
        start = day - timedelta(days=day.weekday())
        end = start + timedelta(days=6)
        lines = [f"# WEEK | {start.strftime('%d%b%y').upper()}–{end.strftime('%d%b%y').upper()}"]
        for offset in range(7):
            current = start + timedelta(days=offset)
            entries = self.entries_for_day(current)
            if not entries:
                continue
            lines.extend(["", f"## {current.strftime('%A | %d%b%y').upper()}"])
            for entry in entries:
                lines.append(render_entry(entry))
                lines.extend(f"     › {detail}" for detail in entry.details)
        if len(lines) == 1:
            lines.extend(["", "No entries this week."])
        return "\n".join(lines)
