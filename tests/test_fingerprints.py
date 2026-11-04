from dataclasses import FrozenInstanceError

import pytest

from AxNotes.fingerprints import FingerprintSet, fingerprint_entry
from AxNotes.models import Entry, EntryType, TaskState


def test_fingerprint_reference_vector():
    entry = Entry(
        EntryType.TASK,
        "Café\rnote",
        TaskState.OPEN,
        ["first", "second"],
    )

    assert fingerprint_entry(entry) == FingerprintSet(
        full="sha256:v1:9b1dbe9807288f276eb41a753ecda15cf38b4fac9a011b097342716e476b7cee",
        content="sha256:v1:33bb39e1f4c46dca3134566fe59e9592e272707c09d4da353384a51986b69f78",
        parent="sha256:v1:ec5c9a685371375c1b116e589c8b71fe8698cc92130d96768e40f62ceb8b085f",
        text="sha256:v1:73bce4560cdd30482140045b83c5f92d9a6255ef37461f089d411e8c963559bf",
    )


def test_fingerprint_set_is_immutable():
    fingerprints = fingerprint_entry(Entry(EntryType.NOTE, "note"))

    with pytest.raises(FrozenInstanceError):
        fingerprints.full = "changed"


def test_content_fingerprint_ignores_task_state():
    open_task = Entry(EntryType.TASK, "Write tests", TaskState.OPEN)
    done_task = Entry(EntryType.TASK, "Write tests", TaskState.DONE)

    open_fingerprints = fingerprint_entry(open_task)
    done_fingerprints = fingerprint_entry(done_task)

    assert open_fingerprints.full != done_fingerprints.full
    assert open_fingerprints.content == done_fingerprints.content
    assert open_fingerprints.parent == done_fingerprints.parent
    assert open_fingerprints.text == done_fingerprints.text


def test_parent_and_text_fingerprints_ignore_details_and_type():
    note = Entry(EntryType.NOTE, "Same text", details=["first"])
    question = Entry(EntryType.QUESTION, "Same text", details=["changed"])

    note_fingerprints = fingerprint_entry(note)
    question_fingerprints = fingerprint_entry(question)

    assert note_fingerprints.full != question_fingerprints.full
    assert note_fingerprints.content != question_fingerprints.content
    assert note_fingerprints.parent != question_fingerprints.parent
    assert note_fingerprints.text == question_fingerprints.text


def test_details_are_ordered_in_full_and_content_fingerprints():
    first = Entry(EntryType.NOTE, "Parent", details=["one", "two"])
    reversed_details = Entry(EntryType.NOTE, "Parent", details=["two", "one"])

    first_fingerprints = fingerprint_entry(first)
    reversed_fingerprints = fingerprint_entry(reversed_details)

    assert first_fingerprints.full != reversed_fingerprints.full
    assert first_fingerprints.content != reversed_fingerprints.content
    assert first_fingerprints.parent == reversed_fingerprints.parent
    assert first_fingerprints.text == reversed_fingerprints.text


def test_normalizes_newlines_and_unicode_to_equivalent_fingerprints():
    composed = Entry(EntryType.NOTE, "Café\nline", details=["résumé"])
    decomposed = Entry(
        EntryType.NOTE,
        "Cafe\u0301\r\nline",
        details=["re\u0301sume\u0301"],
    )

    assert fingerprint_entry(composed) == fingerprint_entry(decomposed)


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("Case", "case"),
        ("word!", "word?"),
        ("one space", "one  space"),
        ("spelling", "speling"),
    ],
)
def test_preserves_case_punctuation_spaces_and_spelling(left, right):
    assert fingerprint_entry(Entry(EntryType.NOTE, left)).text != fingerprint_entry(
        Entry(EntryType.NOTE, right)
    ).text
