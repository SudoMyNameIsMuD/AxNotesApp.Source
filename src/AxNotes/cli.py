import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

from . import __version__
from .index import rebuild, search, sync
from .interaction import COMMANDS, normalize_detail, normalize_entry
from .models import Entry, EntryType, TaskState
from .notebook import Notebook
from .renderer import render_entry

MENU = """Commands
/today     Show today's entries
/week      Show this week's entries
/search    Search notebook entries
/help      Show commands
/quit      Close AxNotes

Maintenance
/reindex   Rebuild the derived index
/sync      Refresh the derived index from authoritative Markdown and metadata sidecars"""


def find_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / "AxNotes.toml").exists():
            return candidate
    return current


def query_context(notebook, query):
    value = query.strip()
    lowered = value.casefold()
    today = date.today()
    names = {name.lower(): index for index, name in enumerate(
        ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
    )}
    if lowered in names:
        target = today - timedelta(days=(today.weekday() - names[lowered]) % 7)
        return target.strftime(notebook.config.date_format)
    for fmt in ("%d%b%y", "%d%b%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date().strftime(notebook.config.date_format)
        except ValueError:
            continue
    return value


def print_search(notebook, query, output_fn=print):
    rows = search(notebook, query_context(notebook, query))
    if not rows:
        output_fn("No matching AxNotes entries.")
        return
    current = None
    for row in rows:
        if row["source_file"] != current:
            current = row["source_file"]
            stem = Path(current).stem
            try:
                output_fn("\n" + notebook.heading(datetime.strptime(stem, notebook.config.date_format).date()))
            except ValueError:
                output_fn("\n# " + current)
        entry = Entry(
            EntryType(row["type"]),
            row["text"],
            TaskState(row["task_state"]) if row["task_state"] else None,
        )
        output_fn(render_entry(entry))


def capture_inline_entry(notebook, raw, day=None):
    value = raw.strip()
    supporting_detail = normalize_detail(value)
    if supporting_detail is not None:
        notebook.append_detail(supporting_detail, day=day)
        return f"     › {supporting_detail}"

    entry_type, text, state = normalize_entry(value)
    normalized = Entry(entry_type, text, state)
    notebook.append(text, entry_type, day=day, task_state=state or TaskState.OPEN)
    notebook.sync_metadata()
    return render_entry(normalized)


def handle_command(notebook, raw, output_fn=print, input_fn=input):
    command, _, argument = raw.partition(" ")
    if command == "/today":
        output_fn("\n" + notebook.render_day(date.today(), render_entry) + "\n")
    elif command == "/week":
        output_fn("\n" + notebook.render_week(date.today(), render_entry) + "\n")
    elif command == "/search":
        query = argument.strip() or input_fn("Search: ").strip()
        if query:
            print_search(notebook, query, output_fn=output_fn)
    elif command == "/reindex":
        output_fn(f"Derived index rebuilt: {rebuild(notebook)} entries")
    elif command == "/sync":
        sync(notebook)
        output_fn("Derived index synchronized.")
    elif command in {"/help", "/"}:
        output_fn("\n" + MENU + "\n")
    elif command in {"/quit", "/exit"}:
        return False
    else:
        output_fn("Commands: " + "  ".join("/" + command for command in COMMANDS))
    return True


def interactive(notebook, input_fn=input, output_fn=print):
    try:
        notebook.validate()
    except FileNotFoundError:
        output_fn("AxNotes\n\nThis folder is not an AxNotes notebook.\n\nRun:\n  AxNotes init\n\nThen start AxNotes again.")
        return 2
    output_fn(f"AxNotes\n\n{notebook.heading(date.today())}\n")
    while True:
        try:
            raw = input_fn("- ")
        except (EOFError, KeyboardInterrupt):
            output_fn("\nAxNotes closed.")
            return 0
        if not raw.strip():
            continue
        if raw.startswith("/"):
            if not handle_command(notebook, raw.strip(), output_fn=output_fn, input_fn=input_fn):
                output_fn("AxNotes closed.")
                return 0
            continue
        try:
            capture_inline_entry(notebook, raw)
        except ValueError as exc:
            output_fn(str(exc))


def parser():
    command_parser = argparse.ArgumentParser(prog="AxNotes")
    command_parser.add_argument("--version", action="version", version=f"AxNotes {__version__}")
    sub = command_parser.add_subparsers(dest="command")
    init = sub.add_parser("init")
    init.add_argument("path", nargs="?", default=".")
    sub.add_parser("today")
    sub.add_parser("week")
    query = sub.add_parser("search")
    query.add_argument("query")
    sub.add_parser("reindex")
    sub.add_parser("sync")
    return command_parser


def main(argv=None):
    args = parser().parse_args(argv)
    if args.command == "init":
        notebook = Notebook(Path(args.path).resolve())
        notebook.initialize()
        print(f"AxNotes notebook initialized: {notebook.root}")
        return 0
    notebook = Notebook(find_root(Path.cwd()))
    if args.command is None:
        return interactive(notebook)
    try:
        notebook.validate()
    except FileNotFoundError:
        print("This folder is not an AxNotes notebook. Run 'AxNotes init' first.")
        return 2
    if args.command == "today":
        print(notebook.render_day(date.today(), render_entry))
    elif args.command == "week":
        print(notebook.render_week(date.today(), render_entry))
    elif args.command == "search":
        print_search(notebook, args.query)
    elif args.command == "reindex":
        print(f"Derived index rebuilt: {rebuild(notebook)} entries")
    elif args.command == "sync":
        sync(notebook)
        print("Derived index synchronized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
