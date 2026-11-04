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