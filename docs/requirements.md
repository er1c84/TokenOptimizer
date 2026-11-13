# Requirements

## Product goals

| ID | Approved requirement | Current status |
| --- | --- | --- |
| R1 | Hybrid optimization: automatic and manual workflows. | Manual project-context tool only. |
| R2 | MCP and native integrations. | Local read-only MCP server; native assistant setup remains separate. |
| R3 | Comprehensive optimization in phases: project context first, then conversations and prompts. | Whole-file selection with optional task-keyword ranking. |

## Constraints

- Keep processing local and offline-first. No cloud infrastructure.
- Keep base runtime dependencies small. The CLI uses the standard library; MCP support is an optional SDK dependency. Setuptools is used for packaging.
- Preserve the original README description and MIT license.
- Keep integrations separate from the core.
- Package the current Python version without committing to a long-term production language or build system.

## Milestone 1

- Run from a checkout without package installation.
- Read project files without modifying them.
- Select whole files within an estimated budget, including file headers.
- Report included, omitted, and skipped paths, with reasons in JSON.
- Support explicit exclusions and a raw-context comparison.
- Include a sample project and unit/integration tests.

## Milestone 2

- Use Git's ignore rules, including nested rules and exceptions, for Git projects.
- Keep tracked files eligible while preserving scanner defaults and explicit exclusions.
- Report ignored paths and warn when Git ignore rules cannot be applied.
- Test ignore behavior, fallback behavior, and read-only scanning.

## Milestone 3

- Install the current version with pip and provide a `tokenoptimizer` command.
- Support `python -m tokenoptimizer` and keep the checkout launcher working.
- Include help, version information, update and uninstall instructions.
- Verify a built wheel in a clean environment outside the checkout.
- Keep installation separate from assistant integration.

## Milestone 4

Task-based selection is implemented as Milestone 4: local path/content keyword
matching, ranking evidence in JSON, fallback to the default order, and tests for
ranking, budget limits, exclusions, and installed-command behavior. It adds no
runtime packages or automatic assistant integration.

## MCP server

The MCP server exposes the existing context builder over stdio, fixes a project
root at startup, returns compact read-only results, and leaves assistant settings
unchanged. It has protocol and packaging checks. Windows MCP installations use
standard Windows Python rather than MSYS2/MinGW.

## Open decisions

- Production language, long-term build tooling, standalone distribution, and supported platforms.
- Native integration methods, MCP capabilities, and transport.
- Automatic triggers, task relevance, and file-selection policies.
- Model tokenizers and accuracy expectations.
- Cache storage, limits, invalidation, and retention.
- Configuration format, location, and precedence.
- Quality checks and performance targets for real projects.

Current defaults are prototype behavior. Planned changes are in the
[roadmap](roadmap.md).
