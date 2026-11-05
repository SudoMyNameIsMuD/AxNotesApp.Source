## AxNotes Roadmap

**Updated:** 04 Nov 2026  
**Canonical repository:** `SudoMyNameIsMuD/AxNotesApp.Source`

**Core UX principle:** AxNotes should become easier to use as its implementation becomes more capable. Ordinary users should not need to understand Python, SQLite, UUIDs, metadata sidecars, or internal file-management behavior.

### Current Baseline

- P0 Steps 1 through 8 are complete.
- Working interactive CLI uses the `notes/` notebook layout.
- Authoritative Markdown contains no visible UUID comments.
- Durable entry identities are stored in validated metadata sidecars under `.AxNotes/metadata/`.
- The derived index is disposable and rebuildable from authoritative Markdown and metadata sidecars.
- Renderer uses the `entry.entry_type` model contract.
- P0 is validated on Windows with OneDrive; macOS and Linux validation remain pending.

### Locked Format and Architecture Decisions

- `notes/` contains authoritative Markdown.
- `AxNotes.toml` identifies an AxNotes notebook.
- `AxNotes init` creates `notes/`, `.AxNotes/metadata/`, and `AxNotes.toml`.
- `.AxNotes/index.sqlite3` is the derived index, created lazily, and may be rebuilt.
- Authoritative Markdown owns entry text, entry type, task state, supporting details, and order.
- Metadata sidecars under `.AxNotes/metadata/` own durable identity and relationships.
- Supporting details do not receive independent UUIDs in metadata schema v1.
- AxNotes supports one level of supporting detail in v0.1.
- Rendered marker alignment is presentation-only; Markdown is not padded for terminal output.
- Metadata failure must never damage or rewrite Markdown.
- Metadata sidecars are committed before the derived index is refreshed.
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

AxNotes v0.2 will improve the writing-first CLI while preserving the durable identity, metadata, reconciliation, and indexing foundation completed during P0.

Each interface step includes implementation, regression tests, help updates, and documentation updates.

#### AxNotes Key

The AxNotes Key shows the rendered marker for each entry type or task state.

```text
 -  Normal note
[ ] Open task
[/] In-progress task
[x] Completed task
[>] Migrated task
[-] Canceled task
 ?  Question
 !  Important entry
 @  Event
     › Supporting detail
```

#### Quick-Entry Notation

Quick-entry notation is the abbreviated syntax accepted while capturing an entry. AxNotes normalizes that input into an entry type, task state when applicable, entry text, and canonical Markdown marker.

| Entry type | Quick-entry notation | Shortest shortcut | Markdown marker | Rendered marker | Example quick entry |
|---|---|---|---|---|---|
| Normal note | Plain text | Plain text | `-` | ` - ` | `Follow up with John Doe` |
| Open task | Leading `[` or `[ ]` | `[` | `[ ]` | `[ ]` | `[Follow up with John Doe` |
| In-progress task | Leading or trailing `[/` or `[/]` | `[/` | `[/]` | `[/]` | `Follow up with John Doe [/` |
| Completed task | Leading or trailing `[x` or `[x]` | `[x` | `[x]` | `[x]` | `Follow up with John Doe [x` |
| Migrated task | Leading or trailing `[>` or `[>]` | `[>` | `[>]` | `[>]` | `Follow up with John Doe [>` |
| Canceled task | Leading or trailing `[-` or `[-]` | `[-` | `[-]` | `[-]` | `Follow up with John Doe [-` |
| Question | Leading or trailing `?` | `?` | `?` | ` ? ` | `Does John Doe have the update?` |
| Important entry | Leading or trailing `!` | `!` | `!` | ` ! ` | `John Doe needs the final report !` |
| Event | Leading or trailing `@` | `@` | `@` | ` @ ` | `Meeting with John Doe @` |
| Supporting detail | Leading or trailing `>` | `>` | `  ›` | `     ›` | `Confirm the due date >` |

##### Important distinctions

