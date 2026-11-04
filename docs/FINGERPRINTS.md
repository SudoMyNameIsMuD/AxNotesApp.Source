# Entry Fingerprints, Version 1

AxNotes fingerprints describe an entry's content for identity matching. They do
not assign UUIDs, reconcile entries, write metadata, or modify Markdown or the
SQLite index.

## Normalization and encoding

Before hashing, normalize each entry's parent text and each supporting detail:

1. Replace CRLF and CR with LF.
2. Normalize Unicode to NFC.
3. Preserve case, punctuation, spelling, internal spaces, and detail order.

For each fingerprint, construct a JSON object with the `algorithm` value
`axnotes-entry-fingerprint`, integer `version` value `1`, and the selected
fields below. Serialize with UTF-8, sorted keys, no insignificant whitespace,
and non-ASCII characters unescaped. The fingerprint is
`sha256:v1:` followed by the lowercase hexadecimal SHA-256 digest.

The object always contains `type`, `task_state`, `text`, and `details`.
Non-applicable fields are represented as `null`, an empty string, or an empty
array as shown:

| Fingerprint | `type` | `task_state` | `text` | `details` |
|---|---|---|---|---|
| `full` | Entry type | Task state or `null` | Parent text | Ordered details |
| `content` | Entry type | `null` | Parent text | Ordered details |
| `parent` | Entry type | `null` | Parent text | `[]` |
| `text` | `""` | `null` | Parent text | `[]` |

## Reference vector

Input entry:

```text
type: task
task_state: open
text: Café<CR>note
details: ["first", "second"]
```

After normalization, the parent text is `Café\nnote`. The expected values are:

```text
full:    sha256:v1:9b1dbe9807288f276eb41a753ecda15cf38b4fac9a011b097342716e476b7cee
content: sha256:v1:33bb39e1f4c46dca3134566fe59e9592e272707c09d4da353384a51986b69f78
parent:  sha256:v1:ec5c9a685371375c1b116e589c8b71fe8698cc92130d96768e40f62ceb8b085f
text:    sha256:v1:73bce4560cdd30482140045b83c5f92d9a6255ef37461f089d411e8c963559bf
```
