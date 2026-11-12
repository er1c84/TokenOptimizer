# RTK design review and TokenOptimizer adaptation

Reviewed on November 12, 2026:

- [RTK repository and README](https://github.com/rtk-ai/rtk): local command-output processing, visibility into savings, and a way to access unfiltered output.
- [RTK architecture](https://github.com/rtk-ai/rtk/blob/develop/docs/contributing/ARCHITECTURE.md): separate command handlers, shared processing/accounting infrastructure, and a staged command lifecycle.

These are links to a moving upstream branch. This review uses high-level design
ideas only; it does not import an RTK version or promise compatibility.

## Ideas applied independently

| Observed idea | TokenOptimizer draft |
| --- | --- |
| Small, inspectable processing steps | Scanner, file records, selector, estimator, and CLI have separate responsibilities. |
| Shared behavior behind tool-specific boundaries | Future Codex, Claude Code, MCP, and API adapters have separate homes around the core. |
| Visible before/after accounting | Every result includes estimated context size before and after selection. |
| Access to unfiltered input | `--raw` returns all eligible scanned context without budget selection; original files are never changed. |

TokenOptimizer's draft operates on project files. It does not reproduce RTK's
command proxy, command-specific filters, shell rewrites, analytics history,
pipelines, or API proxy. No RTK source code, tests, assets, or filter definitions
were copied, and no RTK dependency was introduced. TokenOptimizer's existing MIT
license remains unchanged.

The independently written selector uses a fixed file ordering and a whole-file
size budget. It does not claim RTK's performance or savings figures. The shared
design lessons are modular local processing, inspectability, and measurement.