- `>` identifies a supporting detail.
- `[>` or `[>]` identifies a migrated task.
- `[` is the shortest shortcut for an open task.
- The closing `]` may be omitted when using task-state shorthand.
- AxNotes converts accepted quick-entry notation into the corresponding entry type, task state, and canonical Markdown marker. AxNotes places the canonical Markdown marker at the beginning of the stored entry. Trailing quick-entry notation is removed from the entry text during normalization.
- The CLI applies presentation spacing to produce the rendered marker.
- Display alignment is not written into Markdown solely for appearance.

##### Normalization example

```text
Captured input:
Follow up with John Doe [x

Normalized entry:
Entry type: Task
Task state: Completed
Entry text: Follow up with John Doe

Authoritative Markdown:
[x] Follow up with John Doe

Rendered marker and entry text:
[x] Follow up with John Doe
```

Supporting detail example:

```text
Captured input:
Confirm the due date >

Normalized entry:
Entry type: Supporting detail
Entry text: Confirm the due date

Authoritative Markdown:
  › Confirm the due date

Rendered marker and entry text:
     › Confirm the due date
```

#### Terminology Glossary

| Term | Definition |
|---|---|
| **Entry** | One AxNotes content item. Top-level entries include a normal note, task, question, important entry, event, or decision; a top-level entry may have supporting details. |
| **Entry type** | The semantic category assigned to a top-level entry, such as a normal note, task, question, important entry, event, or decision. A supporting detail is attached to a top-level entry rather than stored as a separate `EntryType`. |
| **Task state** | The condition of a task: open, in progress, completed, migrated, or canceled. |
| **Entry text** | The user-written content after normalization has interpreted the quick-entry notation. Leading notation determines the Markdown marker; trailing quick-entry notation is excluded from entry text during normalization. |
| **Quick-entry notation** | Any abbreviated syntax AxNotes accepts while the user captures an entry. |
| **Shortcut** | The shortest accepted quick-entry notation for an entry type or task state. |
| **Normalization** | The process that converts quick-entry notation into the canonical entry type, task state, entry text, and Markdown marker. |
| **Markdown marker** | The canonical marker written to authoritative Markdown. |
| **Rendered marker** | The Markdown marker plus presentation spacing displayed in the CLI. |
| **Supporting detail** | A subordinate line attached to the preceding top-level entry. Supporting details use `›` in Markdown and rendered views. |
| **Writing prompt** | The `- ` prompt where the user captures an entry or enters a slash command. |
| **Inline command output** | Command results displayed inside the active AxNotes session before returning to the writing prompt. |
| **Authoritative Markdown** | The files under `notes/` that store entry text, entry type, task state, supporting details, and order. |
| **Metadata sidecar** | A JSON sidecar under `.AxNotes/metadata/` that stores durable identity and fingerprints without adding visible UUIDs to authoritative Markdown. |
| **Durable identity** | The UUID that allows AxNotes to recognize the same logical entry after supported changes. |
| **Derived index** | The rebuildable SQLite index used for fast search. The index is recreated from authoritative Markdown and metadata sidecars when needed. |

#### Terminology Structure

Use this hierarchy consistently in the roadmap, README, `/help`, code comments, and tests:

```text
Entry
├── Entry type
├── Task state, when applicable
├── Entry text
└── Supporting details

Input terminology
├── Quick-entry notation
└── Shortcut

Output terminology
├── Markdown marker
└── Rendered marker
```

#### 1. Prompt Continuity and Inline Command Output — Complete

The current CLI uses Python's plain `input()` function. The terminal already echoes captured input, so AxNotes must not print a second copy after saving the entry.

Required capture flow:

```text
Capture input
    ↓
Normalize and validate
    ↓
Write authoritative Markdown
    ↓
Synchronize metadata
    ↓
Refresh the derived index
    ↓
Return to the writing prompt
```

Requirements:

- Do not print a normalized second copy after successful capture.
- Continue displaying concise validation messages.
- Continue rendering command results inside the active session.
- Return to the writing prompt after entries and commands.
- Keep UUIDs, metadata paths, SQLite details, and internal state out of normal user output.
- Do not expose Python tracebacks during ordinary use.

Commands that continue to produce inline command output include:

```text
/today
/week
/search
/help
/reindex
/sync
```

True in-place replacement of raw quick-entry notation with a rendered marker is deferred until the future rich terminal-editing milestone.

