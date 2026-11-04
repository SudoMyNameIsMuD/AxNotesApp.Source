# AxNotes v0.1.7

AxNotes is a local-first, Markdown-authoritative bullet notebook. This build restores the working interactive CLI while retaining the new `notes/` storage layout and clean Markdown introduced during P0.

## Windows PowerShell

From the AxNotes source folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
AxNotes --version
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Create a notebook separately from the source folder:

```powershell
cd ..
mkdir AxNotes-Notebook-v016
cd AxNotes-Notebook-v016
AxNotes init
AxNotes
```

## macOS with zsh

```zsh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[dev]'
python3 -m pytest
AxNotes --version
cd ..
mkdir -p AxNotes-Notebook-v016
cd AxNotes-Notebook-v016
AxNotes init
AxNotes
```

## Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[dev]'
python3 -m pytest
AxNotes --version
cd ..
mkdir -p AxNotes-Notebook-v016
cd AxNotes-Notebook-v016
AxNotes init
AxNotes
```

`AxNotes init` is required once per new notebook. On later sessions, activate the source `.venv`, change into the initialized notebook, and run `AxNotes`.

## Notebook structure

```text
AxNotes-Notebook-v016/
├── notes/
├── .AxNotes/
│   └── metadata/
└── AxNotes.toml
```

The index `.AxNotes/index.sqlite3` is created only when search/indexing requires it. New Markdown contains no UUID HTML comments.

## Writing

Inside AxNotes:

- normal text creates a note
- `[` creates a task
- trailing `[x` or `[x]` marks a task complete
- `!` marks important
- `?` marks a question
- `>` creates a supporting detail
- `/` displays commands

## Commands

Everyday:

- `/today`
- `/week`
- `/search`
- `/help`
- `/quit`

Maintenance:

- `/reindex`
- `/sync`

Planned: `/lastweek` and `/month`.

## P0 architecture status

Implemented in this build:

- `notes/` replaces `daily/` for new notebooks.
- New Markdown is clean and contains no UUID comments.
- `.AxNotes/metadata/` is reserved for durable identity sidecars.
- SQLite continues to be derived and disposable.
- The full interactive CLI is restored on top of the new layout.

Not implemented yet:

- metadata JSON schema persistence
- fingerprinting
- reconciliation engine
- atomic metadata sidecar writes

Those remain the next P0 steps.
