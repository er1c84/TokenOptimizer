"""Rank files by distinct task keywords in their paths and contents."""

from dataclasses import dataclass
import re

from . import ProjectFile

STOP_WORDS = frozenset("""
a an and are as at be by can could do for from how i in into is it me my of on
or our please should that the their this to we what when where which with would
add fix implement update bug issue
""".split())


@dataclass(frozen=True)
class FileRank:
    path: str
    score: int
    path_matches: tuple[str, ...]
    content_matches: tuple[str, ...]


@dataclass(frozen=True)
class TaskSelection:
    task: str
    keywords: tuple[str, ...]
    ranking: tuple[FileRank, ...]
    fallback_reason: str | None = None


def _words(text: str) -> set[str]:
    text = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])|(?<=[a-z0-9])(?=[A-Z])", " ", text)
    return set(re.findall(r"[^\W_]+", text.casefold()))


def task_keywords(task: str) -> tuple[str, ...]:
    if not task.strip():
        raise ValueError("task must not be empty")
    return tuple(sorted(_words(task) - STOP_WORDS))


def rank_file(file: ProjectFile, keywords: tuple[str, ...]) -> FileRank:
    terms = set(keywords)
    if not terms:
        return FileRank(file.path, 0, (), ())
    path_matches = tuple(sorted(terms & _words(file.path)))
    content_matches = tuple(sorted(terms & _words(file.text)))
    return FileRank(file.path, 4 * len(path_matches) + len(content_matches), path_matches, content_matches)
