"""Serve project context over MCP stdio."""

import argparse
from pathlib import Path
from typing import TypedDict

from .context_tool import build_context


class ContextReply(TypedDict):
    context: str
    estimated_tokens: int
    token_budget: int
    included_file_count: int
    omitted_file_count: int
    skipped_file_count: int
    warnings: list[str]


def create_server(project_root: str | Path):
    root = Path(project_root).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(f"Not a project directory: {root}")

    # Keep the SDK optional for the command-line tool and its help commands.
    from mcp.server import MCPServer
    from mcp.types import ToolAnnotations

    server = MCPServer(
        "TokenOptimizer",
        instructions=(
            "Use get_project_context for a task-focused overview of the configured project. "
            "Selection uses keyword matches and can omit relevant files. "
            "Read additional project files whenever needed. Token counts are estimates."
        ),
    )

    @server.tool(
        annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False)
    )
    def get_project_context(task: str, budget: int = 4000) -> ContextReply:
        """Select whole project files for a task within an estimated token budget."""
        result = build_context(root, task, budget)
        return {
            "context": result.context,
            "estimated_tokens": result.estimated_tokens_after,
            "token_budget": budget,
            "included_file_count": len(result.files_included),
            "omitted_file_count": len(result.files_omitted),
            "skipped_file_count": len(result.files_skipped),
            "warnings": list(result.warnings),
        }

    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tokenoptimizer-mcp", description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="project folder to scan (default: current folder)")
    args = parser.parse_args(argv)
    try:
        server = create_server(args.project)
    except ModuleNotFoundError as error:
        parser.exit(2, f"MCP dependency unavailable: {error.name}. Install TokenOptimizer with the [mcp] extra in this Python environment.\n")
    except OSError as error:
        parser.error(str(error))
    server.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
