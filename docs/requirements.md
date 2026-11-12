# Requirements

## Product goals

| ID | Approved requirement | Current status |
| --- | --- | --- |
| R1 | Hybrid optimization: automatic and manual workflows. | Manual project-context tool only. |
| R2 | MCP and native integrations. | Directory placeholders only. |
| R3 | Comprehensive optimization in phases: project context first, then conversations and prompts. | Basic whole-file project-context selection. |

## Constraints

- Keep processing local and offline-first. No cloud infrastructure.
- Keep dependencies small. The prototype uses only the Python standard library.
- Preserve the original README description and MIT license.
- Keep integrations separate from the core.
- Adapt design ideas from RTK without copying its code.
- Treat Python as the prototype language; the production language and build system remain open.

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

## Open decisions

- Production language, build system, packaging, and supported platforms.
- Native integration methods, MCP capabilities, and transport.
- Automatic triggers, task relevance, and file-selection policies.
- Model tokenizers and accuracy expectations.
- Cache storage, limits, invalidation, and retention.
- Configuration format, location, and precedence.
- Quality checks and performance targets for real projects.

Current defaults are prototype behavior. Planned changes are in the
[roadmap](roadmap.md).
