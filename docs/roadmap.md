# Development roadmap

## Milestone 1: Structure plus working draft

Status: prepared for review, uncommitted.

- Modular core, integration, CLI, configuration, test, benchmark, documentation, and example directories.
- Requirements, architecture, roadmap, and independently adapted RTK design notes.
- A manual, read-only project-context CLI with bounded scanning, whole-file budget selection, JSON reporting, and raw comparison.
- A sample project and standard-library unit/integration checks.

Review the structure, run the example, inspect omitted/skipped files, and assess
whether this small workflow is the right foundation. Production language and
build-system selection are the next decision. This draft does not implement the
broader Milestone 2 engine.

## Milestone 2: Production project-context foundation

Status: pending scope and technology approval.

Refine or replace the prototype according to the approved production language and
build system. Define task-aware context selection, ignore policies, model-aware
token budgeting, local cache behavior, and configuration contracts before
implementation. Choose a small first slice rather than assuming every capability
must ship together.

Exit criteria: the agreed workflow works locally, has representative correctness
checks and reproducible benchmarks, and meets explicit quality and resource
targets. File omission alone does not establish optimization quality.

## Later: Native integrations, MCP, and automatic workflows

Status: required product direction; implementation sequence pending.

Validate integration feasibility, then add Codex and Claude Code native adapters
and MCP using shared core contracts. Define manual/automatic controls and
integration checks before enabling automatic behavior.

## Later: Conversation and prompt optimization

Status: required product direction; detailed scope pending.

Define input/output contracts, local data policies, quality criteria, and
performance targets before extending beyond project context.

## Future expansion

Additional AI API adapters and distribution methods remain possible extensions,
not current implementation commitments. No release dates or cloud services are
part of this roadmap.
