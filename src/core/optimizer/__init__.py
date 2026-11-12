"""A deliberately simple whole-file budget selector for the working draft."""

from dataclasses import asdict, dataclass
from pathlib import PurePosixPath

from src.core.context import Omission, ProjectFile, ScanResult, render_context
from src.core.tokenizer import ESTIMATOR, estimate_tokens


@dataclass(frozen=True)
class ContextResult:
    context: str
    files_included: tuple[str, ...]
    files_omitted: tuple[Omission, ...]
    files_skipped: tuple[Omission, ...]
    estimated_tokens_before: int
    estimated_tokens_after: int
    token_budget: int | None

    @property
    def estimated_savings_percent(self) -> float:
        before = self.estimated_tokens_before
        return round(100 * (before - self.estimated_tokens_after) / before, 2) if before else 0.0

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "estimated_savings_percent": self.estimated_savings_percent,
            "token_estimator": ESTIMATOR,
        }


def _priority(file: ProjectFile) -> tuple[int, str]:
    path = PurePosixPath(file.path)
    if len(path.parts) == 1 and path.name.casefold() in {"readme.md", "agents.md", "claude.md"}:
        return (0, file.path)
    return (1 if path.parts[0] == "src" else 2, file.path)


def select_context(scan: ScanResult, budget: int | None) -> ContextResult:
    if budget is not None and budget <= 0:
        raise ValueError("budget must be positive")
    ordered = sorted(scan.files, key=_priority)
    selected: list[ProjectFile] = []
    omitted: list[Omission] = []
    output_bytes = 0
    for file in ordered:
        block_bytes = len(render_context([file]).encode("utf-8"))
        candidate_bytes = output_bytes + block_bytes + (1 if selected else 0)
        if budget is None or (candidate_bytes + 3) // 4 <= budget:
            selected.append(file)
            output_bytes = candidate_bytes
        else:
            omitted.append(Omission(file.path, "does not fit estimated token budget"))
    context = render_context(selected)
    return ContextResult(
        context=context,
        files_included=tuple(file.path for file in selected),
        files_omitted=tuple(omitted),
        files_skipped=scan.skipped,
        estimated_tokens_before=estimate_tokens(render_context(ordered)),
        estimated_tokens_after=estimate_tokens(context),
        token_budget=budget,
    )
