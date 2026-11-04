## AxNotes Roadmap

**Updated:** 04 Nov 2026  
**Canonical repository:** `SudoMyNameIsMuD/AxNotesApp.Source`

**Core UX principle:** AxNotes should become easier to use as its implementation becomes more capable. Ordinary users should not need to understand Python, SQLite, UUIDs, metadata sidecars, or internal file-management behavior.

### Current Baseline

- P0 Steps 1 through 8 are complete.
- Working interactive CLI uses the `notes/` notebook layout.
- Clean Markdown contains no visible UUID comments.
- Durable entry identities are stored in validated JSON sidecars under `.AxNotes/metadata/`.
- SQLite is derived, disposable, and rebuildable from Markdown plus metadata.
- Renderer uses the `entry.entry_type` model contract.
- P0 is validated on Windows with OneDrive; macOS and Linux validation remain pending.

### Locked Format and Architecture Decisions

- `notes/` is the authoritative Markdown content directory.
- `AxNotes.toml` identifies an AxNotes notebook.
- `AxNotes init` creates `notes/`, `.AxNotes/metadata/`, and `AxNotes.toml`.
- `.AxNotes/index.sqlite3` is derived, created lazily, and may be rebuilt.
- Markdown owns entry text, type, task state, supporting details, and order.
- `.AxNotes/metadata/` owns durable identity and relationships.
- Supporting details do not receive independent UUIDs in metadata schema v1.
- AxNotes supports one supporting-detail level in v0.1.
- Display alignment is presentation-only; Markdown is not padded for terminal output.
- Metadata failure must never damage or rewrite Markdown.
- Metadata is committed before SQLite is refreshed.
- Normal packages remain complete runnable applications unless explicitly labeled as prototypes.

### P0: Storage and Durable Identity Foundation — Complete

#### Step 1: Notes-based notebook layout
- `notes/` replaced `daily/` for new notebooks.
- `.AxNotes/metadata/` reserved for durable identity sidecars.
- Clean Markdown writer and interactive CLI retained.

#### Step 2: Metadata schema and validation
- Added `src/AxNotes/metadata.py` and metadata tests.
- Added schema, UUID, ordinal, source, date, type, and fingerprint validation.
- Added deterministic JSON loading and serialization.

#### Step 3: Deterministic fingerprints
- Added full, content, parent, and text fingerprints.
- Added deterministic SHA-256 canonicalization, line-ending normalization, and Unicode NFC normalization.

#### Step 4: Pure reconciliation engine
- Added exact, task-state, detail, type-transition, structural, new, and ambiguous matching behavior.
- When identity is uncertain, AxNotes creates a new identity rather than guessing.

#### Step 5: Reconciliation hardening
- Added duplicate-content, insert, delete, reorder, state, detail, type, ambiguity, Unicode, and UUID-invariant coverage.

#### Step 6: Atomic metadata persistence
- Added temporary-file writing, validation, flushing, and atomic replacement.
- Previous valid sidecars remain intact when replacement fails.

#### Step 7: Notebook integration
- Added sidecar loading, reconciliation, atomic persistence, and post-metadata index refresh.
- Markdown remains unchanged during ordinary reconciliation.

#### Step 8: Metadata-aware indexing
- Added entry UUIDs to the derived SQLite index.
- SQLite rebuilds from authoritative Markdown plus durable metadata.
- Deleting and rebuilding SQLite preserves content and identity.

#### P0 exit status

- P0 Steps 1 through 8 are complete.
- CLI, metadata persistence, reconciliation, and index rebuilding are validated on Windows with OneDrive.
- Cross-platform validation on macOS and Linux remains pending.
- The durable identity foundation is ready for the v0.2 interface milestone.

### v0.2: Interface Improvement Roadmap

Each step includes implementation, tests, help/documentation updates, and regression validation.

#### 1. Inline rendering flow

- Render each normalized entry immediately after capture.
- Return to the writing prompt after entries and commands.
- Use the shared renderer for interactive output and command views.
- Keep UUIDs, metadata paths, SQLite details, and internal state out of user-facing output.
- Show concise validation messages without ending the session or exposing a traceback.

#### 2. Complete quick-entry notation

Support consistent notation:

```text
text    Normal note
[       Open task
[/      In-progress task
[x      Completed task
[>      Migrated task
[-      Canceled task
?       Question
!       Important entry
@       Event
>       Supporting detail
```

- Support explicit leading task markers and trailing task-state shorthand.
- Remove control markers from normalized entry text.
- Preserve ordinary punctuation and meaningful text.
- Reject empty markers without creating empty entries.

Example:

```text
- [Follow up with John Doe
[ ] Follow up with John Doe
-
```

#### 3. `/markdown` and `/md`

- Open today's Markdown file in the operating system's default Markdown application.
- Create today's file first when it does not exist.
- Keep the interactive AxNotes session running.
- Support Windows, macOS, and Linux without requiring Visual Studio Code.
- Report launch failures with a concise message rather than a traceback.

#### 4. Improved `/help`

Organize help into:

```text
Writing
Commands
Maintenance
Planned
```

- Show every active marker and command.
- Keep maintenance commands separate from everyday commands.
- Do not present planned commands as available until implemented.

