# Reconciliation, Step 4

This module provides a pure in-memory reconciliation pass for matching prior and current entry sequences without mutating Markdown, metadata, or SQLite.

## Matching order

The implementation follows the Step 4 safety model:

1. Unique `full` fingerprint: exact match.
2. Unique `content` fingerprint: task-state change.
3. Unique `parent` fingerprint: supporting-detail change.
4. Unique `text` fingerprint: compatible type transition.
5. Single remaining change bounded by existing matched neighbors.
6. Otherwise, create a new identity and emit a diagnostic.

The final safety rule is to prefer a fresh UUID over attaching an existing identity to an ambiguous entry.

## API

```python
from AxNotes.reconcile import reconcile

result = reconcile(old_entries, new_entries)
```

`ReconciliationResult.matches` contains the per-entry mapping, and `diagnostics` records newly created identities for ambiguous entries.