#### 2. Complete Quick-Entry Notation

Implement and test all quick-entry notation shown in the table above.

Requirements:

- Support all five task states.
- Support leading and trailing task-state notation.
- Support questions, important entries, events, and supporting details.
- Convert quick-entry notation into the canonical Markdown marker.
- Remove trailing shortcuts from entry text.
- Preserve ordinary punctuation and meaningful text.
- Reject empty markers without creating empty entries.
- Preserve the existing Markdown storage format.

#### 3. `/markdown` and `/md`

Add two equivalent commands:

```text
/markdown
/md
```

Requirements:

- Open today's Markdown file in the operating system's default Markdown application.
- Create today's Markdown file first if it does not exist.
- Keep AxNotes running after the file opens.
- Return to the writing prompt.
- Support paths containing spaces.
- Support Windows, macOS, and Linux without requiring Visual Studio Code.
- Display a concise error instead of a traceback if the file cannot be opened.
- Mock the operating-system opener during automated tests.

#### 4. Improved `/help`

Organize help into clear sections:

```text
Writing
Commands
Maintenance
Planned
```

Requirements:

- Use terminology from the glossary.
- Show active quick-entry notation and shortcuts.
- Explain Markdown markers separately from rendered markers when needed.
- Keep maintenance commands separate from everyday commands.
- Do not present planned commands as available.
- Keep `/help`, the roadmap, and later README documentation consistent.

#### 5. Wrapped Rendering

Add terminal-width-aware wrapping to rendered output.

Top-level example:

```text
[ ] Follow up with John Doe regarding the updated information and confirm
    the expected completion date.
```

Supporting detail example:

```text
     › Include the supporting information requested during the meeting
       and note any remaining open items.
```

Requirements:

- Align top-level continuation lines beneath entry text.
- Align supporting detail continuation lines beneath their text.
- Apply the same rules to `/today`, `/week`, `/search`, and standalone rendering.
- Preserve entry order and parent-detail relationships.
- Keep display alignment out of authoritative Markdown.
- Defer cursor-aware wrapped editing until the future rich terminal interface.

#### 6. `/lastweek`

Add:

```text
/lastweek
```

Requirements:

- Display the previous Monday through Sunday.
- Group entries chronologically by date.
- Preserve entry order within each date.
- Keep supporting details attached to their parent entries.
- Reuse the shared renderer and time-view formatting.
- Return to the writing prompt.

#### 7. `/month`

Add:

```text
/month
```

Requirements:

- Display the current calendar month.
- Group entries chronologically by date.
- Preserve entry order and parent-detail relationships.
- Reuse the shared renderer.
- Begin with a reliable monthly view rather than an automated summary.
- Return to the writing prompt.

#### 8. Welcome Note and `/clearwelcome`

When `AxNotes init` creates a genuinely empty notebook, create a welcome note demonstrating all active entry types, task states, quick-entry notation, and key commands.

Requirements:

- Use neutral examples such as John Doe.
- Mark the generated note with `axnotes_welcome: true` in frontmatter.
- Never overwrite an existing note.
- Never add welcome content to an established notebook.
- Add `/clearwelcome` to remove an unchanged generated welcome note.
- Remove the associated metadata sidecar and refresh the derived index.
- Keep AxNotes running after removal.
- Refuse automatic deletion if generated content was modified or user content was added.
- Direct the user to `/md` for manual editing when automatic removal is refused.

#### v0.2 Completion Target

AxNotes v0.2 is complete when:

- All eight interface steps are implemented.
- Quick-entry terminology is consistent across the roadmap, `/help`, tests, and documentation.
- Inline command output and writing-prompt continuity work reliably.
- Markdown markers and rendered markers remain clearly separated.
- Authoritative Markdown remains clean and contains no visible UUID comments.
- Ruff, pytest, and Git whitespace checks pass.
- Regression tests cover each notation form, command, view, and safety rule.
- Windows validation is complete.
- macOS and Linux validation is completed where operating-system behavior differs.

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
- Transform quick-entry notation in place rather than echoing raw and normalized lines.
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
2. Begin v0.2 Step 2: complete quick-entry notation.
3. Add tests and documentation with each interface step.
