## AxNotes Roadmap

**Updated:** 05 Nov 2026
**Canonical repository:** `SudoMyNameIsMuD/AxNotesApp.Source`

**Core UX principle:** AxNotes should become easier to use as its implementation becomes more capable. Ordinary users should not need to understand Python, SQLite, UUIDs, metadata sidecars, or internal file-management behavior.

### Current Baseline

- P0 Steps 1 through 8 are complete.
- The current v0.1.8 CLI uses the `notes/` daily-file layout; migrated and newly initialized v0.2 notebooks will use one authoritative `notebook.md` file.
- Clean Markdown contains no visible UUID comments.
- Durable entry identities are stored in validated JSON sidecars under `.AxNotes/metadata/`.
- SQLite is derived, disposable, and rebuildable from Markdown plus metadata.
- Renderer uses the `entry.entry_type` model contract.
- P0 is validated on Windows with OneDrive; macOS and Linux validation remain pending.

### Locked Format and Architecture Decisions

- Current v0.1 notebooks use `notes/` as authoritative Markdown; migrated and newly initialized v0.2 notebooks will use one authoritative `notebook.md` file.
- `AxNotes.toml` identifies an AxNotes notebook.
- Current v0.1 `AxNotes init` creates `notes/`, `.AxNotes/metadata/`, and `AxNotes.toml`; v0.2 initialization will create `notebook.md`, `.AxNotes/metadata/`, and `AxNotes.toml` after the single-file format is complete.
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

### v0.2: Single-File Notebook and Interface Roadmap

AxNotes v0.2 will migrate from one Markdown file per day to one authoritative `notebook.md` file organized by year, month, day, and section headings. The migration must preserve durable entry identities, clean Markdown, atomic persistence, metadata sidecars, the rebuildable SQLite index, and compatibility with existing v0.1 notebooks.

This is a foundational storage change. Implement and validate the single-file model before building section-aware views, `/lastweek`, or `/month`.


#### Confirmed v0.2 Design Decisions

1. **Authoritative storage:** v0.1 notebooks continue using dated files; v0.2 uses one authoritative `notebook.md` only after explicit migration.
2. **Metadata layout:** migrated v0.2 notebooks use one `.AxNotes/metadata/notebook.json` sidecar.
3. **`/md` behavior:** `/md` opens `notebook.md`; `/today` remains the current-day CLI view.
4. **Manual headings:** all Markdown heading levels are accepted with validation and hierarchy repair.
5. **Event notation:** both leading `@Owners Meeting` and trailing `Owners Meeting @` create an event section.
6. **Divider semantics:** a divider is an unnamed structural boundary and ends supporting-detail attachment eligibility.
7. **Release scope:** v0.2 includes both the single-file migration and the planned interface improvements.

#### Target Notebook Layout

```text
AxNotes-Notebook/
├── notebook.md
├── AxNotes.toml
└── .AxNotes/
    ├── metadata/
    │   └── notebook.json
    └── index.sqlite3
```

#### Canonical Heading Hierarchy

| Level | Purpose | Example |
|---|---|---|
| `#` | Notebook title | `# AxNotes Notebook` |
| `##` | Year | `## 2026` |
| `###` | Month | `### November` |
| `####` | Day | `#### Thursday \| 05NOV26` |
| `#####` | Named section | `##### Follow-Up` |
| `##### @` | Event section | `##### @ Owners Meeting` |

Example:

```markdown
# AxNotes Notebook

## 2026

### November

#### Thursday | 05NOV26

##### General Notes

- Follow up with John Doe
[ ] Prepare the weekly report

___

##### @ Owners Meeting

  › 05-Nov-2026 2:00 PM

- Notes taken during the Owners Meeting
[ ] Send the meeting notes
  › Confirm the due date
```

#### Storage and Architecture Rules

- `notebook.md` becomes authoritative for entry text, entry type, task state, supporting details, section context, and order.
- `.AxNotes/metadata/notebook.json` owns durable entry identity and fingerprints.
- `.AxNotes/index.sqlite3` remains derived, disposable, and rebuildable.
- Year, month, day, and section headings are structural Markdown in schema v1 and do not receive durable UUIDs.
- Supporting details remain attached to their parent and do not receive independent UUIDs in schema v1.
- Display alignment remains presentation-only.
- All Markdown and metadata replacements must be atomic.
- A failed migration or write must leave the prior valid notebook intact.
- Existing `notes/YYYY-MM-DD.md` notebooks remain supported until explicitly migrated.

