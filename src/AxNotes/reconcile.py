from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from .fingerprints import FingerprintSet, fingerprint_entry
from .models import Entry


class ReconciliationError(ValueError):
    """Raised when reconciliation input cannot be matched or normalized."""


@dataclass(frozen=True, slots=True)
class ReconciliationMatch:
    new_index: int
    old_index: int | None
    reason: str
    preserved: bool
    old_identity: UUID | str | None = None
    new_identity: UUID | str | None = None


@dataclass(frozen=True, slots=True)
class ReconciliationDiagnostic:
    new_index: int
    reason: str
    message: str


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    matches: tuple[ReconciliationMatch, ...]
    diagnostics: tuple[ReconciliationDiagnostic, ...] = ()

    @property
    def matched_new_entries(self) -> tuple[int, ...]:
        return tuple(match.new_index for match in self.matches)

    @property
    def new_identities(self) -> tuple[UUID | str | None, ...]:
        return tuple(match.new_identity for match in self.matches)

    def as_mapping(self) -> dict[int, ReconciliationMatch]:
        return {match.new_index: match for match in self.matches}


@dataclass(frozen=True, slots=True)
class _NormalizedEntry:
    source: Any
    id_: UUID | str | None
    type_: str
    task_state: str | None
    text: str
    details: tuple[str, ...]
    full: str
    content: str
    parent: str
    text_fingerprint: str


def _normalized_fingerprints(entry: Any) -> FingerprintSet:
    if isinstance(entry, dict):
        if "fingerprints" in entry:
            fingerprints = entry["fingerprints"]
            return FingerprintSet(
                full=fingerprints["full"],
                content=fingerprints["content"],
                parent=fingerprints["parent"],
                text=fingerprints["text"],
            )
        raise ReconciliationError("Dictionary entries must include fingerprints for reconciliation.")
    if isinstance(entry, Entry):
        return fingerprint_entry(entry)
    if hasattr(entry, "fingerprints"):
        fingerprints = entry.fingerprints
        if isinstance(fingerprints, dict):
            return FingerprintSet(
                full=fingerprints["full"],
                content=fingerprints["content"],
                parent=fingerprints["parent"],
                text=fingerprints["text"],
            )
    if hasattr(entry, "entry_type") and hasattr(entry, "text"):
        return fingerprint_entry(entry)
    raise ReconciliationError(f"Unsupported entry type for reconciliation: {type(entry)!r}")


def _entry_id(entry: Any) -> UUID | str | None:
    if isinstance(entry, dict):
        return entry.get("id")
    return getattr(entry, "id", None)


def _normalize_entry(entry: Any) -> _NormalizedEntry:
    if isinstance(entry, dict): # noqa: SIM102
        if "entry_type" in entry and "text" in entry:
            parsed = Entry(
                entry_type=entry["entry_type"],
                text=entry["text"],
                task_state=entry.get("task_state"),
                details=list(entry.get("details", [])),
            )
            fingerprints = fingerprint_entry(parsed)
            raw_type = (
                parsed.entry_type.value
                if hasattr(parsed.entry_type, "value")
                else str(parsed.entry_type)
            )
            raw_task = (
                parsed.task_state.value
                if parsed.task_state is not None and hasattr(parsed.task_state, "value")
                else parsed.task_state
            )
            return _NormalizedEntry(
                source=entry,
                id_=_entry_id(entry),
                type_=raw_type,
                task_state=raw_task,
                text=parsed.text,
                details=tuple(parsed.details),
                full=fingerprints.full,
                content=fingerprints.content,
                parent=fingerprints.parent,
                text_fingerprint=fingerprints.text,
            )

    if isinstance(entry, Entry):
        fingerprints = fingerprint_entry(entry)
        return _NormalizedEntry(
            source=entry,
            id_=_entry_id(entry),
            type_=(
                entry.entry_type.value
                if hasattr(entry.entry_type, "value")
                else str(entry.entry_type)
            ),
            task_state=(
                entry.task_state.value
                if entry.task_state is not None and hasattr(entry.task_state, "value")
                else entry.task_state
            ),
            text=entry.text,
            details=tuple(entry.details),
            full=fingerprints.full,
            content=fingerprints.content,
            parent=fingerprints.parent,
            text_fingerprint=fingerprints.text,
        )

    fingerprints = _normalized_fingerprints(entry)
    entry_type = getattr(entry, "entry_type", None)
    if hasattr(entry_type, "value"):
        entry_type_name = entry_type.value
    else:
        entry_type_name = str(entry_type) if entry_type is not None else ""

    task_state = getattr(entry, "task_state", None)
    if task_state is not None and hasattr(task_state, "value"):
        task_state = task_state.value

    text = getattr(entry, "text", "")
    details = tuple(getattr(entry, "details", ()))
    return _NormalizedEntry(
        source=entry,
        id_=_entry_id(entry),
        type_=entry_type_name,
        task_state=task_state,
        text=text,
        details=details,
        full=fingerprints.full,
        content=fingerprints.content,
        parent=fingerprints.parent,
        text_fingerprint=fingerprints.text,
    )


