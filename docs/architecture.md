# Architecture: working Milestone 1 draft

## Scope and technology status

The original structure-only milestone was expanded at the user's request to
include a small working prototype informed by RTK's design. The implementation
is independently written for TokenOptimizer's project-context workflow.

Python 3.12+ and the standard library are used to make the draft runnable without
installation or added dependencies. The production language, build system,
distribution format, and final package layout remain pending approval. This
prototype does not select Rust or commit the project to Python for production.

## Directory responsibilities

| Directory | Responsibility | Draft status |
| --- | --- | --- |
| `docs/` | Requirements, architecture, roadmap, and design references. | Written. |
| `src/core/` | Shared engine behavior, independent of assistant SDKs. | Minimal context workflow. |
| `src/core/scanner/` | Read-only project discovery and bounded UTF-8 reads; record skipped paths and reasons. | Implemented with fixed defaults and explicit exclusions. |
| `src/core/context/` | Shared file/omission records and context formatting with path headers. | Implemented; source text is preserved. |
| `src/core/optimizer/` | Select context within a budget and report before/after size. | Simple deterministic whole-file selection only. |
| `src/core/tokenizer/` | Token accounting and future model-aware counting. | UTF-8 size heuristic only. |
| `src/core/cache/` | Future local reuse, storage limits, and invalidation. | Placeholder. |
| `src/integrations/` | Translate external tool/protocol contracts to core inputs and outputs. | Reserved boundary. |
| `src/integrations/codex/` | Future Codex native integration. | Placeholder; no hooks installed. |
| `src/integrations/claude/` | Future Claude Code native integration. | Placeholder; no hooks installed. |
| `src/integrations/mcp/` | Future MCP server and protocol handling. | Placeholder; no server implemented. |
| `src/integrations/api/` | Future optional AI API adapters. | Placeholder; no provider selected. |
| `src/cli/` | Argument parsing, manual invocation, text/JSON presentation, and error exits. | Implemented. |
| `src/config/` | Explicit settings and defaults; future configuration loading and validation. | In-memory settings only. |
| `tests/unit/` | Component behavior, scanner boundaries, selection, and accounting checks. | Implemented using `unittest`. |
| `tests/integration/` | End-to-end CLI behavior and read-only checks. | Implemented using subprocesses and temporary fixtures. |
| `benchmarks/` | Future reproducible token, latency, and memory workloads. | Placeholder; no performance claims. |
| `examples/` | Runnable sample project and expected selection behavior. | Small greeting project. |

`tokenoptimizer.py` is a thin repository-local launcher. Python namespace packages
allow the source tree to run without a package installation or build manifest.
Empty leaf directories contain `.gitkeep`; remove those placeholders when real
files occupy them.

## Dependencies and flow

```text
tokenoptimizer.py -> CLI -> scanner -> file records
                        -> selector -> formatted context + report

CLI supplies explicit settings.
Scanner uses settings and shared records.
Selector uses shared records, formatting, and token estimation.
Future adapters call the same core rather than duplicating selection behavior.
```

Core modules do not import the CLI, assistant SDKs, or integration implementations.
The scanner currently depends on the settings record in `src/config/`, not a
configuration-file loader. There are no third-party runtime dependencies.

1. The CLI validates the manual request and budget.
2. The scanner discovers files in deterministic order, prunes exclusions, and reads within byte limits.
3. The selector prioritizes root guidance files, then `src/`, then other paths.
4. Each complete file is included if its content and framing fit the remaining estimated budget. Oversized candidates are omitted; later candidates are still considered.
5. The CLI emits context and inclusion/omission reporting. No source files or settings are changed.

## Measurement contract

The baseline is the formatted context of all eligible, successfully scanned files
in selection order, after scanner exclusions and limits. The output estimate is
the formatted selected subset, including file headers and separators. Both use
`ceil(UTF-8 bytes / 4)`. Reporting metadata is outside this budget.

The reported percentage measures estimated context-size reduction through file
omission. It does not measure task quality, semantic preservation across omitted
files, provider tokenization, or billing savings. Empty input reports zero
reduction. `--raw` uses the same scanner and ordering but bypasses the budget,
making the baseline reproducible.

## Boundaries still to design

Automatic triggers, native adapters, MCP contracts, real tokenizers, persistent
cache policy, configuration files, task-aware relevance, and distribution remain
future work. See [requirements](requirements.md) for pending approval decisions,
the [roadmap](roadmap.md) for sequencing, and [RTK notes](rtk-design-notes.md) for
the design reference and the limits of this adaptation.
