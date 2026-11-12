"""Small data contracts and transparent whole-file context formatting."""

from dataclasses import dataclass
import json


@dataclass(frozen=True)
class ProjectFile:
    path: str
    text: str


@dataclass(frozen=True)
class Omission:
    path: str
    reason: str


@dataclass(frozen=True)
class ScanResult:
    files: tuple[ProjectFile, ...]
    skipped: tuple[Omission, ...]
    warnings: tuple[str, ...] = ()


def render_context(files: list[ProjectFile] | tuple[ProjectFile, ...]) -> str:
    # JSON quoting makes filenames containing newlines unambiguous in headers.
    return "\n".join(
        f"--- file: {json.dumps(file.path, ensure_ascii=True)} ---\n{file.text}"
        for file in files
    )