def _unique_index(fingerprint_map: dict[str, list[int]], key: str) -> int | None:
    matches = fingerprint_map.get(key)
    if not matches:
        return None
    if len(matches) != 1:
        return None
    return matches[0]


def _candidate_for_new_entry(
    new_index: int,
    entry: _NormalizedEntry,
    old: tuple[_NormalizedEntry, ...],
    old_by_full: dict[str, list[int]],
    old_by_content: dict[str, list[int]],
    old_by_parent: dict[str, list[int]],
    old_by_text: dict[str, list[int]],
    used_old: set[int],
) -> tuple[int | None, str, str | None]:
    exact_match = _unique_index(old_by_full, entry.full)
    if exact_match is not None and exact_match not in used_old:
        return exact_match, "exact_match", None

    content_match = _unique_index(old_by_content, entry.content)
    if content_match is not None and content_match not in used_old:
        return content_match, "task_state_change", None

    parent_match = _unique_index(old_by_parent, entry.parent)
    if parent_match is not None and parent_match not in used_old:
        return parent_match, "supporting_detail_change", None

    text_match = _unique_index(old_by_text, entry.text_fingerprint)
    if text_match is not None and text_match not in used_old:
        return text_match, "type_transition", None

    unmatched_old = [index for index in range(len(old)) if index not in used_old]
    if not unmatched_old:
        return None, "new_identity", None

    if len(old) > 1 and len(unmatched_old) == 1:
        candidate = unmatched_old[0]
        return candidate, "neighbor_match", None

    neighbor_candidates = [index for index in unmatched_old if abs(index - new_index) <= 1]
    if len(old) > 1 and len(neighbor_candidates) == 1:
        return neighbor_candidates[0], "neighbor_match", None
    if len(neighbor_candidates) > 1:
        return None, "new_identity", "ambiguous_identity"
    return None, "new_identity", "new_identity"


def reconcile(old_entries: Iterable[Any], new_entries: Iterable[Any]) -> ReconciliationResult:
    """Match new entries to old entries using the stable fingerprint passes from Step 4.

    The matching order is exact, task-state, supporting detail, compatible type transition,
    then a bounded-neighbor pass. Any remaining entries are treated as new identities rather
    than reusing ambiguous or missing UUIDs.
    """
    old = tuple(_normalize_entry(entry) for entry in old_entries)
    new = tuple(_normalize_entry(entry) for entry in new_entries)

    old_by_full: dict[str, list[int]] = {}
    old_by_content: dict[str, list[int]] = {}
    old_by_parent: dict[str, list[int]] = {}
    old_by_text: dict[str, list[int]] = {}
    for index, entry in enumerate(old):
        old_by_full.setdefault(entry.full, []).append(index)
        old_by_content.setdefault(entry.content, []).append(index)
        old_by_parent.setdefault(entry.parent, []).append(index)
        old_by_text.setdefault(entry.text_fingerprint, []).append(index)

    used_old: set[int] = set()
    matches: list[ReconciliationMatch] = []
    diagnostics: list[ReconciliationDiagnostic] = []

    for new_index, entry in enumerate(new):
        candidate, reason, diagnostic_reason = _candidate_for_new_entry(
            new_index,
            entry,
            old,
            old_by_full,
            old_by_content,
            old_by_parent,
            old_by_text,
            used_old,
        )

        if candidate is None:
            new_uuid = uuid4()
            diag_reason = diagnostic_reason or "new_identity"
            diagnostics.append(
                ReconciliationDiagnostic(
                    new_index=new_index,
                    reason=diag_reason,
                    message=(
                        "Identity was ambiguous; created a new UUID."
                        if diag_reason == "ambiguous_identity"
                        else "Identity was absent; created a new UUID."
                    ),
                )
            )
            matches.append(
                ReconciliationMatch(
                    new_index=new_index,
                    old_index=None,
                    reason="new_identity",
                    preserved=False,
                    old_identity=None,
                    new_identity=new_uuid,
                )
            )
            continue

        old_entry = old[candidate]
        new_identity = old_entry.id_ if old_entry.id_ is not None else uuid4()
        matches.append(
            ReconciliationMatch(
                new_index=new_index,
                old_index=candidate,
                reason=reason,
                preserved=(reason in {"exact_match", "task_state_change", "supporting_detail_change", "type_transition", "neighbor_match"}),
                old_identity=old_entry.id_,
                new_identity=new_identity,
            )
        )
        used_old.add(candidate)

    return ReconciliationResult(matches=tuple(matches), diagnostics=tuple(diagnostics))


match_entries = reconcile
reconcile_entries = reconcile


__all__ = [
    "ReconciliationDiagnostic",
    "ReconciliationError",
    "ReconciliationMatch",
    "ReconciliationResult",
    "match_entries",
    "reconcile",
    "reconcile_entries",
]
