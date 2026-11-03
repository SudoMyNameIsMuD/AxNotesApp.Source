# AxNotes Roadmap

**Updated:** 03 Nov 2026  
**Canonical repository:** `SudoMyNameIsMuD/AxNotesApp.Source`

> **Core UX principle:** AxNotes should become easier to use as its implementation becomes more capable. Ordinary users should not need to understand Python, SQLite, UUIDs, metadata sidecars, or internal file-management behavior.

## Current Baseline

- Working interactive CLI on the `notes/` notebook layout.
- Clean Markdown with no visible UUID comments in new notes.
- SQLite remains derived, disposable, and rebuildable.
- Shared renderer uses `entry.entry_type`.
- Canonical repository baseline: Ruff clean and 8 tests passing.
- Public GitHub source currently contains the P0 Step 1 application foundation. P0 Step 2 work was described in a handoff but must be recovered or reimplemented in the canonical repository before Steps 3 and 4.

## Locked Format and Architecture Decisions

- `notes/` is the authoritative Markdown content directory for new notebooks.
- `AxNotes.toml` identifies an AxNotes notebook.
- `AxNotes init` creates only `notes/`, `.AxNotes/metadata/`, and `AxNotes.toml`.
- `projects/` and `templates/` are not created until those features exist.
- `.AxNotes/index.sqlite3` is created lazily and remains derived/disposable.
- New Markdown must not contain visible `AxNotes:id` UUID comments.
- Markdown owns entry text, type, task state, supporting details, and order.
- `.AxNotes/metadata/` will own durable entry identity and relationships.
- Supporting details do not receive independent UUIDs in metadata schema v1.
- AxNotes supports one supporting-detail level in v0.1.
- Display alignment is presentation-layer behavior; do not pad authoritative Markdown for terminal alignment.
- Same-file reordering may preserve identity when entries can be matched confidently.
- External cross-file moves create new identity in schema v1; a future controlled move operation may preserve identity.
- Task-state changes preserve identity when reconciliation is unambiguous.
- Metadata failure must never damage or rewrite Markdown.
- Metadata commits before SQLite refresh.
- Normal development packages must remain complete runnable applications unless explicitly labeled as prototypes.

## P0: Storage and Durable Identity Foundation

### Step 1: Notes-based notebook layout — Complete

- `notes/` replaced `daily/` for new notebooks.
- `.AxNotes/metadata/` reserved for durable identity sidecars.
- Clean Markdown writer retained.
- Interactive CLI restored on top of the new layout.

### Step 2: Metadata schema and validation — Next canonical task

Recover or implement in the Git-controlled repository:

- `src/AxNotes/metadata.py`
- `tests/test_metadata.py`
- `MetadataEntry` and `MetadataFile` dataclasses.
- Schema-version validation.
- UUID validation.
- One-based ordinal validation and duplicate detection.
- Notebook-relative source validation.
- ISO source-date validation.
- Fingerprint-format validation.
- JSON load and deterministic serialization.
- Safe error classes for missing, malformed, or unsupported metadata.

Do not integrate metadata into normal capture yet.

### Step 3: Deterministic fingerprints — Planned

Create:

- `src/AxNotes/fingerprints.py`
- `tests/test_fingerprints.py`
- `docs/FINGERPRINTS.md`

Implement an immutable `FingerprintSet` containing:

- `full`: type, task state, text, ordered details.
- `content`: type, text, ordered details; ignores task state.
- `parent`: type and parent text; ignores state/details.
- `text`: parent text only; ignores type/state/details.

Requirements:

- SHA-256 with deterministic compact JSON.
- Fingerprint algorithm version marker.
- CRLF/CR to LF normalization.
- Unicode NFC normalization.
- Preserve case, punctuation, spelling, meaningful internal spaces, and detail order.
- Exact reference-vector tests.
- No UUID assignment, reconciliation, sidecar writes, SQLite changes, Markdown changes, or CLI changes.

### Step 4: Pure in-memory reconciliation engine — Planned

Create:

- `src/AxNotes/reconcile.py`
- `tests/test_reconcile.py`
- `docs/RECONCILIATION.md`

Matching passes:

1. Unique full fingerprint → exact match.
2. Unique content fingerprint → task-state change.
3. Unique parent fingerprint → supporting-detail change.
4. Compatible type transition with strong context.
5. Single changed entry bounded by matched neighbors.
6. New identity or ambiguous identity diagnostic.

Safety rule:

> When identity is uncertain, generate a new identity rather than attach an existing UUID to the wrong entry.

Step 4 remains pure: no filesystem writes, Markdown rewrites, SQLite changes, or CLI output.

### Step 5: Reconciliation hardening

- Expanded duplicate-content scenarios.
- Insert, delete, reorder, state-change, detail-change, and type-change matrix.
- Ambiguity diagnostics.
- One-to-one UUID invariants.
- Cross-platform and Unicode coverage.
- Property/invariant tests where practical.

### Step 6: Atomic metadata persistence

- Write sidecars to a temporary file.
- Flush and validate temporary JSON.
- Use atomic replacement.
- Preserve the previous sidecar on failure.
- Validate Windows and OneDrive behavior.
- Do not truncate authoritative metadata before replacement succeeds.

