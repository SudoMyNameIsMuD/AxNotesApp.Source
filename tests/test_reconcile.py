from uuid import UUID, uuid4

from AxNotes.models import Entry, EntryType, TaskState
from AxNotes.reconcile import ReconciliationResult, reconcile


def test_reconcile_exact_match_preserves_existing_identity():
    old_identity = uuid4()
    prior = {"id": old_identity, "entry_type": EntryType.NOTE, "text": "hello"}
    current = {"entry_type": EntryType.NOTE, "text": "hello"}

    result = reconcile([prior], [current])

    assert result.matches[0].old_index == 0
    assert result.matches[0].new_index == 0
    assert result.matches[0].reason == "exact_match"
    assert result.matches[0].old_identity == old_identity
    assert result.matches[0].new_identity == old_identity
    assert result.matches[0].preserved is True


def test_reconcile_task_state_change_keeps_same_identity():
    old_identity = uuid4()
    prior = {"id": old_identity, "entry_type": EntryType.TASK, "text": "Write tests", "task_state": TaskState.OPEN}
    current = {"entry_type": EntryType.TASK, "text": "Write tests", "task_state": TaskState.DONE}

    result = reconcile([prior], [current])

    assert result.matches[0].reason == "task_state_change"
    assert result.matches[0].new_identity == old_identity


def test_reconcile_new_identity_when_no_match_exists():
    previous = [Entry(EntryType.NOTE, "keep")]
    current = [Entry(EntryType.NOTE, "new note")]

    result = reconcile(previous, current)

    assert result.matches[0].old_index is None
    assert result.matches[0].reason == "new_identity"
    assert result.diagnostics[0].reason == "new_identity"
    assert isinstance(result.matches[0].new_identity, UUID)


def test_reconcile_reorders_with_same_identity_pairs():
    first_id = uuid4()
    second_id = uuid4()
    previous = [
        {"id": first_id, "entry_type": EntryType.NOTE, "text": "first"},
        {"id": second_id, "entry_type": EntryType.NOTE, "text": "second"},
    ]
    current = [
        {"entry_type": EntryType.NOTE, "text": "second"},
        {"entry_type": EntryType.NOTE, "text": "first"},
    ]

    result = reconcile(previous, current)

    assert [match.old_index for match in result.matches] == [1, 0]
    assert result.matches[0].new_identity == second_id
    assert result.matches[1].new_identity == first_id


def test_reconcile_does_not_reuse_identity_for_ambiguous_duplicate_content():
    first = {"id": uuid4(), "entry_type": EntryType.NOTE, "text": "duplicate"}
    second = {"id": uuid4(), "entry_type": EntryType.NOTE, "text": "duplicate"}
    current = [{"entry_type": EntryType.NOTE, "text": "duplicate"}]

    result = reconcile([first, second], current)

    assert result.matches[0].old_index is None
    assert result.matches[0].reason == "new_identity"
    assert result.diagnostics[0].reason == "ambiguous_identity"
    assert result.matches[0].new_identity != first["id"]
    assert result.matches[0].new_identity != second["id"]


def test_reconcile_preserves_identity_across_task_state_and_detail_changes():
    identity = uuid4()
    previous = [{
        "id": identity,
        "entry_type": EntryType.TASK,
        "text": "Write docs",
        "task_state": TaskState.OPEN,
        "details": ["draft"],
    }]
    current = [{
        "entry_type": EntryType.TASK,
        "text": "Write docs",
        "task_state": TaskState.DONE,
        "details": ["revised"],
    }]

    result = reconcile(previous, current)

    assert result.matches[0].old_index == 0
    assert result.matches[0].new_identity == identity
    assert result.matches[0].reason in {"task_state_change", "supporting_detail_change"}
