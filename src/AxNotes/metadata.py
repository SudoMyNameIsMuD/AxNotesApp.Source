import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any
from uuid import UUID

SCHEMA_VERSION = 1
FINGERPRINT_FIELDS = frozenset({"full", "content", "parent", "text"})
_FINGERPRINT_PATTERN = re.compile(r"sha256:v1:[0-9a-f]{64}\Z")


class MetadataError(Exception):
    """Base class for metadata loading and validation errors."""


class MetadataNotFoundError(MetadataError):
    """Raised when a metadata file does not exist."""


class MalformedMetadataError(MetadataError):
    """Raised when metadata content does not match the supported schema."""


class UnsupportedMetadataVersionError(MetadataError):
    """Raised when metadata uses an unsupported schema version."""


def _validate_source(source: str) -> None:
    if not isinstance(source, str) or not source or "\\" in source:
        raise MalformedMetadataError("Metadata source must be a notebook-relative path.")

    path = PurePosixPath(source)
    windows_path = PureWindowsPath(source)
    if (
        path.is_absolute()
        or windows_path.is_absolute()
        or windows_path.drive
        or source != path.as_posix()
        or any(part in {"", ".", ".."} for part in source.split("/"))
    ):
        raise MalformedMetadataError("Metadata source must be a normalized notebook-relative path.")


def _validate_fingerprints(fingerprints: dict[str, str]) -> None:
    if not isinstance(fingerprints, dict) or set(fingerprints) != FINGERPRINT_FIELDS:
        raise MalformedMetadataError(
            "Metadata fingerprints must contain full, content, parent, and text."
        )
    if any(
        not isinstance(value, str) or not _FINGERPRINT_PATTERN.fullmatch(value)
        for value in fingerprints.values()
    ):
        raise MalformedMetadataError("Metadata fingerprints must use the sha256:v1 format.")


@dataclass(frozen=True, slots=True)
class MetadataEntry:
    id: UUID
    source: str
    source_date: date
    ordinal: int
    fingerprints: dict[str, str]

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise MalformedMetadataError("Metadata entry id must be a UUID.")
        _validate_source(self.source)
        if not isinstance(self.source_date, date):
            raise MalformedMetadataError("Metadata source_date must be a date.")
        if type(self.ordinal) is not int or self.ordinal < 1:
            raise MalformedMetadataError("Metadata ordinal must be a one-based integer.")
        _validate_fingerprints(self.fingerprints)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MetadataEntry":
        expected_fields = {"id", "source", "source_date", "ordinal", "fingerprints"}
        if not isinstance(data, dict) or set(data) != expected_fields:
            raise MalformedMetadataError("Metadata entry has missing or unknown fields.")

        try:
            entry_id = UUID(data["id"])
        except (AttributeError, TypeError, ValueError) as error:
            raise MalformedMetadataError("Metadata entry id must be a valid UUID.") from error

        source_date_value = data["source_date"]
        if not isinstance(source_date_value, str):
            raise MalformedMetadataError("Metadata source_date must be an ISO date.")
        try:
            source_date = date.fromisoformat(source_date_value)
        except ValueError as error:
            raise MalformedMetadataError(
                "Metadata source_date must be an ISO date in YYYY-MM-DD format."
            ) from error
        if source_date.isoformat() != source_date_value:
            raise MalformedMetadataError(
                "Metadata source_date must be an ISO date in YYYY-MM-DD format."
            )

        return cls(
            id=entry_id,
            source=data["source"],
            source_date=source_date,
            ordinal=data["ordinal"],
            fingerprints=data["fingerprints"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "source": self.source,
            "source_date": self.source_date.isoformat(),
            "ordinal": self.ordinal,
            "fingerprints": dict(self.fingerprints),
        }


@dataclass(frozen=True, slots=True)
class MetadataFile:
    schema_version: int
    entries: tuple[MetadataEntry, ...]

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int:
            raise MalformedMetadataError("Metadata schema_version must be an integer.")
        if self.schema_version != SCHEMA_VERSION:
            raise UnsupportedMetadataVersionError(
                f"Unsupported metadata schema version: {self.schema_version}."
            )
        if not isinstance(self.entries, tuple) or any(
            not isinstance(entry, MetadataEntry) for entry in self.entries
        ):
            raise MalformedMetadataError("Metadata entries must be a tuple of MetadataEntry values.")

        ids = [entry.id for entry in self.entries]
        if len(ids) != len(set(ids)):
            raise MalformedMetadataError("Metadata entry ids must be unique.")

        ordinals = [(entry.source, entry.ordinal) for entry in self.entries]
        if len(ordinals) != len(set(ordinals)):
            raise MalformedMetadataError("Metadata ordinals must be unique within each source.")

    @classmethod
    def from_json(cls, content: str) -> "MetadataFile":
        try:
            data = json.loads(content)
        except json.JSONDecodeError as error:
            raise MalformedMetadataError("Metadata file contains invalid JSON.") from error
        if not isinstance(data, dict) or set(data) != {"schema_version", "entries"}:
            raise MalformedMetadataError("Metadata file has missing or unknown fields.")
        if type(data["schema_version"]) is not int:
            raise MalformedMetadataError("Metadata schema_version must be an integer.")
        if data["schema_version"] != SCHEMA_VERSION:
            raise UnsupportedMetadataVersionError(
                f"Unsupported metadata schema version: {data['schema_version']}."
            )
        if not isinstance(data["entries"], list):
            raise MalformedMetadataError("Metadata entries must be a JSON array.")

        return cls(
            schema_version=data["schema_version"],
            entries=tuple(MetadataEntry.from_dict(entry) for entry in data["entries"]),
        )

    def to_json(self) -> str:
        data = {
            "schema_version": self.schema_version,
            "entries": [entry.to_dict() for entry in self.entries],
        }
        return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def load_metadata(path: str | Path) -> MetadataFile:
    try:
        content = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise MetadataNotFoundError(f"Metadata file not found: {path}") from error
    except UnicodeDecodeError as error:
        raise MalformedMetadataError("Metadata file is not valid UTF-8.") from error
    return MetadataFile.from_json(content)
