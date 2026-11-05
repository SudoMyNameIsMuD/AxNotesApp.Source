import sqlite3
from contextlib import closing
from datetime import datetime
from uuid import uuid4

from .metadata import MetadataNotFoundError, load_metadata
from .parser import parse_file
from .single_file import parse_notebook

SCHEMA = """
CREATE TABLE IF NOT EXISTS files(
 path TEXT PRIMARY KEY,
 modified_ns INTEGER NOT NULL,
 size INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS entries(
 id TEXT,
 type TEXT NOT NULL,
 text TEXT NOT NULL,
 task_state TEXT,
 source_file TEXT NOT NULL,
 line_number INTEGER NOT NULL,
 source_date TEXT,
 ordinal INTEGER
);
CREATE INDEX IF NOT EXISTS ix_entries_text ON entries(text);
"""


def connect(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db


def files(notebook):
    if notebook.uses_single_file:
        return [notebook.single_file_path]
    return sorted(notebook.notes_dir.glob("*.md"))


def metadata_for_file(notebook, path):
    relative = str(path.relative_to(notebook.root)).replace("\\", "/")
    sidecar = (
        notebook.single_file_metadata_path
        if relative == "notebook.md"
        else notebook.metadata_dir / relative.replace(".md", ".json")
    )
    if not sidecar.exists():
        return {}
    try:
        metadata = load_metadata(sidecar)
    except MetadataNotFoundError:
        return {}
    return {entry.ordinal: str(entry.id) for entry in metadata.entries if entry.source == relative}


def replace(db, notebook, path):
    relative = str(path.relative_to(notebook.root)).replace("\\", "/")
    stat = path.stat()
    db.execute("DELETE FROM entries WHERE source_file=?", (relative,))
    db.execute("INSERT OR REPLACE INTO files VALUES(?,?,?)", (relative, stat.st_mtime_ns, stat.st_size))
    metadata_map = metadata_for_file(notebook, path)
    count = 0
    if relative == "notebook.md":
        records = parse_notebook(path.read_text(encoding="utf-8"), notebook.config.heading_format)
        values = ((record.line_number, record.ordinal, record.day, record.entry) for record in records)
    else:
        entries = parse_file(path)
        try:
            source_date = datetime.strptime(path.stem, notebook.config.date_format).date()
        except ValueError:
            source_date = None
        values = ((ordinal, ordinal, source_date, entry) for ordinal, entry in enumerate(entries, start=1))
    for line_number, ordinal, source_date, entry in values:
        entry_id = metadata_map.get(ordinal)
        db.execute(
            "INSERT INTO entries(id,type,text,task_state,source_file,line_number,source_date,ordinal) VALUES(?,?,?,?,?,?,?,?)",
            (
                entry_id,
                entry.entry_type.value,
                entry.text,
                entry.task_state.value if entry.task_state else None,
                relative,
                line_number,
                source_date.isoformat() if source_date else None,
                ordinal,
            ),
        )
        count += 1
    return count


def rebuild(notebook):
    notebook.validate()
    temporary_path = notebook.index_path.with_name(f".{notebook.index_path.name}.{uuid4().hex}.tmp")
    count = 0
    try:
        with closing(connect(temporary_path)) as db, db:
            for path in files(notebook):
                count += replace(db, notebook, path)
        temporary_path.replace(notebook.index_path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    return count


def sync(notebook):
    notebook.validate()
    if not notebook.index_path.exists():
        return rebuild(notebook)
    current = {str(path.relative_to(notebook.root)): path for path in files(notebook)}
    with closing(connect(notebook.index_path)) as db:
        known = {row["path"]: (row["modified_ns"], row["size"])
                 for row in db.execute("SELECT * FROM files")}
        with db:
            for relative in set(known) - set(current):
                db.execute("DELETE FROM entries WHERE source_file=?", (relative,))
                db.execute("DELETE FROM files WHERE path=?", (relative,))
            for relative, path in current.items():
                stat = path.stat()
                if known.get(relative) != (stat.st_mtime_ns, stat.st_size):
                    replace(db, notebook, path)


def search(notebook, query, limit=50):
    sync(notebook)
    value = query.strip()
    lowered = value.casefold()
    with closing(connect(notebook.index_path)) as db:
        if value == "*":
            return list(db.execute("SELECT * FROM entries ORDER BY source_file DESC,line_number DESC LIMIT ?", (limit,)))
        if lowered in {"[ ]", "[]", "open", "open task", "open tasks", "task", "tasks"}:
            return list(db.execute("SELECT * FROM entries WHERE type='task' AND task_state='open' ORDER BY source_file DESC,line_number DESC LIMIT ?", (limit,)))
        if lowered in {"[x]", "complete", "completed", "done", "completed task", "completed tasks"}:
            return list(db.execute("SELECT * FROM entries WHERE type='task' AND task_state='done' ORDER BY source_file DESC,line_number DESC LIMIT ?", (limit,)))
        if value == "!" or lowered.startswith("important"):
            return list(db.execute("SELECT * FROM entries WHERE type='important' ORDER BY source_file DESC,line_number DESC LIMIT ?", (limit,)))
        if value == "?" or lowered in {"question", "questions"}:
            return list(db.execute("SELECT * FROM entries WHERE type='question' ORDER BY source_file DESC,line_number DESC LIMIT ?", (limit,)))
        pattern = f"%{value}%"
        return list(db.execute("SELECT * FROM entries WHERE text LIKE ? OR source_file LIKE ? ORDER BY source_file DESC,line_number DESC LIMIT ?", (pattern, pattern, limit)))
