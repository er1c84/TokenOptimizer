# TokenOptimizer
A lightweight, local tool designed to reduce AI token usage across coding assistants and AI-powered applications.

## Status

The first version is a manual tool for preparing project context. It reads local
files, selects whole files within an estimated token budget, and reports what
was included or skipped. It leaves the original files alone.

Requires Python 3.12+. There are no third-party runtime packages. Git is needed
to apply ignore rules.

## Install

From the repository folder:

```console
python -m pip install .
```

If Python reports that pip is missing, run `python -m ensurepip --upgrade` first.
Installing from source may download setuptools to build the package; running the
tool is offline.

After installation, run this from any project folder:

```console
tokenoptimizer context . --budget 4000
```

If the short command is not on your PATH, use
`python -m tokenoptimizer context . --budget 4000` with the same Python used to
install it.

Check the installed version with `tokenoptimizer --version`. To install local
updates, run `python -m pip install --upgrade .` from the repository folder.
To remove it, run `python -m pip uninstall TokenOptimizer`.

## Usage

Try the sample from the repository folder, without installing:

```console
python tokenoptimizer.py context examples/sample_project --budget 100
```

The sample includes the README and source file and leaves out the notes.

Once installed, point it at another project:

```console
tokenoptimizer context "C:/Projects/MyApp" --budget 4000
```

Options:

- `--task "fix the login bug"`: prioritize files whose paths or contents match task keywords.
- `--format json`: include file lists, skip reasons, and size estimates.
- `--exclude "*.log"`: exclude a filename or relative-path pattern. Repeat for more patterns; use `/` for path separators. Matching is case-sensitive.
- `--raw`: include all eligible files without applying the token budget.

Text mode prints context to standard output and the summary to standard error.
In JSON mode, the budget applies to the `context` field, not the entire report.
Nothing is sent to an assistant automatically.

## Task-based selection

```console
tokenoptimizer context . --task "fix gitignore scanning" --budget 4000 --format json
```

Task matching is local and uses no AI service. Matches are case-insensitive whole
words, including words in `snake_case` and `camelCase` identifiers. Common request
words such as "fix" and "the" are ignored. Each distinct keyword earns four
points when found in a path and one when found in content; repetition adds no
points. Higher scores come first, with the usual file order breaking ties.

JSON adds `task_selection` with the keywords, ordered scores, and path/content
matches for every eligible file. This report is outside the context budget.
Unmatched files can still fill remaining space. If the task has no searchable
keywords or no files match, the default order is used with a warning.

Without `--task`, behavior and JSON fields stay the same. `--raw --task` ranks
all eligible files without applying a budget. Keyword matches are relevance hints;
the tool does not understand dependencies or guarantee that every necessary file
is selected.

## Git ignore rules

In a Git project, the scanner uses Git's ignore rules, including nested
`.gitignore` files, `!` exceptions, `.git/info/exclude`, and configured global
exclusions. Tracked files stay eligible, but scanner defaults and `--exclude`
still take precedence.

For example, if `.gitignore` contains `logs/`, an untracked `logs/` folder is
listed in the JSON `files_skipped` report with the reason `ignored by Git`:

```console
tokenoptimizer context "C:/Projects/MyApp" --format json
```

Outside a Git repository, or if Git is missing or fails, the scanner uses its
normal filters. Text mode reports a warning on standard error; JSON mode includes
it in `warnings`. Ignore rules are not applied in that case. Scan nested
repositories and submodules separately to use their own ignore rules.

## Current limits

- Token counts are estimates: `ceil(UTF-8 bytes / 4)`.
- Without a task, root README and assistant instruction files come first, then `src/`, then other paths. Task keywords change priority when `--task` is supplied.
- Files are included whole or omitted. A small budget can produce empty context.
- Hidden paths, common dependency/build folders, generated lockfiles, OS metadata, credential-file extensions, links, binary/non-UTF-8 files, and large files are skipped. See [scanner defaults](src/core/scanner/__init__.py) for the lists. This is not secret detection.
- Reads are capped at 128 KiB per file and 8 MiB per scan.
- `--raw` still uses Git ignore rules, scanner exclusions, and read limits.

## Tests

```console
python -m unittest discover -s tests -v
```

Tested on Windows with Python 3.12. Other platforms still need testing.

To build and check an installable wheel:

```console
python -m pip wheel --no-deps --wheel-dir dist .
python tests/check_install.py dist/tokenoptimizer-0.1.0a2-py3-none-any.whl
```

The install check creates a temporary environment, installs the wheel without
network access, runs it outside the checkout, and checks uninstalling it.

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
