import json
from datetime import date
from uuid import UUID

import pytest

from AxNotes.metadata import (
    MalformedMetadataError,
    MetadataEntry,
    MetadataFile,
    MetadataNotFoundError,
    UnsupportedMetadataVersionError,
    load_metadata,
    write_metadata,
)

FINGERPRINT = "sha256:v1:" + "a" * 64


def entry_data(**overrides):
    data = {
        "id": "12345678-1234-5678-1234-567812345678",
        "source": "notes/2026-11-04.md",
        "source_date": "2026-11-04",
        "ordinal": 1,
        "fingerprints": {
            "full": FINGERPRINT,
            "content": FINGERPRINT,
            "parent": FINGERPRINT,
            "text": FINGERPRINT,
        },
    }
    data.update(overrides)
    return data


def metadata_json(*entries, schema_version=1):
    return json.dumps({"schema_version": schema_version, "entries": list(entries)})


def test_loads_metadata_entry():
    metadata = MetadataFile.from_json(metadata_json(entry_data()))

    assert metadata.schema_version == 1
    assert metadata.entries[0] == MetadataEntry(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        source="notes/2026-11-04.md",
        source_date=date(2026, 11, 4),
        ordinal=1,
        fingerprints={key: FINGERPRINT for key in ("full", "content", "parent", "text")},
    )


def test_serialization_is_deterministic_and_round_trips():
    metadata = MetadataFile.from_json(metadata_json(entry_data()))

    serialized = metadata.to_json()

    assert serialized.endswith("\n")
    assert serialized == metadata.to_json()
    assert MetadataFile.from_json(serialized) == metadata


def test_rejects_malformed_json():
    with pytest.raises(MalformedMetadataError, match="invalid JSON"):
        MetadataFile.from_json("{")


def test_rejects_unsupported_schema_version():
    with pytest.raises(UnsupportedMetadataVersionError, match="version: 2"):
        MetadataFile.from_json(metadata_json(schema_version=2))


def test_rejects_invalid_uuid():
    with pytest.raises(MalformedMetadataError, match="valid UUID"):
        MetadataFile.from_json(metadata_json(entry_data(id="not-a-uuid")))


@pytest.mark.parametrize(
    "source",
    ["/notes/2026-11-04.md", "../notes.md", "notes/../note.md", r"C:\notes.md", "notes\\x.md"],
)
def test_rejects_non_notebook_relative_source(source):
    with pytest.raises(MalformedMetadataError, match="notebook-relative"):
        MetadataFile.from_json(metadata_json(entry_data(source=source)))


@pytest.mark.parametrize("source_date", ["20261104", "2026-13-01", "not-a-date"])
def test_rejects_non_iso_source_date(source_date):
    with pytest.raises(MalformedMetadataError, match="ISO date"):
        MetadataFile.from_json(metadata_json(entry_data(source_date=source_date)))


@pytest.mark.parametrize("ordinal", [0, -1, 1.5, True])
def test_rejects_non_one_based_integer_ordinal(ordinal):
    with pytest.raises(MalformedMetadataError, match="one-based"):
        MetadataFile.from_json(metadata_json(entry_data(ordinal=ordinal)))


def test_rejects_duplicate_ids():
    second = entry_data(source="notes/2026-11-05.md", source_date="2026-11-05")

    with pytest.raises(MalformedMetadataError, match="ids must be unique"):
        MetadataFile.from_json(metadata_json(entry_data(), second))


def test_rejects_duplicate_ordinals_within_source():
    second = entry_data(id="22345678-1234-5678-1234-567812345678")

    with pytest.raises(MalformedMetadataError, match="ordinals must be unique"):
        MetadataFile.from_json(metadata_json(entry_data(), second))


def test_rejects_invalid_fingerprint_format():
    fingerprints = entry_data()["fingerprints"]
    fingerprints["full"] = "not-a-fingerprint"

    with pytest.raises(MalformedMetadataError, match="sha256:v1"):
        MetadataFile.from_json(metadata_json(entry_data(fingerprints=fingerprints)))


def test_load_metadata_reports_missing_file(tmp_path):
    with pytest.raises(MetadataNotFoundError, match="not found"):
        load_metadata(tmp_path / "missing.json")


def test_load_metadata_reads_valid_file(tmp_path):
    path = tmp_path / "metadata.json"
    path.write_text(metadata_json(entry_data()), encoding="utf-8")

    assert load_metadata(path).entries[0].id == UUID("12345678-1234-5678-1234-567812345678")


def test_load_metadata_reports_invalid_encoding(tmp_path):
    path = tmp_path / "metadata.json"
    path.write_bytes(b"\xff")

    with pytest.raises(MalformedMetadataError, match="UTF-8"):
        load_metadata(path)


def test_write_metadata_replaces_file_atomically(tmp_path):
    path = tmp_path / "metadata.json"
    original = MetadataFile.from_json(metadata_json(entry_data()))
    path.write_text(metadata_json(entry_data(source="notes/2026-11-05.md")), encoding="utf-8")

    write_metadata(path, original)

    assert load_metadata(path) == original
    assert path.read_text(encoding="utf-8") == original.to_json()


def test_write_metadata_preserves_original_when_temp_validation_fails(tmp_path, monkeypatch):
    path = tmp_path / "metadata.json"
    original_text = metadata_json(entry_data())
    path.write_text(original_text, encoding="utf-8")
    original = MetadataFile.from_json(original_text)
    real_from_json = MetadataFile.from_json
    calls = {"count": 0}

    def fake_from_json(content):
        calls["count"] += 1
        if calls["count"] == 2:
            raise MalformedMetadataError("temp validation failed")
        return real_from_json(content)

    monkeypatch.setattr("AxNotes.metadata.MetadataFile.from_json", fake_from_json)

    with pytest.raises(MalformedMetadataError, match="temp validation failed"):
        write_metadata(path, original)

    assert path.read_text(encoding="utf-8") == original_text
