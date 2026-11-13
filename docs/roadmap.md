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

## Milestone 3: Installable command

Complete for the current Python version.

- Install from a checkout with `python -m pip install .`.
- Run `tokenoptimizer` from any project folder, or use `python -m tokenoptimizer`.
- Check the version with `--version`.
- Keep the original checkout command working.
- Build a wheel and check installation, scanning, and uninstalling in a clean environment.

This uses setuptools for packaging and adds no runtime dependencies. It does not
install assistant hooks or enable automatic optimization.

## Later improvements

Take these one at a time; the order can change:

- Save common settings in a local configuration file.
- Add model-specific token counting.
- Select files based on the task.
- Cache repeated work locally.
- Add native Codex and Claude Code adapters and an MCP server.
- Add automatic workflows, then conversation and prompt optimization.

The current Python version has pip/setuptools packaging. The production language,
long-term tooling, and standalone installers remain open decisions.
