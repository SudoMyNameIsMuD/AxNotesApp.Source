# AxNotes Roadmap

> **Core UX principle:** AxNotes should become easier to use as its implementation becomes more capable. New functionality should not require ordinary users to understand Markdown metadata, SQLite, UUIDs, Python, or internal file-management behavior.

## v0.1 Refinement Backlog

### Capture and editing
- Edit an existing entry safely.
- Delete an existing entry safely.
- Change an existing task state after capture.
- Move or migrate an entry to another day.
- Add a supporting detail to an existing entry, not only the immediately preceding entry.
- Define behavior for orphaned `>` details when no parent entry exists.
- Add undo for the most recent capture.
- Evaluate multiline entries without compromising simple bullet capture.
- Keep bare `-` and otherwise empty input from becoming entries.

### Tasks
- Support simple interaction for all five task states:
  - `[ ]` Open
  - `[/]` In progress
  - `[x]` Complete
  - `[>]` Migrated
  - `[-]` Canceled
- Filter tasks by state.
- Evaluate an option to hide completed or canceled tasks in normal views without deleting them.

### Search
- Continue improving search semantics and result formatting.
- Search supporting-detail text as well as parent entries.
- Search tags and entities.
- Add phrase search.
- Maintain consistent case-insensitive search behavior.
- Add date-range search.
- Support combined filters, for example `/search task open report`.
- Keep shortcuts such as `*`, `[ ]`, `[x]`, `!`, and `?` predictable.
- Define a practical result limit for `/search *` and other broad searches.
- Improve empty/no-result messages.
- Optionally show supporting details under matching parent entries.
- Keep internal UUID metadata hidden in all search output.

### Time-based views and commands
- Keep `/today` and `/week` consistent with normal AxNotes entry formatting.
- `/lastweek`: show the previous Monday through Sunday.
- `/month`: show the current calendar month.
- Define whether `/month` is a complete entry listing, compact summary, or supports both modes.
- Later allow an explicit month, for example `/month October`.
- Evaluate `/yesterday`.
- Evaluate an explicit date command such as `/date 02Nov26`.
- Ensure supporting details remain attached to parent entries in every time-based view.

### Navigation
- Open today's Markdown file in the configured editor.
- Open a search result in its source Markdown file.
- Jump directly to another daily note.
- Clearly distinguish viewing historical notes from modifying historical notes.

### Notebook safety and recovery
- Expose backup through the simple AxNotes interface.
- Add a safe restore workflow.
- Use atomic writes for operations that rewrite existing Markdown.
- Define interrupted-write recovery.
- Detect duplicate UUIDs.
- Define a missing-UUID repair strategy.
- Handle malformed Markdown non-destructively and provide useful diagnostics.
- Improve index-rebuild diagnostics.
- Define behavior when externally edited files change while AxNotes is running.
- Verify deletion and rebuilding of SQLite never loses authoritative content or identity.

### Configuration
- Preferred external editor.
- Date-display formats.
- Notebook location/default notebook behavior.
- Optional heading behavior.
- Search and display preferences.
- Keep configuration optional by providing sensible defaults.

### Cross-platform validation
- Continue Windows, macOS, and Linux validation.
- Test paths containing spaces and synchronized-folder paths such as OneDrive locations.
- Verify terminal behavior in Windows PowerShell, macOS zsh, and common Linux shells.

## Later UX Improvements

### Rich terminal editing
- Replace plain Python `input()` with a richer terminal editing layer.
- Transform `[`, `!`, `?`, and `>` markers in place while typing instead of echoing raw input followed by normalized output.
- Preserve the writing-first interface.
- Keep everyday commands visually separate from maintenance commands such as `/reindex` and `/sync`.
- Add command completion and suggestions after typing `/`.
- Add arrow-key input history.
- Support left/right arrow editing, Home, End, and other expected line-editing behavior.
- Handle terminal width and long-line wrapping cleanly.
- Gracefully handle Ctrl+C and EOF/Ctrl+Z/Ctrl+D behavior.
- Evaluate color only where it communicates structure or task state.
- Provide a no-color/accessibility-friendly mode.

## Data Portability
- Markdown import.
- Plain Markdown export.
- Whole-notebook export.
- Validate that SQLite can always be deleted and rebuilt from Markdown.
- Define a migration strategy before any future authoritative Markdown-format change.
- Preserve compatibility with notebooks created by earlier v0.1 builds wherever practical.

## Distribution and Installation
- Keep `.venv` as the supported source/development installation approach during v0.1.
- Eventually provide a standalone Windows executable.
- Eventually provide a standalone macOS executable/application distribution.
- Eventually provide a Linux executable/package.
- Remove the requirement for ordinary users to understand Python or virtual environments once packaged releases are available.
- Automate release testing across Windows, macOS, and Linux.

## Quality and Testing
- Add a regression test whenever hands-on testing finds a bug.
- Keep parser tests separate from interface tests where practical.
- Test compatibility with previous v0.1 notebook formats and metadata markers.
- Test notebooks modified externally between AxNotes operations.
- Test large notebooks with thousands of entries.
- Test Unicode and unusual punctuation.
- Test file paths containing spaces.
- Maintain a known-issues list during v0.1 development.
- Keep public fixtures and examples synthetic and free of private/project data.

## Architectural Guardrails
- Markdown remains authoritative storage.
- SQLite remains derived, disposable, and rebuildable.
- AxNotes remains local-first and offline-capable.
- External Markdown editing remains supported.
- Unknown Markdown should be preserved wherever practical.
- Internal UUID metadata stays hidden from normal AxNotes output.
- Formatting communicates structure or state rather than decoration.
- Preserve Windows, macOS, and Linux compatibility.
- Prefer backward compatibility with earlier v0.1 notebooks.
- Keep domain behavior independent from the terminal interface so a future TUI or other UI can reuse the same core.

## P0 Decisions Locked
- `notes/` replaces `daily/` for new notebooks.
- Durable identities are required and will live under `.AxNotes/metadata/`, not in visible Markdown.
- SQLite remains derived/disposable.
- New Markdown must remain free of UUID comments.
