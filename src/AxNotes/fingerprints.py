import hashlib
import json
import unicodedata
from dataclasses import dataclass

from .models import Entry

FINGERPRINT_VERSION = 1
_FINGERPRINT_PREFIX = f"sha256:v{FINGERPRINT_VERSION}:"
_ALGORITHM = "axnotes-entry-fingerprint"


@dataclass(frozen=True, slots=True)
class FingerprintSet:
    full: str
    content: str
    parent: str
    text: str


def _normalize(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    return unicodedata.normalize("NFC", value)


def _fingerprint(entry_type: str, task_state: str | None, text: str, details: list[str]) -> str:
    payload = {
        "algorithm": _ALGORITHM,
        "version": FINGERPRINT_VERSION,
        "type": entry_type,
        "task_state": task_state,
        "text": text,
        "details": details,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _FINGERPRINT_PREFIX + hashlib.sha256(encoded).hexdigest()


def fingerprint_entry(entry: Entry) -> FingerprintSet:
    """Create versioned fingerprints for the identity-relevant parts of an entry."""
    entry_type = entry.entry_type.value
    task_state = entry.task_state.value if entry.task_state is not None else None
    text = _normalize(entry.text)
    details = [_normalize(detail) for detail in entry.details]

    return FingerprintSet(
        full=_fingerprint(entry_type, task_state, text, details),
        content=_fingerprint(entry_type, None, text, details),
        parent=_fingerprint(entry_type, None, text, []),
        text=_fingerprint("", None, text, []),
    )