#### Single-File Trade-Offs and Safeguards

- A OneDrive conflict can affect the full notebook, so atomic writes and backups are mandatory.
- Appending to the current day should avoid rewriting unrelated content when practical, but the final replacement must remain atomic.
- Editing an older date requires safe insertion into the middle of `notebook.md`.
- Validate performance with representative notebooks containing approximately 10,000, 50,000, and 100,000 entries.
- Parsing should remain linear, and search should use the derived index rather than reparsing for every query.

#### Migration Command

Add an explicit command:

```text
axnotes migrate single-file
```

Migration must:

1. Back up `notes/`, `.AxNotes/metadata/`, and `AxNotes.toml`.
2. Read dated Markdown files in chronological order.
3. Build `notebook.md` in a temporary location.
4. Preserve existing entry UUIDs.
5. Generate and validate `.AxNotes/metadata/notebook.json`.
6. Rebuild SQLite from the generated Markdown and metadata.
7. Compare source and destination entry counts and UUIDs.
8. Atomically install the new notebook and metadata.
9. Keep the old notes directory as `notes.pre-single-file-backup/`.
10. Never silently delete the backup.

Do not silently migrate existing notebooks during startup or `AxNotes init`.

#### Migration Validation

- Every source entry appears exactly once in `notebook.md`.
- Existing UUIDs remain unchanged.
- Supporting details remain attached to their parents.
- Dates are placed under the correct year and month headings.
- Existing Markdown remains available in the retained backup.
- Rebuilding SQLite preserves search results and durable identities.
- Failed validation prevents installation of the generated files.

### AxNotes Key

The AxNotes Key shows how each entry type appears in the CLI after rendering.

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

### Quick-Entry Notation

| Entry type | Accepted quick-entry notation | Shortest shortcut | Markdown marker | Rendered marker | Example quick entry |
|---|---|---|---|---|---|
| Normal note | Plain text | Plain text | `-` | ` - ` | `Follow up with John Doe` |
| Open task | Leading `[` or `[ ]` | `[` | `[ ]` | `[ ]` | `[Follow up with John Doe` |
| In-progress task | Leading or trailing `[/` or `[/]` | `[/` | `[/]` | `[/]` | `Follow up with John Doe [/` |
| Completed task | Leading or trailing `[x` or `[x]` | `[x` | `[x]` | `[x]` | `Follow up with John Doe [x` |
| Migrated task | Leading or trailing `[>` or `[>]` | `[>` | `[>]` | `[>]` | `Follow up with John Doe [>` |
| Canceled task | Leading or trailing `[-` or `[-]` | `[-` | `[-]` | `[-]` | `Follow up with John Doe [-` |
| Question | Leading or trailing `?` | `?` | `?` | ` ? ` | `Does John Doe have the update?` |
| Important entry | Leading or trailing `!` | `!` | `!` | ` ! ` | `John Doe needs the final report !` |
| Event | Leading or trailing `@` | `@` | Event-section heading | ` @ ` | `Meeting with John Doe @` |
| Supporting detail | Leading or trailing `>` | `>` | `  ›` | `     ›` | `Confirm the due date >` |

Important distinctions:

- `>` identifies a supporting detail.
- `[>` or `[>]` identifies a migrated task.
- `[` is the shortest shortcut for an open task.
- AxNotes converts quick-entry notation into the corresponding entry type, task state, entry text, and canonical Markdown marker.
- Trailing shortcuts are removed from entry text during normalization.
- The CLI applies presentation spacing to produce the rendered marker.
- Display alignment is never written into Markdown solely for appearance.

### Terminology Glossary