### Step 7: Notebook integration

- Load sidecars for parsed note files.
- Reconcile in memory.
- Atomically save replacement metadata.
- Refresh SQLite only after metadata succeeds.
- Keep Markdown unchanged during ordinary reconciliation.

### Step 8: Metadata-aware indexing

- Store UUIDs as derived index fields.
- Rebuild SQLite entirely from Markdown plus durable metadata.
- Confirm deleting SQLite never loses user content or identity.

### P0 exit criteria

- Notes layout, metadata schema, fingerprints, reconciliation, atomic writes, and index integration are complete.
- Full CLI continues working.
- Renderer and inline views are stable.
- Windows and macOS validation completed.
- Notebook format documented and suitable for a v0.2 milestone.

## P1: Core User Experience

### Shared renderer and alignment

Use the same renderer for capture, `/today`, `/week`, `/search`, standalone render, and future time views.

```text
 -  Normal note
[ ] Open task
[/] In-progress task
[x] Completed task
[>] Migrated task
[-] Canceled task
 ?  Question
 !  Important
 @  Event
     › Supporting detail
```

- Top-level wrapped lines align under entry text.
- Detail continuations align under detail text.
- Terminal-width-aware wrapping remains presentation-only.

### Inline rendering flow

After each entry:

1. Normalize and validate input.
2. Write clean Markdown.
3. Update metadata/index when integrated.
4. Render normalized result.
5. Return to the `- ` prompt.

Commands render inside the session and then return to the writing prompt.

### Time views

- `/lastweek`: previous Monday through Sunday.
- `/month`: current calendar month grouped by date.
- Later consider `/yesterday` and an explicit `/date` command.

### Search refinement

- Preserve `*`, `[ ]`, `[x]`, `!`, `?`, weekday, and date shortcuts.
- Search supporting details.
- Display parent plus matching details together.
- Add phrase search and date-range search.
- Add predictable broad-result limits and clearer no-result messages.
- Defer complex query grammar until basic search is stable.

## P2: Identity-backed Entry Operations

Implement only after P0 identity integration is stable:

1. Change an existing task state.
2. Edit an existing entry.
3. Delete an entry safely.
4. Move/migrate an entry to another day.
5. Add a detail to a previously created entry.
6. Narrow `/undo` for the most recent AxNotes mutation.

Requirements:

- Safe failure and recovery behavior.
- Clear distinction between viewing and modifying historical notes.
- No silent destructive edits.

## P3: Rich Terminal Experience

- Replace plain `input()` with a richer terminal editing layer.
- Transform quick markers in place rather than echoing raw and normalized lines.
- Add slash-command suggestions and completion.
- Add input history and expected Left/Right/Home/End behavior.
- Improve long-line editing and wrapping.
- Gracefully handle Ctrl+C and EOF.
- Add color only where it communicates structure/state.
- Provide no-color/accessibility-friendly behavior.

## P4: Writing Assistance

### Spellcheck

- Suggestions only; never silent autocorrect.
- Local-first and offline-capable.
- User dictionary for names, acronyms, companies, and technical/project terms.
- Ignore AxNotes markers and commands.
- Preserve Markdown until the user explicitly accepts a correction.
- Start with a future `/spellcheck` command before real-time highlighting.

## P5: Navigation, Safety, and Portability

### Navigation

- Open today's Markdown in the configured editor.
- Open a search result in its source file.
- Jump directly to another date.

### Backup and restore

Back up:

- `notes/`
- `.AxNotes/metadata/`
- `AxNotes.toml`

Do not require backup of the disposable SQLite index.

Add:

- Safe backup command.
- Staged restore workflow.
- Collision handling.
- Restore verification and rollback.

### Data portability

- Markdown import.
- Plain Markdown export.
- Whole-notebook export.
- Migration strategy before future authoritative format changes.
- Preserve compatibility with earlier v0.1 notebooks where practical.

## P6: Distribution and Project Maturity

- Keep `.venv` as the supported source/development workflow during v0.1.
- Add automated Windows, macOS, and Linux tests.
- Later provide standalone Windows, macOS, and Linux packages.
- Remove the Python/virtual-environment requirement for ordinary users once packaged releases are available.
- Add `CONTRIBUTING.md`, `SECURITY.md`, architecture/format documentation, issue templates, and pull-request templates.

## Test Architecture

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

## Quality Gates for Every Commit

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
- No `.venv`, caches, personal notebooks, or secrets committed.
- Every hands-on bug receives a regression test.
- GitHub repository remains the canonical source of truth.

## Versioning Recommendation

- Continue foundation and identity work under `v0.1.x`.
- Use `v0.2` for the first build running on the fully integrated metadata/fingerprint/reconciliation foundation.
- Reserve `v1.0` for a stable notebook format, dependable cross-platform installation, and mature core UX.

## Immediate Next Actions

1. Locate the previously implemented Step 2 `metadata.py` and `test_metadata.py`, or reimplement them in the canonical repository.
2. Verify Step 2 with Ruff and pytest.
3. Commit and push Step 2 separately.
4. Implement and commit Step 3 fingerprints.
5. Implement Step 4 reconciliation in two reviewable commits: foundation, then changed/ambiguous matching.
