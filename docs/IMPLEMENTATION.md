# P0 Implementation Status

## Step 1: notes-based notebook layout

Implemented.

- `notes/` replaces `daily/` for new notebooks.
- `.AxNotes/metadata/` is created for future durable identity sidecars.
- `projects/` and `templates/` are not created until features require them.
- `AxNotes.toml` declares `notes_directory` and metadata location.
- New note Markdown contains no UUID comments.
- `.AxNotes/index.sqlite3` remains lazy/derived and is not created by `init`.

Next specification step: metadata dataclasses and schema validation.
