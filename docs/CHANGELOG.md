# Changelog

## 0.1.6 Full Working Build
- Restored the interactive writing CLI on top of the new `notes/` storage architecture.
- Restored `/today`, `/week`, `/search`, `/help`, `/reindex`, `/sync`, and `/quit`.
- Added shared entry renderer with aligned top-level markers.
- Kept new Markdown free of UUID comments.
- Indexing now reads only `notes/*.md`.
- Added a clean message instead of a traceback when AxNotes is started outside an initialized notebook.
- Kept `.AxNotes/metadata/` ready for the next durable identity implementation step.
