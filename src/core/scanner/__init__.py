"""Bounded, read-only discovery of local UTF-8 project files."""

from fnmatch import fnmatchcase
import os
from pathlib import Path

from src.config import Settings
from src.core.context import Omission, ProjectFile, ScanResult

GENERATED_DIRECTORIES = frozenset({
    "node_modules", "target", "dist", "build", "__pycache__", "venv",
    "vendor", "coverage", "htmlcov",
})
IGNORED_FILES = frozenset({
    "desktop.ini", "thumbs.db", "package-lock.json", "yarn.lock",
    "pnpm-lock.yaml", "cargo.lock", "poetry.lock", "uv.lock",
})
SENSITIVE_SUFFIXES = frozenset({".pem", ".key", ".p12", ".pfx"})


def _skip_reason(path: Path, relative: str, settings: Settings) -> str | None:
    if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
        return "symbolic link or junction"
    if path.name.startswith("."):
        return "hidden path"
    if any(
        fnmatchcase(relative, pattern) or fnmatchcase(path.name, pattern)
        for pattern in settings.exclude
    ):
        return "user exclusion"
    if path.is_dir() and path.name.casefold() in GENERATED_DIRECTORIES:
        return "generated or dependency directory"
    if path.name.casefold() in IGNORED_FILES:
        return "metadata or generated lockfile"
    if path.suffix.casefold() in SENSITIVE_SUFFIXES:
        return "credential file extension"
    return None


def scan_project(root: Path, settings: Settings) -> ScanResult:
    root = root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(f"Not a project directory: {root}")
    files: list[ProjectFile] = []
    skipped: list[Omission] = []
    bytes_read = 0

    def walk_error(error: OSError) -> None:
        path = Path(error.filename) if error.filename else root
        relative = path.relative_to(root).as_posix()
        skipped.append(Omission(relative, "directory could not be read"))

    for directory, directories, names in os.walk(root, onerror=walk_error, followlinks=False):
        base = Path(directory)
        kept = []
        for name in sorted(directories):
            path = base / name
            relative = path.relative_to(root).as_posix()
            reason = _skip_reason(path, relative, settings)
            if reason:
                skipped.append(Omission(relative + "/", reason))
            else:
                kept.append(name)
        directories[:] = kept

        for name in sorted(names):
            path = base / name
            relative = path.relative_to(root).as_posix()
            reason = _skip_reason(path, relative, settings)
            if reason:
                skipped.append(Omission(relative, reason))
                continue
            try:
                if not path.is_file():
                    skipped.append(Omission(relative, "not a regular file"))
                    continue
                if bytes_read >= settings.max_scan_bytes:
                    skipped.append(Omission(relative, "scan read limit reached"))
                    continue
                read_limit = min(settings.max_file_bytes + 1, settings.max_scan_bytes - bytes_read)
                with path.open("rb") as handle:
                    data = handle.read(read_limit)
                    # stat also detects a partial read at the total scan limit.
                    size = os.fstat(handle.fileno()).st_size
                bytes_read += len(data)
                if size > settings.max_file_bytes or len(data) > settings.max_file_bytes:
                    skipped.append(Omission(relative, "file size limit exceeded"))
                    continue
                if size > len(data):
                    skipped.append(Omission(relative, "scan read limit reached"))
                    continue
                text = data.decode("utf-8")
                if any(ord(char) < 32 and char not in "\t\r\n" for char in text):
                    skipped.append(Omission(relative, "binary or control-character content"))
                    continue
            except UnicodeDecodeError:
                skipped.append(Omission(relative, "not UTF-8 text"))
                continue
            except OSError:
                skipped.append(Omission(relative, "file could not be read"))
                continue
            files.append(ProjectFile(relative, text))

    return ScanResult(tuple(files), tuple(skipped))