| Term | Definition |
|---|---|
| **Entry** | One AxNotes content item, such as a normal note, task, question, important entry, event, or supporting detail. |
| **Entry type** | The semantic category assigned to an entry. |
| **Task state** | Open, in progress, completed, migrated, or canceled. |
| **Entry text** | User-written content after quick-entry notation is interpreted. |
| **Quick-entry notation** | Abbreviated syntax accepted while capturing an entry. |
| **Shortcut** | The shortest accepted quick-entry notation. |
| **Normalization** | Conversion into canonical entry type, task state, entry text, and Markdown marker. |
| **Markdown marker** | The canonical marker written to authoritative Markdown. |
| **Rendered marker** | The marker and presentation spacing displayed in the CLI. |
| **Section** | A named structural region beneath a day heading. |
| **Event section** | A section created by a newly captured event and paired with a generated timestamp. |
| **Divider** | A structural horizontal rule stored as `___`; it separates content but does not create a named section. |
| **Supporting detail** | A subordinate line attached to the preceding eligible entry in the current section. |
| **Authoritative Markdown** | `notebook.md` after migration; dated files under `notes/` before migration. |
| **Metadata sidecar** | JSON that stores durable identity and fingerprints without visible UUIDs in Markdown. |
| **Durable identity** | The UUID used to recognize the same logical entry after supported changes. |
| **Derived index** | Rebuildable SQLite used for fast search. |
| **Writing prompt** | The `- ` prompt used for entries and slash commands. |
| **Inline command output** | Command results displayed before AxNotes returns to the writing prompt. |

### Interface and Section Implementation Sequence

#### Step 1: Single-File Notebook Foundation

- Complete: add `notebook.md` discovery, creation, date-aware loading, and atomic writing.
- Complete: add `notebook.json` metadata loading and atomic persistence.
- Complete: update indexing to derive rows from `notebook.md` plus `notebook.json`; rebuilds install atomically.
- Complete: keep v0.1 daily-file notebooks readable until explicit migration.
- Complete: add `axnotes migrate single-file`, source/configuration backups, UUID/count validation, rollback, and migration regression tests.

#### Step 2: Prompt Continuity and Inline Command Output

- Do not print a normalized second copy after successful capture.
- Continue displaying concise validation messages.
- Render command results inside the active session.
- Return to the writing prompt after entries and commands.
- Keep UUIDs, metadata paths, SQLite details, and internal state out of normal output.
- Defer true in-place marker replacement to a future rich terminal editor.

#### Step 3: Complete Quick-Entry Notation

- Complete: implement all entry and task-state notation in the table above.
- Complete: normalize accepted notation into canonical Markdown markers and entry text.
- Complete: remove trailing shortcuts from entry text while preserving meaningful punctuation and internal marker characters.
- Complete: reject empty markers without creating entries.
- Event-section formatting and generated timestamps remain Step 6.

#### Step 4: Headings and Dividers

Accept structural headings:

```text
# Notebook-level heading
## Year-level heading
### Month-level heading
#### Day-level heading
##### Section heading
```

AxNotes accepts manual headings at all Markdown levels with validation and hierarchy repair.

Manual-heading rules:

- Preserve a valid manual heading exactly when it fits the current hierarchy.
- Validate that heading text is nonempty.
- Reject a heading that cannot be placed safely without ambiguity.
- Repair missing structural parents only when the intended year, month, day, or section context can be determined unambiguously.
- Never silently move existing entries or overwrite an existing structural heading.
- Report the repair or rejection with a concise user-facing message.
- Keep `/newsection` as the preferred way to create a level-five section heading.
- Add regression tests for valid headings, skipped levels, duplicate structural headings, hierarchy repair, and rejected ambiguous input.

Support divider input:

```text
___
/divider
```

Rules:

- Three or more underscores alone normalize to `___`.
- Do not add a normal-note marker.
- Do not create consecutive dividers.
- A divider does not create a named section.
- A divider is an unnamed structural boundary and ends supporting-detail attachment eligibility.
- A supporting detail must not attach across a divider.
- `_`, `__`, and underscores inside ordinary text remain normal text.

#### Step 5: Named Sections

Add:

```text
/newsection Follow-Up
/new section Follow-Up
```

Rules:

- Create `##### Follow-Up` beneath the current day.
- Insert `___` before the section when appropriate.
- Do not duplicate adjacent dividers.
- Reject empty section titles.
- Allow repeated section names.
- Keep subsequent entries under the current section.

#### Step 6: Event Sections and Timestamps

Newly captured events create sections using either leading or trailing quick-entry notation:

```text
@Owners Meeting
Owners Meeting @
```

Both forms normalize to the same event title and create the same event section.

Stored beneath the current day as:

