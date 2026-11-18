# Connect to Codex

Install MCP support using Python 3.12 or newer:

```powershell
python -m pip install ".[mcp]"
```

Use standard Windows Python rather than MSYS2/MinGW on Windows. Use the same
Python environment for installation and the server command below.

## Register the tool

Register the server in Codex's shared settings. Use the full path to the Python
environment where you installed TokenOptimizer and its MCP dependencies:

```powershell
codex mcp add tokenoptimizer -- "C:/path/to/python.exe" -m tokenoptimizer.integrations.mcp.server
codex mcp get tokenoptimizer
```

In Codex's user configuration (`~/.codex/config.toml`), add these settings under
the new `[mcp_servers.tokenoptimizer]` entry:

```toml
required = true
startup_timeout_sec = 20
```

Codex then waits for the tool to connect before starting work. If the server
cannot start, Codex reports the connection error. Optional servers can be omitted
from the initial tool list while they are still connecting.

Without `--project`, the server scans its starting folder. The project-specific
setup below can pin it to a particular folder.

Use Settings → MCP servers → Restart after changing the settings, or fully quit
and reopen Codex. Closing a window may leave its background process running.
In the Codex CLI, use `/mcp` to check for `tokenoptimizer` and its
`get_project_context` tool. A working server test alone does not confirm that an
existing chat has loaded the tool.

If an existing chat still does not list the server, open a new Codex chat in the
configured project and check `/mcp` there.

Ask Codex:

> Use TokenOptimizer's get_project_context tool with task "gitignore scanner"
> and budget 4000, then explain which code handles ignore rules.

Confirm that Codex uses the MCP tool directly. If it runs a Python command or
starts a separate MCP client instead, the chat has not loaded the tool yet.

## Check the connection

From a TokenOptimizer checkout, run:

```powershell
python tests/check_codex.py
```

This requires the Codex CLI on PATH and the saved MCP settings. It verifies tool
discovery and a budgeted context request through Codex's own tool system in an
in-memory session. It does not start a model turn or create a saved chat. Check
the tool list in your desktop chat separately using `/mcp`.

## Project-specific setup

In the project you want Codex to work on, create `.codex/config.toml` with the
following entry. Replace the paths with absolute paths on your computer; forward
slashes also work on Windows.

```toml
[mcp_servers.tokenoptimizer]
command = "C:/path/to/python.exe"
args = ["-m", "tokenoptimizer.integrations.mcp.server", "--project", "C:/Projects/MyApp"]
cwd = "C:/Projects/MyApp"
required = true
startup_timeout_sec = 20
```

On macOS or Linux, use paths such as `/path/to/venv/bin/python` and
`/path/to/project`. The server is fixed to the folder supplied with `--project`.

The project must be trusted in Codex for its local configuration to load. Keep
this configuration local: it contains paths specific to your computer. This
repository ignores its own `.codex/config.toml`.

Restart Codex after saving the configuration and open the configured project.
The project entry overrides the shared entry with the same name.

## Using it during work

This repository's `AGENTS.md` asks Codex to use the tool when it needs to explore
the project, while allowing additional reads and normal searches. Other projects
can add the same guidance to their own `AGENTS.md`.

The budget limits the selected file contents returned by this tool. It does not
limit all Codex reads, conversation tokens, or total usage. Actual savings depend
on whether the selected files reduce the work needed for the task.

To remove the shared registration, run `codex mcp remove tokenoptimizer`. If you
also added a project entry, remove it from that project's configuration. Restart
Codex after disconnecting.

Configuration details: [Codex MCP documentation](https://developers.openai.com/codex/mcp/).
