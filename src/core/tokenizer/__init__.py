"""Dependency-free size heuristic, not a model-specific tokenizer."""

ESTIMATOR = "ceil(UTF-8 bytes / 4); approximate, not a model token count"


def estimate_tokens(text: str) -> int:
    return (len(text.encode("utf-8")) + 3) // 4
