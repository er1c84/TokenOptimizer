# Roadmap

Keep changes small: one feature, tests for that feature, and a short usage update.

## Milestone 1: Working prototype

Complete.

- Repository structure and documentation.
- Read-only project scanner.
- Whole-file selection using an estimated token budget.
- Text/JSON output and raw comparison.
- Sample project and unit/integration tests.

## Milestone 2: Respect .gitignore

Complete.

For Git projects, apply Git's ignore rules while keeping the existing scanner
filters and `--exclude` behavior.

- Root and nested `.gitignore` files, directory patterns, and `!` exceptions.
- Tracked files remain eligible unless another scanner filter excludes them.
- Ignored files and folders have a skip reason in the report.
- Outside a repository or when Git cannot be used, normal filters apply and a warning is reported.
- Tests use temporary repositories; the README includes a usage example.

Uses Git's file listing without adding packages. The existing scanner and budget
tests still apply.

## Later improvements

Take these one at a time; the order can change:

- Save common settings in a local configuration file.
- Add model-specific token counting.
- Select files based on the task.
- Cache repeated work locally.
- Add native Codex and Claude Code adapters and an MCP server.
- Add automatic workflows, then conversation and prompt optimization.

The production language and build system remain undecided. Resolve those before
production packaging or a larger rewrite.
