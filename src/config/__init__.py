"""Prototype defaults, supplied explicitly to the core."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    token_budget: int = 2000
    max_file_bytes: int = 128 * 1024
    max_scan_bytes: int = 8 * 1024 * 1024
    exclude: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("token_budget", "max_file_bytes", "max_scan_bytes"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
