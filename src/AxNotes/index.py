import sqlite3
from contextlib import closing

from .parser import parse_file

SCHEMA = """
CREATE TABLE IF NOT EXISTS files(
 path TEXT PRIMARY KEY,
 modified_ns INTEGER NOT NULL,
 size INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS entries(
 id INTEGER PRIMARY KEY,
 type TEXT NOT NULL,
 text TEXT NOT NULL,
 task_state TEXT,
 source_file TEXT NOT NULL,
 line_number INTEGER NOT NULL
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
    return sorted(notebook.notes_dir.glob("*.md"))


def replace(db, notebook, path):
    relative = str(path.relative_to(notebook.root))
    stat = path.stat()
    db.execute("DELETE FROM entries WHERE source_file=?", (relative,))
    db.execute("INSERT OR REPLACE INTO files VALUES(?,?,?)", (relative, stat.st_mtime_ns, stat.st_size))
    count = 0
    for line_number, entry in enumerate(parse_file(path), 1):
        db.execute(
            "INSERT INTO entries(type,text,task_state,source_file,line_number) VALUES(?,?,?,?,?)",
            (entry.entry_type.value, entry.text,
             entry.task_state.value if entry.task_state else None,
             relative, line_number),
        )
        count += 1
    return count


def rebuild(notebook):
    notebook.validate()
    if notebook.index_path.exists():
        notebook.index_path.unlink()
    count = 0
    with closing(connect(notebook.index_path)) as db, db:
        for path in files(notebook):
            count += replace(db, notebook, path)
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
