import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG = '''[notebook]
version = "0.1"
notes_directory = "notes"
date_format = "%Y-%m-%d"

[metadata]
directory = ".AxNotes/metadata"

[display]
heading_format = "%A | %d%b%y"
'''


@dataclass(frozen=True, slots=True)
class Config:
    root: Path
    format: str = "daily-files"
    notes_directory: str = "notes"
    metadata_directory: str = ".AxNotes/metadata"
    date_format: str = "%Y-%m-%d"
    heading_format: str = "%A | %d%b%y"

    @classmethod
    def load(cls, root: Path) -> "Config":
        path = root / "AxNotes.toml"
        if not path.exists():
            return cls(root)
        with path.open("rb") as stream:
            data = tomllib.load(stream)
        notebook = data.get("notebook", {})
        metadata = data.get("metadata", {})
        display = data.get("display", {})
        return cls(
            root=root,
            format=str(notebook.get("format", "daily-files")),
            notes_directory=str(notebook.get("notes_directory", "notes")),
            metadata_directory=str(metadata.get("directory", ".AxNotes/metadata")),
            date_format=str(notebook.get("date_format", "%Y-%m-%d")),
            heading_format=str(display.get("heading_format", "%A | %d%b%y")),
        )
