# TokenOptimizer

TokenOptimizer is a local command-line tool that selects project files for AI
coding assistants. It prepares a smaller bundle of file contents using an
estimated token budget and optional task keywords.

## How it works

1. Scans a project folder for UTF-8 text files.
2. Applies Git ignore rules and exclusions, skipping hidden files, binary files, and common dependency/build folders.
3. Prioritizes files using keywords from your task. Without a task, it puts root guidance files first, followed by `src/` and other files.
4. Includes complete files that fit the budget and reports what was included, omitted, or skipped.

Matching uses words in file paths and contents. It ignores case and recognizes
words in `snake_case` and `camelCase` names. If nothing matches, it uses the
default file order and reports a warning.

Files remain unchanged. You run the tool and pass the selected contents to your
assistant. Token counts are estimates based on UTF-8 size. The budget covers the
selected context, not the extra JSON report. Reads are limited to 128 KiB per file
and 8 MiB per scan.

## Install

Requires Python 3.12 or newer. Git is needed to apply ignore rules.

```powershell
git clone https://github.com/er1c84/TokenOptimizer.git
cd TokenOptimizer
python -m pip install .
```

If you already have the repository, run the install command from that folder.
If pip is missing, run `python -m ensurepip --upgrade` first. If you use a virtual
environment, activate it before installing and running the tool.

Installing from source may download setuptools to build the package. The tool
runs locally and has no third-party runtime packages.

## Use

From the project folder you want to scan:

```powershell
tokenoptimizer context . --task "fix the login bug" --budget 4000
```

The `.` means the current folder. To scan a different project:

```powershell
tokenoptimizer context "C:/Projects/MyApp" --budget 4000 --format json
```

Text output contains the selected files and a brief summary. JSON also includes
file lists, skip reasons, token estimates, and task-ranking details when a task
is provided.

If your terminal cannot find `tokenoptimizer`, use the same Python environment
you installed it with:

```powershell
python -m tokenoptimizer context . --task "fix the login bug" --budget 4000
```

## Options

| Option | What it does |
| --- | --- |
| `--budget 4000` | Sets the estimated context budget. Default: 2000. |
| `--task "fix the login bug"` | Prioritizes files that match task keywords. |
| `--format json` | Prints context and selection details as JSON. Default: text. |
| `--exclude "*.log"` | Excludes a filename or relative-path pattern. Repeat for more patterns; use `/` for paths. Matching is case-sensitive. |
| `--raw` | Includes all eligible files without a budget. Ignore rules, exclusions, and read limits still apply. |

Use `tokenoptimizer context --help` for command help and `tokenoptimizer --version`
to check the installed version.

## MCP server

Install the optional MCP support from the repository folder:

```powershell
python -m pip install ".[mcp]"
```

On Windows, use a standard Python installation from [python.org](https://www.python.org/downloads/windows/).
The MCP SDK's Windows dependencies do not support MSYS2/MinGW Python.

Launch the server for a project:

```powershell
tokenoptimizer-mcp --project "C:/Projects/MyApp"
```

You can also launch it with `python -m tokenoptimizer.integrations.mcp.server`.
The server uses stdio: an MCP client starts it and sends requests through its
input and output streams. Starting it in a terminal leaves it waiting for a
client; press Ctrl+C to stop it.

The read-only `get_project_context` tool accepts `task` and an optional `budget`
(default: 4000). It returns selected context, estimated tokens, file counts, and
warnings. Requests use the folder configured with `--project`, which defaults
to the server's starting folder. The client connection is configured separately.
The base CLI installation does not require the MCP SDK.

## License

[MIT](LICENSE).
