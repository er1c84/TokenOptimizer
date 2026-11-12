"""Load ignored paths using Git's own rules."""

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class GitIgnore:
    paths: frozenset[str] = frozenset()
    warning: str | None = None

    def ignores(self, relative: str, *, directory: bool = False) -> bool:
        path = relative + "/" if directory else relative
        return "./" in self.paths or path in self.paths


def load_git_ignores(root: Path) -> GitIgnore:
    env = os.environ.copy()
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
        env.pop(name, None)
    try:
        result = subprocess.run(
            ["git", "--no-optional-locks", "-C", str(root), "ls-files",
             "--others", "--ignored", "--exclude-standard", "--directory", "-z", "--", "."],
            capture_output=True, timeout=10, env=env, check=False,
        )
    except FileNotFoundError:
        return GitIgnore(warning="Git is not installed; ignore rules were not applied.")
    except (OSError, subprocess.TimeoutExpired):
        return GitIgnore(warning="Git could not be run; ignore rules were not applied.")
    if result.returncode != 0:
        return GitIgnore(warning="Git ignore rules could not be loaded (outside a repository or Git failed). Scanner filters still apply.")
    paths = frozenset(path.decode("utf-8", errors="surrogateescape") for path in result.stdout.split(b"\0") if path)
    return GitIgnore(paths)