```markdown
___

##### @ Owners Meeting

  › 05-Nov-2026 2:00 PM
```

Rules:

- Preserve `@` in the section heading.
- Generate one timestamp supporting detail.
- Round to the nearest 15 minutes; halfway values round forward.
- Preserve date correctly across midnight.
- Inject the clock for deterministic tests.
- Prevent duplicate generated timestamps.
- Historical `@` entries remain unchanged unless explicitly migrated later.

#### Step 7: Current-Section and Supporting-Detail Rules

- The latest section heading is the current section.
- Notes and tasks remain beneath that section until another section begins.
- A supporting detail attaches only to the preceding eligible entry in the current section.
- Do not attach details across a divider, day, month, year, or section boundary.
- An orphan detail returns: `A supporting detail needs a parent entry in the current section.`
- The generated event timestamp is explicitly attached to the event heading by the event workflow.

#### Step 8: `/markdown` and `/md`

- `/md` and `/markdown` open `notebook.md` in the operating system's default Markdown application.
- `/today` remains the current-day CLI view and does not open a separate dated file.
- Keep AxNotes running and return to the writing prompt.
- Support paths containing spaces.
- Mock operating-system launch behavior in tests.

#### Step 9: Improved `/help`

Organize help into:

```text
Writing
Commands
Maintenance
Planned
```

Include headings, `___`, `/divider`, `/newsection`, and event-section behavior only when implemented.

#### Step 10: Wrapped Rendering

- Align top-level continuation lines beneath entry text.
- Align supporting-detail continuation lines beneath detail text.
- Apply consistent wrapping to `/today`, `/week`, `/search`, and standalone views.
- Keep display spacing out of authoritative Markdown.

#### Step 11: Section-Aware Views and Search

- `/today` selects the current day subtree.
- `/week` selects the current Monday-through-Sunday range.
- Search returns matching entries with year, month, day, and nearest section context.
- Do not return dividers as standalone results.
- Section headings may be searchable by title.
- Keep supporting details with matching parents.

#### Step 12: `/lastweek`

- Display the previous Monday through Sunday.
- Preserve chronological date, section, entry, and detail order.

#### Step 13: `/month`

- Display the current month subtree.
- Preserve date, section, entry, and parent-detail order.
- Begin with a reliable view rather than an automated summary.

#### Step 14: Welcome Note and `/clearwelcome`

- Create examples only in a genuinely empty notebook.
- Use neutral examples such as John Doe.
- Mark generated content with `axnotes_welcome: true` in configuration or metadata appropriate to the single-file model.
- Never overwrite existing content.
- `/clearwelcome` removes only unchanged generated content and associated derived state.
- Refuse automatic deletion if the user modified the examples or added personal content.

### Parser and Model Requirements

Recognition order should account for:

```text
1. Frontmatter or notebook metadata markers, if used
2. Code fences
3. Notebook title
4. Year heading
5. Month heading
6. Day heading
7. Section or event-section heading
8. Divider
9. Supporting detail
10. Task
11. Question or important entry
12. Normal note
```

Requirements:

- Preserve heading level and structural context.
- Accept all Markdown heading levels with validation and hierarchy repair.
- Do not silently repair ambiguous hierarchy.
- Ignore heading-like content inside fenced code.
- Never parse headings or dividers as normal notes.
- Maintain entry and supporting-detail order.
- Keep legacy v0.1 daily notes parseable during migration.
- Keep normalized entries independent from CLI alignment.

### Metadata, Reconciliation, and Indexing

- Move migrated metadata to `.AxNotes/metadata/notebook.json`.
- Each entry retains `source_date` and section context.
- Preserve existing UUIDs during migration.
- Reconciliation matches logical entries across headings inserted around them.
- Headings and dividers do not receive UUIDs in schema v1.
- Index rows include entry UUID, date, and section context as derived fields.
- Rebuilding SQLite from `notebook.md` and `notebook.json` preserves search and identity.
- Metadata synchronization must not rewrite user headings.

### Backward Compatibility

- Do not require immediate migration.
- Do not silently convert old notebooks.
- Continue opening existing daily-file notebooks until the explicit migration succeeds.
- Preserve old events, supporting details, metadata sidecars, and indexes.
- Do not convert historical event entries into event sections automatically.
- Keep the pre-migration backup until the user explicitly removes it.

