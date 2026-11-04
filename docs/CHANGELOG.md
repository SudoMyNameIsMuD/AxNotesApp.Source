# Changelog

## 0.1.6 Full Working Build
- Restored the interactive writing CLI on top of the new `notes/` storage architecture.
- Restored `/today`, `/week`, `/search`, `/help`, `/reindex`, `/sync`, and `/quit`.
- Added shared entry renderer with aligned top-level markers.
- Kept new Markdown free of UUID comments.
- Indexing now reads only `notes/*.md`.
- Added a clean message instead of a traceback when AxNotes is started outside an initialized notebook.
- Kept `.AxNotes/metadata/` ready for the next durable identity implementation step.

## 0.1.7 - 04 Nov 2026
Added durable entry identities under .AxNotes/metadata/.
Added deterministic entry fingerprints and conservative reconciliation.
Added atomic metadata writes with temporary-file validation and replacement.
Added automatic metadata and search-index synchronization.
Preserved clean, human-readable Markdown without visible UUID comments.
Fixed the renderer to use the correct entry.entry_type model field.
Expanded metadata, fingerprint, reconciliation, and persistence tests.
Verified with Ruff, 50 passing tests, valid generated JSON sidecars, and interactive smoke testing.

## 0.1.8 - 04 Nov 2026

### Added

- Added durable entry identities using validated JSON sidecars under `.AxNotes/metadata/`.
- Added deterministic full, content, parent, and text fingerprints.
- Added conservative identity reconciliation for task-state, detail, type, order, and content changes.
- Added atomic metadata persistence with temporary-file validation and replacement.
- Added automatic metadata synchronization for Markdown files in `notes/`.
- Added metadata-aware SQLite indexing with entry UUIDs derived from durable sidecar metadata.
- Added index rebuilding from authoritative Markdown and metadata sidecars.

### Improved

- Kept Markdown as the authoritative source for entry text, type, task state, supporting details, and order.
- Kept SQLite derived, disposable, and rebuildable.
- Updated metadata sidecars to mirror their Markdown source paths.
- Improved handling of missing metadata without hiding malformed or invalid sidecars.
- Expanded automated coverage to 51 passing tests.
- Updated the roadmap, README, and release documentation for the completed P0 foundation.

### Fixed

- Fixed the renderer to use the `entry.entry_type` model contract.
- Fixed metadata and search-index synchronization.
- Fixed SQLite rebuilding so durable entry identities are preserved.
- Fixed temporary-file cleanup after successful metadata replacement.
- Fixed Ruff import, formatting, and reconciliation warnings.
- Preserved clean Markdown without visible UUID comments.

### P0 Exit Validation

- Ruff completed with all checks passing.
- Pytest completed with 51 tests passing.
- Git whitespace validation completed without errors.
- Interactive note, task, supporting-detail, `/today`, `/week`, `/search *`, and `/quit` checks passed.
- Metadata sidecars were generated and validated as JSON.
- Repeated metadata synchronization preserved durable UUIDs.
- No abandoned temporary metadata files remained.
- Deleting and rebuilding `index.sqlite3` preserved note content, search results, and durable identity.
- P0 Steps 1 through 8 are complete and validated on Windows with OneDrive.
- Cross-platform validation on macOS and Linux remains pending.