#### 5. Wrapped rendering

- Wrap long entries to the terminal width.
- Align top-level continuation lines beneath entry text.
- Align detail continuation lines beneath detail text.
- Apply the same wrapping to inline output, `/today`, `/week`, `/search`, and standalone rendering.
- Keep alignment padding out of authoritative Markdown.

#### 6. `/lastweek`

- Display the previous Monday through Sunday.
- Group entries by date.
- Preserve supporting details beneath parents.
- Reuse the shared renderer and time-view formatting.

#### 7. `/month`

- Display the current calendar month grouped chronologically by date.
- Preserve entry order and parent-detail relationships.
- Begin with a reliable calendar-month view rather than an automated summary.

#### 8. Welcome note and `/clearwelcome`

- Create an example welcome note only when initializing a genuinely empty notebook.
- Demonstrate all active markers and key commands using neutral examples such as John Doe.
- Mark generated content with `axnotes_welcome: true` in frontmatter.
- Add `/clearwelcome` to remove an unchanged generated welcome note, its metadata sidecar, and derived index entries.
- Refuse automatic deletion when user content has been added or generated content has been modified.
- Never overwrite an existing note or add welcome content to an established notebook.

#### v0.2 completion target

- All eight interface steps implemented.
- Consistent inline and command rendering.
- Clean Markdown remains UUID-free.
- Ruff, pytest, and Git whitespace checks pass.
- Help, roadmap, changelog, and user documentation are updated with each step.
- Windows validation complete, with macOS and Linux validation where OS behavior differs.

### Future Identity-backed Entry Operations

Implement after the v0.2 interface milestone is stable:

- Change an existing task state.
- Edit an existing entry.
- Delete an entry safely.
- Move or migrate an entry to another day.
- Add a detail to a previously created entry.
- Add narrow `/undo` for the most recent AxNotes mutation.

Requirements:

- Safe failure and recovery behavior.
- Clear distinction between viewing and modifying older notes.
- No silent destructive edits.

### Rich Terminal Experience

- Replace plain `input()` with a richer terminal editing layer.
- Transform quick markers in place rather than echoing raw and normalized lines.
- Add slash-command suggestions and completion.
- Add input history and expected Left/Right/Home/End behavior.
- Improve long-line editing and wrapping.
- Gracefully handle Ctrl+C and EOF.
- Use optional color only where it conveys structure or state.

### Writing Assistance

#### Spellcheck

- Suggestions only; never silently autocorrect.
- Local-first and offline-capable.
- User dictionary for names, acronyms, companies, and technical terms.
- Ignore AxNotes markers and commands.
- Preserve Markdown until the user explicitly accepts a correction.
- Start with `/spellcheck` before real-time highlighting.

### Navigation, Safety, and Portability

#### Navigation

- Open today's Markdown in the configured/default editor.
- Open a search result in its source file.
- Jump directly to another date.

#### Backup and restore

Back up:

- `notes/`
- `.AxNotes/metadata/`
- `AxNotes.toml`

The disposable SQLite index does not require backup.

Add:

- Safe backup command.
- Staged restore workflow.
- Collision handling.
- Restore verification and rollback.

#### Data portability

- Markdown import.
- Plain Markdown export.
- Whole-notebook export.
- Migration strategy before authoritative format changes.
- Compatibility with earlier v0.1 notebooks where practical.

### Distribution and Project Maturity

- Keep `.venv` as the supported source/development workflow during v0.1.x.
- Add automated Windows, macOS, and Linux tests.
- Later provide standalone Windows, macOS, and Linux packages.
- Remove the Python/virtual-environment requirement for ordinary users once packaged releases are available.
- Add `CONTRIBUTING.md`, `SECURITY.md`, architecture/format documentation, issue templates, and pull-request templates.

### Test Architecture

Organize coverage into:

```text
tests/
├── conftest.py
├── test_interaction.py
├── test_renderer.py
├── test_parser_renderer.py
├── test_notebook_persistence.py
├── test_notebook_views.py
├── test_inline_cli.py
├── test_inline_commands.py
├── test_cli_commands.py
├── test_error_output.py
├── test_metadata.py
├── test_fingerprints.py
└── test_reconcile.py
```

Add injectable `input_fn` and `output_fn` to `interactive()` for reliable prompt-flow tests.

### Quality Gates for Every Commit

```powershell
python -m ruff check src tests
python -m pytest
git diff --check
```

For renderer-sensitive changes also run:

```powershell
axnotes render 2026-11-02
```

Requirements:

- No Python traceback during normal use.
- New Markdown remains UUID-free.
- No `.venv`, caches, personal notebooks, credentials, or secrets are committed.
- Every hands-on bug receives a regression test.
- GitHub remains the canonical source of truth.

### Versioning Recommendation

- Release the completed P0 identity foundation under v0.1.8.
- Use v0.2 for the interface improvement milestone defined above.
- Reserve v1.0 for a stable notebook format, dependable cross-platform installation, and mature core UX.

### Immediate Next Actions

1. Complete and publish the v0.1.8 P0 release.
2. Begin v0.2 Step 1: inline rendering flow.
3. Add tests and documentation with each interface step.
