# Architecture

The current version uses Python 3.12+ and the standard library. It installs with
pip and builds with setuptools. The long-term production language and tooling
remain open.

## Layout

| Directory | Purpose |
| --- | --- |
| `src/core/scanner/` | Apply Git ignore rules, find eligible files, read UTF-8 text, and record skipped paths. |
| `src/core/context/` | File records, skip reasons, and context formatting. |
| `src/core/optimizer/` | Select whole files within an estimated token budget. |
| `src/core/tokenizer/` | Estimate tokens from UTF-8 size. |
| `src/core/cache/` | Placeholder for local caching. |
| `src/cli/` | Parse arguments and print text or JSON. |
| `src/config/` | Settings and defaults. No config-file loading yet. |
| `src/integrations/codex/` | Placeholder for a Codex adapter. |
| `src/integrations/claude/` | Placeholder for a Claude Code adapter. |
| `src/integrations/mcp/` | Context builder and optional read-only MCP stdio server. |
| `src/integrations/api/` | Placeholder for future API adapters. |
| `tests/unit/` | Scanner, selection, and token estimate checks. |
| `tests/integration/` | CLI and read-only behavior checks. |
| `examples/` | Sample project. |
| `benchmarks/` | Placeholder for performance tests. |
| `docs/` | Requirements, architecture, roadmap, and references. |

Empty directories contain `.gitkeep` so Git can track them.

## How it runs

1. The installed `tokenoptimizer` command, `python -m tokenoptimizer`, or the checkout's `tokenoptimizer.py` calls the CLI.
2. The CLI validates arguments and supplies settings to the scanner.
3. The scanner applies Git ignore rules and its own filters, then returns file contents, skip reasons, and any warnings.
4. The selector orders files and includes each whole file that fits the budget.
5. The CLI prints the context and report.

Without a task, root `README.md`, `AGENTS.md`, and `CLAUDE.md` come first, followed by `src/`
files, then other paths. Each group is sorted by path. A file that does not fit
is skipped; smaller files later in the list can still be included.

Core modules do not import the CLI or assistant integrations. Future adapters
should call the same core functions.

## Task ranking

`core/context/ranking.py` extracts distinct task keywords and matches whole words
in eligible file paths and contents. Matching ignores case, separates snake-case
and camel-case identifiers, and removes common request words. Each matching path
keyword scores four points; each content keyword scores one. Repeated occurrences
do not increase the score. This is a local keyword heuristic, not semantic search.

The selector sorts by descending score, then the existing default order. It still
includes only whole files that fit. Unmatched files remain eligible. Scanner
exclusions and read limits apply before ranking. No keywords or no matches means
the original order is used and a warning is returned.

With `--task`, JSON includes `task_selection`: the task, keywords, all candidate
scores and matching terms, and any fallback reason. Without a task, the JSON
shape is unchanged. Ranking details are outside the context budget. Raw mode
uses the same ranking but includes all eligible files.

## Installation

`pyproject.toml` defines the package, Python requirement, version source, and
command entry point. Setuptools maps `src/` to the installed `tokenoptimizer`
package. Relative imports let the same code run from a checkout or an installed
wheel without moving the source folders.

Setuptools is a build dependency only. The base CLI has no third-party runtime
dependencies; the optional `[mcp]` extra installs the official MCP Python SDK v2
and its dependencies. The wheel includes the MIT license and active Python modules;
tests and placeholder directories are not installed.

`tests/check_install.py` installs a wheel in a fresh temporary environment and
checks the command, module entry point, scanning from another folder, and
uninstalling. Installation does not configure an assistant integration.

## MCP server

`integrations/mcp/context_tool.py` connects the scanner and selector through
`build_context`. `integrations/mcp/server.py` wraps that function in one tool,
`get_project_context(task, budget=4000)`, using the optional MCP SDK.

`create_server(project_root)` resolves and fixes the project directory when the
server is created. Tool calls cannot supply a different path. Scanner exclusions
and read limits still apply. The response contains selected context and compact
counts rather than the complete ranking report. A typed response gives clients
an output schema. Read-only annotations describe the behavior to clients; they
do not replace client permissions.

The installed `tokenoptimizer-mcp` command accepts `--project` and runs over stdio.
The SDK is imported only when a server is created, so base installation and help
remain usable without MCP dependencies. No assistant settings are changed.

MCP tests cover discovery, calls, invalid inputs, ignored files, unchanged project
contents, and an installed subprocess with modern and legacy clients. They skip
when the optional SDK is absent. Run them after installing `.[mcp]`.

Windows SDK dependencies require standard Windows Python. The MSYS2 interpreter
used for the CLI cannot install those wheels. A private, ignored `.mcp-runtime/`
environment is used for local MCP verification; it is not included in packages.

## Git ignore rules

`scanner/gitignore.py` uses `git ls-files --others --ignored --exclude-standard
--directory -z` to list ignored paths. Git handles nested rules, exceptions,
tracked files, and configured exclusions. NUL-separated output preserves spaces
and other characters in filenames. See the [Git documentation](https://git-scm.com/docs/git-ls-files).

The listing is read-only and has a ten-second timeout. Scanner defaults and
explicit exclusions still apply, including to tracked files. Ignored directories
are pruned and reported once, unless tracked files require scanning inside them.
Rules are loaded for the selected working tree; scan nested repositories and
submodules separately.

When Git is unavailable or the listing fails, scanning continues with the usual
filters. The report includes a warning; JSON exposes it in `warnings`, and text
mode prints it on standard error. No packages were added.

## Estimates

Before and after counts include file headers and separators. Both use
`ceil(UTF-8 bytes / 4)`. The baseline contains all eligible files successfully
read during the scan; `--raw` returns that same context without a budget.

The percentage measures estimated context removed by leaving files out. It does
not measure answer quality or billing savings. See the [README](../README.md)
for scanner limits and the [roadmap](roadmap.md) for planned changes.
