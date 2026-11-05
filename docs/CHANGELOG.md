# Changelog

## Unreleased

- Standardized v0.2 terminology for entries, quick-entry notation, Markdown markers, rendered markers, supporting details, metadata sidecars, and the derived index.
- Clarified the README's current quick-entry notation and completed P0 architecture status.
- Added explicit `AxNotes migrate single-file` migration with retained source and metadata/configuration backups, durable identity preservation, rollback, and a rebuildable single-file index.
- Added atomic Markdown writing and date-aware loading, appending, and rendering for migrated single-file notebooks.
- Synchronize metadata and the derived index after supporting-detail capture.
- Completed quick-entry normalization for all task states and entry types, preserving natural sentence-ending question marks and rejecting empty markers.
- Redraw the remembered `/today` or `/week` view after every successful entry capture.

## 0.1.6 Full Working Build
- Restored the interactive writing CLI on top of the new `notes/` storage architecture.
- Restored `/today`, `/week`, `/search`, `/help`, `/reindex`, `/sync`, and `/quit`.
- Added a shared renderer with aligned rendered markers for top-level entries.
- Kept new authoritative Markdown free of visible UUID comments.
- Indexing now reads only `notes/*.md`.
- Added a clean message instead of a traceback when AxNotes is started outside an initialized notebook.
- Kept `.AxNotes/metadata/` ready for durable identity sidecars.

## 0.1.7 - 04 Nov 2026
Added durable entry identities in metadata sidecars under `.AxNotes/metadata/`.
Added deterministic entry fingerprints and conservative durable-identity reconciliation.
Added atomic metadata-sidecar writes with temporary-file validation and replacement.
Added automatic metadata and derived-index synchronization.
Preserved clean, human-readable authoritative Markdown without visible UUID comments.
Fixed the renderer to use the correct `entry.entry_type` model field.
Expanded metadata-sidecar, fingerprint, reconciliation, and persistence tests.
Verified with Ruff, 50 passing tests, valid generated JSON metadata sidecars, and interactive smoke testing.

## 0.1.8 - 04 Nov 2026

### Added

- Added durable entry identities using validated metadata sidecars under `.AxNotes/metadata/`.
- Added deterministic full, content, parent, and text fingerprints.
- Added conservative identity reconciliation for task-state, detail, type, order, and content changes.
- Added atomic metadata persistence with temporary-file validation and replacement.
- Added automatic metadata synchronization for Markdown files in `notes/`.
- Added metadata-aware derived-indexing with entry UUIDs from durable metadata sidecars.
- Added derived-index rebuilding from authoritative Markdown and metadata sidecars.

### Improved

- Kept authoritative Markdown as the canonical source for entry text, entry type, task state, supporting details, and order.
- Kept the derived index disposable and rebuildable.
- Updated metadata sidecars to mirror their authoritative Markdown source paths.
- Improved handling of missing metadata without hiding malformed or invalid sidecars.
- Expanded automated coverage to 51 passing tests.
- Updated the roadmap, README, and release documentation for the completed P0 foundation.

### Fixed

- Fixed the renderer to use the `entry.entry_type` model contract.
- Fixed metadata-sidecar and derived-index synchronization.
- Fixed derived-index rebuilding so durable entry identities are preserved.
- Fixed temporary-file cleanup after successful metadata replacement.
- Fixed Ruff import, formatting, and reconciliation warnings.
- Preserved clean authoritative Markdown without visible UUID comments.

### P0 Exit Validation

- Ruff completed with all checks passing.
- Pytest completed with 51 tests passing.
- Git whitespace validation completed without errors.
- Interactive normal note, open task, supporting detail, `/today`, `/week`, `/search *`, and `/quit` checks passed.
- Metadata sidecars were generated and validated as JSON.
- Repeated metadata synchronization preserved durable UUIDs.
- No abandoned temporary metadata sidecars remained.
- Deleting and rebuilding `index.sqlite3` preserved note content, search results, and durable identity.
- P0 Steps 1 through 8 are complete and validated on Windows with OneDrive.
- Cross-platform validation on macOS and Linux remains pending.