### Required Testing

Create or update tests for:

- Single-file creation and atomic replacement.
- Migration success, rollback, counts, UUID preservation, and retained backup.
- Year, month, day, section, and event heading parsing.
- Manual headings at all levels, including validation, safe hierarchy repair, and ambiguous-input rejection.
- Leading and trailing event notation producing equivalent event sections.
- Divider notation, `/divider`, and prevention of supporting-detail attachment across dividers.
- `/newsection` and `/new section`.
- Event timestamp rounding and midnight rollover.
- Current-section tracking and orphan-detail rejection.
- Prompt continuity and no duplicate visual output.
- All quick-entry notation.
- `/today`, `/week`, `/lastweek`, `/month`, and search context.
- Metadata validity and absence of visible UUID comments.
- SQLite deletion and rebuild.
- Existing v0.1 notebook compatibility.
- Representative performance at 10,000, 50,000, and 100,000 entries.

### Manual Smoke Test

After migrating a disposable test notebook:

```text
# Project Notes
Normal note before a section
___
/newsection Follow-Up
Follow up with John Doe
[Prepare the report
>Confirm the due date
@Owners Meeting
Meeting discussion
[Send meeting notes
/today
/search John Doe
/quit
```

Verify `notebook.md` contains the expected year, month, day, section, entries, timestamp, and supporting-detail hierarchy. Also verify:

- Every source entry occurs once.
- No heading or divider receives a normal-note marker.
- No duplicate divider or event timestamp exists.
- Existing UUIDs remain stable.
- Metadata JSON is valid.
- No `.tmp` files remain.
- Search includes section context.
- The original daily-file backup remains intact.
- No traceback appears.

### Quality Gate

```powershell
python -m ruff check src tests
python -m pytest
git diff --check
```

Then review:

```powershell
git status --short
git --no-pager diff --stat
git --no-pager diff
```

Do not commit or push until migration, smoke testing, and the final diff are reviewed.

### v0.2 Definition of Done

- `notebook.md` is the authoritative format for migrated or newly initialized v0.2 notebooks.
- v0.1 dated files remain usable before explicit migration.
- Migrated metadata is stored in one `.AxNotes/metadata/notebook.json` sidecar.
- `/md` opens `notebook.md`, while `/today` remains the current-day CLI view.
- Manual headings at all levels are validated and repaired only when unambiguous.
- Leading and trailing `@` both create event sections.
- Dividers end supporting-detail attachment eligibility.
- Explicit migration preserves all content and durable identities.
- Failed migration or persistence leaves the previous notebook intact.
- Year, month, day, section, and event hierarchy works.
- Headings and dividers remain structural Markdown.
- Event sections receive one rounded timestamp.
- Supporting details remain within section boundaries.
- `/today`, `/week`, `/lastweek`, `/month`, and search understand hierarchy.
- Existing v0.1 notebooks remain usable before migration.
- Metadata and SQLite remain valid, derived, and recoverable.
- Ruff, pytest, whitespace, performance, and manual smoke tests pass.

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

- Open `notebook.md` in the configured/default editor with `/md` or `/markdown`.
- Use `/today` for the current-day CLI view.
- Open a search result in `notebook.md` and, where the host editor supports it, navigate to the matching heading or line.
- Jump directly to another date within the notebook hierarchy.

#### Backup and restore

Back up according to notebook format.

For v0.1 daily-file notebooks:

- `notes/`
- `.AxNotes/metadata/`
- `AxNotes.toml`

For migrated or newly initialized v0.2 single-file notebooks:

- `notebook.md`
- `.AxNotes/metadata/notebook.json`
- `AxNotes.toml`
- `notes.pre-single-file-backup/` until migration acceptance

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
- Use v0.2 for the explicit single-file notebook migration and the interface-improvement milestone defined above.
- Reserve v1.0 for a stable notebook format, dependable cross-platform installation, and mature core UX.

### Immediate Next Actions

1. Complete and publish the v0.1.8 P0 release.
2. Complete representative performance checks for 10,000, 50,000, and 100,000-entry single-file notebooks.
3. Continue with v0.2 Step 3: complete quick-entry notation, then implement heading/divider and section behavior.
4. Add tests and documentation with every storage and interface step.
