# Requirements

## Scope update

The initial request limited Milestone 1 to structure and documentation. The later
request explicitly expanded it to a rough draft that works, drawing ideas from
RTK without copying its implementation. The current milestone therefore includes
a minimal manual project-context CLI alongside the repository foundation. It
does not attempt the full optimization engine or integrations.

## Approved product requirements

| ID | Requirement | Current delivery |
| --- | --- | --- |
| R1 | Hybrid optimization: automatic and manual optimization. | Manual project-context prototype only; automatic workflows pending. |
| R2 | MCP and native integrations. | Architecture and directory boundaries only; implementation pending. |
| R3 | Comprehensive optimization in phases, beginning with project context and expanding to conversation and prompt optimization. | Whole-file project-context selection prototype; later workflows pending. |

## Constraints

- Keep processing local, lightweight, and offline-first; add no cloud infrastructure.
- Use independently written code; adapt design ideas rather than copying RTK code, filters, tests, or assets.
- Preserve the original README text and existing LICENSE; extend the README with current status and instructions.
- Use only necessary dependencies; the prototype uses the Python standard library and adds none.
- Keep the production language and build system unresolved. Python 3.12+ is explicitly a prototype implementation choice.
- Leave changes uncommitted for review.
- Keep future integrations modular and track empty directories with placeholders.

## Working draft acceptance criteria

- Run from a checkout using Python, without package installation or a network service.
- Scan a local project without modifying its contents.
- Select whole UTF-8 files within a stated estimated context budget, including file headers in accounting.
- Report selected, omitted, and skipped paths; explain omissions and skips in JSON.
- Support explicit exclusions and a raw eligible-context comparison.
- Label counts as estimates and distinguish context reduction from quality or billing claims.
- Include an executable example and checks for selection, exclusions, accounting, errors, and CLI behavior.
- Keep automatic hooks, MCP, native adapters, cache storage, and advanced algorithms outside this draft.

## Pending approval decisions

| Decision | Questions to resolve |
| --- | --- |
| Production language and build system | Rust, Python, or another language? Which packaging, build, and test tools? |
| Supported platforms and distribution | Which OS versions and installation/update methods? The draft has been exercised on Windows only. |
| Integration contracts | Native connection methods for Codex and Claude Code; MCP capabilities and transport; future API scope. |
| Context policy and workflows | Automatic triggers and controls, Git ignore support, task relevance, handling generated and sensitive content, and selection priorities. |
| Token counting | Supported models, tokenizer dependencies, accuracy expectations, and budget-overflow behavior. |
| Cache and configuration | Storage location, format, size, invalidation and retention; configuration format, location, and precedence. |
| Success criteria | Representative workloads, quality checks, token-savings goals, latency limits, and resource budgets. |

The current defaults are reviewable prototype behavior, not approved final
policies. Resolve the production language first, then the remaining decisions
before implementing their corresponding capabilities.
