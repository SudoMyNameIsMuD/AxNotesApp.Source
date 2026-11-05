import os
import re
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from .models import TASK_MARKERS, Entry, EntryType
from .parser import parse_markdown

DAY_HEADING = re.compile(r"^####\s+(.+?)\s*$")
DIVIDER = re.compile(r"^\s*(?:---+|___+|\*\*\*+)\s*$")
ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
DETAIL = re.compile(r"^\s{2,}›\s+(?P<text>.*)$")
SECTION_HEADING = re.compile(r"^(?P<level>#{1,6})\s+")


@dataclass(frozen=True, slots=True)
class NotebookRecord:
    entry: Entry
    day: date | None
    line_number: int
    ordinal: int


def _heading_date(title: str, heading_format: str) -> date | None:
    for candidate_format in (heading_format, "%A | %d%b%y", "%Y-%m-%d", "%d%b%y"):
        try:
            return datetime.strptime(title, candidate_format).date()
        except ValueError:
            continue

    match = ISO_DATE.search(title)
    if match:
        return date.fromisoformat(match.group())
    return None


def parse_notebook(text: str, heading_format: str = "%A | %d%b%y") -> list[NotebookRecord]:
    records: list[NotebookRecord] = []
    current_day = None
    previous_record = None
    fence = None

    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            fence = None if fence == marker else marker
            previous_record = None
            continue
        if fence:
            continue

        heading = DAY_HEADING.match(line)
        if heading:
            current_day = _heading_date(heading.group(1), heading_format)
            previous_record = None
            continue
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if level <= 3:
                current_day = None
            previous_record = None
            continue
        if DIVIDER.fullmatch(line):
            previous_record = None
            continue

        detail = DETAIL.match(line)
        if detail:
            if previous_record is not None:
                previous_record.entry.details.append(detail.group("text").rstrip())
            continue

        parsed = parse_markdown(line)
        if not parsed:
            continue
        entry = parsed[0]
        record = NotebookRecord(entry, current_day, line_number, len(records) + 1)
        records.append(record)
        previous_record = record

    return records


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def append_to_notebook(
    path: Path, day: date, line: str, heading_format: str = "%A | %d%b%y"
) -> None:
    content = path.read_text(encoding="utf-8") if path.exists() else "# AxNotes Notebook\n"
    lines = content.splitlines()
    day_title = day.strftime(heading_format).upper()
    day_line = f"#### {day_title}"
    day_start = next(
        (
            index
            for index, value in enumerate(lines)
            if (match := DAY_HEADING.match(value))
            and _heading_date(match.group(1), heading_format) == day
        ),
        None,
    )

    if day_start is None:
        insertion = len(lines)
        year_line = f"## {day.year}"
        year_start = next(
            (index for index, value in enumerate(lines) if value.strip() == year_line),
            None,
        )
        if year_start is None:
            later_year = next(
                (
                    index
                    for index, value in enumerate(lines)
                    if (match := re.match(r"^##\s+(\d{4})\s*$", value))
                    and int(match.group(1)) > day.year
                ),
                None,
            )
            insertion = later_year if later_year is not None else len(lines)
            block = [
                year_line,
                "",
                f"### {day.strftime('%B')}",
                "",
                day_line,
                "",
                "##### General Notes",
                line,
            ]
        else:
            year_end = next(
                (
                    index
                    for index in range(year_start + 1, len(lines))
                    if re.match(r"^##\s+", lines[index])
                ),
                len(lines),
            )
            month_title = f"### {day.strftime('%B')}"
            month_start = next(
                (
                    index
                    for index in range(year_start + 1, year_end)
                    if lines[index].strip() == month_title
                ),
                None,
            )
            if month_start is None:
                later_month = next(
                    (
                        index
                        for index in range(year_start + 1, year_end)
                        if (match := re.match(r"^###\s+(.+?)\s*$", lines[index]))
                        and _month_number(match.group(1)) > day.month
                    ),
                    None,
                )
                insertion = later_month if later_month is not None else year_end
                block = [month_title, "", day_line, "", "##### General Notes", line]
            else:
                month_end = next(
                    (
                        index
                        for index in range(month_start + 1, year_end)
                        if re.match(r"^###\s+", lines[index])
                    ),
                    year_end,
                )
                later_day = next(
                    (
                        index
                        for index in range(month_start + 1, month_end)
                        if (match := DAY_HEADING.match(lines[index]))
                        and (existing_day := _heading_date(match.group(1), heading_format))
                        and existing_day > day
                    ),
                    None,
                )
                insertion = later_day if later_day is not None else month_end
                block = [day_line, "", "##### General Notes", line]

        prefix = [""] if insertion > 0 and lines[insertion - 1].strip() else []
        suffix = [""] if insertion < len(lines) and lines[insertion].strip() else []
        lines[insertion:insertion] = prefix + block + suffix
    else:
        day_end = len(lines)
        for index in range(day_start + 1, len(lines)):
            heading = SECTION_HEADING.match(lines[index])
            if heading and len(heading.group("level")) <= 4:
                day_end = index
                break

        section_start = None
        for index in range(day_start + 1, day_end):
            if lines[index].strip() == "##### General Notes":
                section_start = index
        if section_start is None:
            insertion = day_end
            while insertion > day_start and not lines[insertion - 1].strip():
                insertion -= 1
            suffix = [""] if day_end < len(lines) else []
            lines[insertion:insertion] = ["", "##### General Notes", line] + suffix
        else:
            section_end = day_end
            for index in range(section_start + 1, day_end):
                heading = SECTION_HEADING.match(lines[index])
                if (heading and len(heading.group("level")) <= 5) or DIVIDER.fullmatch(
                    lines[index]
                ):
                    section_end = index
                    break
            insertion = section_end
            while insertion > section_start + 1 and not lines[insertion - 1].strip():
                insertion -= 1
            lines[insertion:insertion] = [line]

    atomic_write_text(path, "\n".join(lines).rstrip() + "\n")


def _month_number(value: str) -> int:
    try:
        return datetime.strptime(value, "%B").month
    except ValueError:
        return 0


def render_notebook(
    records: list[NotebookRecord],
    days: list[date] | None = None,
    heading_format: str = "%A | %d%b%y",
) -> str:
    lines = ["# AxNotes Notebook", ""]
    current_year = None
    current_month = None
    records_by_day: dict[date, list[NotebookRecord]] = {}
    for record in records:
        if record.day is None:
            raise ValueError(
                f"Entry on line {record.line_number} is not under a valid day heading."
            )
        records_by_day.setdefault(record.day, []).append(record)
    ordered_days = sorted(set(days or ()) | set(records_by_day))

    for day in ordered_days:
        if day.year != current_year:
            current_year = day.year
            current_month = None
            lines.extend([f"## {current_year}", ""])
        if (day.year, day.month) != current_month:
            current_month = (day.year, day.month)
            lines.extend([f"### {day.strftime('%B')}", ""])
        lines.extend([f"#### {day.strftime(heading_format).upper()}", "", "##### General Notes"])

        for record in records_by_day.get(day, []):
            entry = record.entry
            if entry.entry_type is EntryType.TASK:
                marker = TASK_MARKERS[entry.task_state]
            else:
                marker = {
                    EntryType.NOTE: "-",
                    EntryType.IMPORTANT: "!",
                    EntryType.QUESTION: "?",
                    EntryType.DECISION: "!",
                    EntryType.EVENT: "@",
                }[entry.entry_type]
            lines.append(f"{marker} {entry.text}")
            lines.extend(f"  › {detail}" for detail in entry.details)

    return "\n".join(lines).rstrip() + "\n"
