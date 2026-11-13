"""Command-line interface."""

import argparse
import json
from pathlib import Path
import sys

from .. import __version__
from ..config import Settings
from ..core.optimizer import select_context
from ..core.scanner import scan_project


def _positive_integer(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tokenoptimizer", description="Prepare local project context.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    context = commands.add_parser("context", help="select whole UTF-8 files within an estimated budget")
    context.add_argument("path", nargs="?", type=Path, default=Path("."))
    context.add_argument("--budget", type=_positive_integer, default=2000, help="estimated token budget (default: 2000)")
    context.add_argument("--exclude", action="append", default=[], help="exclude a relative path or filename glob; repeatable")
    context.add_argument("--raw", action="store_true", help="include all eligible files without applying a budget")
    context.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    settings = Settings(token_budget=args.budget, exclude=tuple(args.exclude))
    try:
        result = select_context(scan_project(args.path, settings), None if args.raw else settings.token_budget)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=True))
    else:
        for warning in result.warnings:
            print(f"Warning: {warning}", file=sys.stderr)
        sys.stdout.write(result.context)
        eligible = len(result.files_included) + len(result.files_omitted)
        print(
            f"Context: {len(result.files_included)}/{eligible} eligible files; "
            f"estimated tokens: {result.estimated_tokens_before} -> {result.estimated_tokens_after} "
            f"({result.estimated_savings_percent}% reduction). "
            f"Skipped: {len(result.files_skipped)}. Counts use UTF-8 bytes / 4, not a model tokenizer.",
            file=sys.stderr,
        )
        if result.files_omitted or result.files_skipped:
            print("Use --format json for inclusion/omission details; --raw bypasses the budget only.", file=sys.stderr)
    return 0
