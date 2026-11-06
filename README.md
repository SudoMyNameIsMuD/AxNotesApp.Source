# AxNotes v0.1.8

AxNotes is a local-first bullet notebook. Authoritative Markdown stores entries, while metadata sidecars preserve durable identity and the derived index supports search.

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

The derived index `.AxNotes/index.sqlite3` is created only when search or indexing requires it. Authoritative Markdown contains no UUID HTML comments.

## Writing

Inside AxNotes, quick-entry notation currently includes:

- Plain text creates a normal note.
- Leading `[` or `[ ]` creates an open task.
- Leading or trailing `[/` or `[/]` creates an in-progress task.
- Leading or trailing `[x` or `[x]` creates a completed task.
- Leading or trailing `[>` or `[>]` creates a migrated task.
- Leading or trailing `[-` or `[-]` creates a canceled task.
- Leading or whitespace-separated trailing `!` creates an important entry.
- Leading or whitespace-separated trailing `?` creates a question. A natural sentence-ending question mark without preceding whitespace is preserved as entry text.
- Leading or whitespace-separated trailing `@` marks an event entry. Event-section formatting is a later roadmap step.
- Leading or whitespace-separated trailing `>` creates a supporting detail.
- `/` displays commands

AxNotes converts accepted quick-entry notation into the corresponding entry type, task state, and canonical Markdown marker. AxNotes places the canonical Markdown marker at the beginning of the stored entry. Trailing quick-entry notation is removed from the entry text during normalization. The CLI adds presentation spacing to form the rendered marker; alignment is not stored in Markdown.

After a successful capture, AxNotes redraws the most recently requested `/today` or `/week` view before returning to the writing prompt. Until either view is requested, it redraws `/today`. This shows the saved entry in context without printing a separate duplicate line. Other commands do not change the remembered view.

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

Available:

- `/markdown`
- `/md`

Planned, not yet available: `/lastweek`, `/month`, and `/clearwelcome`.

Command results appear as inline command output before AxNotes returns to the writing prompt.

## P0 architecture status

P0 Steps 1 through 8 are complete:

- `notes/` contains authoritative Markdown.
- Metadata sidecars under `.AxNotes/metadata/` store durable entry identities.
- The derived index is disposable and rebuildable from Markdown and metadata sidecars.
- Markdown remains clean and contains no visible UUID comments.

## Single-file notebook migration

Existing v0.1 notebooks continue using dated files under `notes/` until explicitly migrated. From the notebook folder, run:

```text
AxNotes migrate single-file
```

Migration creates `notebook.md` and `.AxNotes/metadata/notebook.json`, rebuilds the derived index, and preserves the original notes at `notes.pre-single-file-backup/`. It also keeps a copy of the metadata sidecars and configuration under `.AxNotes/backups/`. Migration refuses to overwrite an existing backup or single-file notebook.
