# Architecture

The prototype uses Python 3.12+ and the standard library. The production language,
build system, and packaging are still undecided.

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
| `src/integrations/mcp/` | Placeholder for an MCP server. |
| `src/integrations/api/` | Placeholder for future API adapters. |
| `tests/unit/` | Scanner, selection, and token estimate checks. |
| `tests/integration/` | CLI and read-only behavior checks. |
| `examples/` | Sample project. |
| `benchmarks/` | Placeholder for performance tests. |
| `docs/` | Requirements, architecture, roadmap, and references. |

Empty directories contain `.gitkeep` so Git can track them.

## How it runs

1. `tokenoptimizer.py` calls the CLI.
2. The CLI validates arguments and supplies settings to the scanner.
3. The scanner applies Git ignore rules and its own filters, then returns file contents, skip reasons, and any warnings.
4. The selector orders files and includes each whole file that fits the budget.
5. The CLI prints the context and report.

Root `README.md`, `AGENTS.md`, and `CLAUDE.md` come first, followed by `src/`
files, then other paths. Each group is sorted by path. A file that does not fit
is skipped; smaller files later in the list can still be included.

Core modules do not import the CLI or assistant integrations. Future adapters
should call the same core functions.

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
