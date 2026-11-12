# TokenOptimizer
A lightweight, local tool designed to reduce AI token usage across coding assistants and AI-powered applications.

## Status

The first version is a manual tool for preparing project context. It reads local
files, selects whole files within an estimated token budget, and reports what
was included or skipped. It leaves the original files alone.

Requires Python 3.12+. No packages to install. The production language and build
system are still undecided.

## Usage

Run from the repository folder:

```console
python tokenoptimizer.py context examples/sample_project --budget 100
```

The sample includes the README and source file and leaves out the notes.

Point it at another project:

```console
python tokenoptimizer.py context "C:/Projects/MyApp" --budget 4000
```

Options:

- `--format json`: include file lists, skip reasons, and size estimates.
- `--exclude "*.log"`: exclude a filename or relative-path pattern. Repeat for more patterns; use `/` for path separators. Matching is case-sensitive.
- `--raw`: include all eligible files without applying the token budget.

Text mode prints context to standard output and the summary to standard error.
In JSON mode, the budget applies to the `context` field, not the entire report.
Nothing is sent to an assistant automatically.

## Git ignore rules

In a Git project, the scanner uses Git's ignore rules, including nested
`.gitignore` files, `!` exceptions, `.git/info/exclude`, and configured global
exclusions. Tracked files stay eligible, but scanner defaults and `--exclude`
still take precedence.

For example, if `.gitignore` contains `logs/`, an untracked `logs/` folder is
listed in the JSON `files_skipped` report with the reason `ignored by Git`:

```console
python tokenoptimizer.py context "C:/Projects/MyApp" --format json
```

Outside a Git repository, or if Git is missing or fails, the scanner uses its
normal filters. Text mode reports a warning on standard error; JSON mode includes
it in `warnings`. Ignore rules are not applied in that case. Scan nested
repositories and submodules separately to use their own ignore rules.

## Current limits

- Token counts are estimates: `ceil(UTF-8 bytes / 4)`.
- Root README and assistant instruction files come first, then `src/`, then other paths. Selection does not account for the task yet.
- Files are included whole or omitted. A small budget can produce empty context.
- Hidden paths, common dependency/build folders, generated lockfiles, OS metadata, credential-file extensions, links, binary/non-UTF-8 files, and large files are skipped. See [scanner defaults](src/core/scanner/__init__.py) for the lists. This is not secret detection.
- Reads are capped at 128 KiB per file and 8 MiB per scan.
- `--raw` still uses Git ignore rules, scanner exclusions, and read limits.

## Tests

```console
python -m unittest discover -s tests -v
```

Tested on Windows with Python 3.12. Other platforms still need testing.

## Layout

- `src/core/`: scanning, context selection, token estimates, and future caching.
- `src/cli/`: command-line arguments and output.
- `src/config/`: settings and defaults.
- `src/integrations/`: placeholders for Codex, Claude Code, MCP, and API adapters.
- `tests/`: unit and integration tests.
- `examples/`: sample project.
- `benchmarks/`: reserved for performance tests.
- `docs/`: [architecture](docs/architecture.md), [requirements](docs/requirements.md), [roadmap](docs/roadmap.md), and [RTK notes](docs/rtk-design-notes.md).

## License

[MIT](LICENSE).
