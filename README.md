# TokenOptimizer
A lightweight, local tool designed to reduce AI token usage across coding assistants and AI-powered applications.

TokenOptimizer is planned as a local-first, cross-platform engine for Codex,
Claude Code, and future AI integrations.

## Current status

Milestone 1 is a working draft for review: a modular repository plus a small,
read-only project-context CLI. It discovers local UTF-8 files, selects complete
files within an estimated token budget, and reports inclusions, omissions, and
before/after estimates. Source files are never rewritten.

The prototype uses Python 3.12+ and its standard library, with no package
installation, network calls, or cloud infrastructure. This is an explicit
prototype choice, not a final production-language or build-system decision.

The approved product requirements are:

1. Hybrid optimization: automatic and manual optimization.
2. MCP and native integrations.
3. Comprehensive optimization delivered in phases, starting with project context
   and expanding to conversation and prompt optimization.

Only the manual project-context draft is implemented. Automatic workflows, native
assistant adapters, MCP, caching, and model-specific tokenizers are future work.

## Try the working draft

From the repository root with Python 3.12+ installed:

```console
python tokenoptimizer.py context examples/sample_project --budget 100
python tokenoptimizer.py context examples/sample_project --budget 100 --format json
```

The included sample selects `README.md` and `src/hello.py`, omitting
`docs/notes.md`. In the tested checkout it reduces the estimated context size
from 227 to 77 tokens (66.08%); line endings can change these estimates. This is
a demonstration of leaving files out, not a measured improvement in answer
quality or actual provider billing.

Scan your project, exclude additional paths, or compare all eligible content:

```console
python tokenoptimizer.py context . --budget 2000 --exclude "examples/*" --format json
python tokenoptimizer.py context examples/sample_project --raw --format json
```

Text mode puts context on standard output and a brief report on standard error.
JSON mode returns context, included paths, omitted/skipped paths and reasons,
estimates, and the budget. Only the `context` value is budgeted; JSON reporting
overhead is not included. Output is UTF-8. Nothing is sent to an assistant
automatically; inspect and use the selected context in your workflow.

### Prototype behavior and limits

- Counts use `ceil(UTF-8 bytes / 4)`, not a model-specific tokenizer. The budget is an estimate, not a guarantee of actual model token usage.
- Root `README.md`, `AGENTS.md`, and `CLAUDE.md` come first, then `src/` files, then other paths, sorted lexicographically within each group. There is no task-aware relevance ranking yet.
- Files either fit whole or are omitted. Larger files do not prevent later smaller files from being considered. A very small budget may produce empty context.
- Hidden paths, dependency/build directories, common generated lockfiles, OS metadata, credential-file extensions, links, non-UTF-8/binary content, and oversized files are skipped. See the [scanner defaults](src/core/scanner/__init__.py) for the exact lists. These exclusions are not a secret-detection system.
- Reads are limited to 128 KiB per eligible file and 8 MiB total per scan. Discovery is deterministic, visiting directory entries in sorted order. Skipped directories are reported once, not expanded into every child path.
- `--exclude` accepts repeatable, case-sensitive filename or relative-path globs using `/` separators; a matching directory is pruned. This draft does **not** read `.gitignore` or implement Git's ignore rules.
- `--raw` bypasses budget selection while retaining scanner exclusions and read limits. Original files remain available on disk.

## Project structure

```text
TokenOptimizer/
|-- README.md
|-- LICENSE
|-- .gitignore
|-- tokenoptimizer.py
|-- docs/
|   |-- requirements.md
|   |-- architecture.md
|   |-- roadmap.md
|   `-- rtk-design-notes.md
|-- src/
|   |-- core/
|   |   |-- scanner/
|   |   |-- optimizer/
|   |   |-- context/
|   |   |-- cache/
|   |   `-- tokenizer/
|   |-- integrations/
|   |   |-- codex/
|   |   |-- claude/
|   |   |-- mcp/
|   |   `-- api/
|   |-- cli/
|   `-- config/
|-- tests/
|   |-- unit/
|   `-- integration/
|-- benchmarks/
`-- examples/
```

`src/core/` holds the shared engine responsibilities. `src/integrations/` reserves
separate adapters for each tool or protocol. `src/cli/` and `src/config/` separate
the command-line interface from configuration management. Tests, benchmarks,
examples, and documentation have their own directories. Empty directories use
`.gitkeep` placeholders so Git can track the structure.

Prototype Python modules occupy the active source directories; integrations,
caching, and benchmarks remain placeholders. The layout can be refined after the
production language and build system are approved.

## Documentation

- [Requirements](docs/requirements.md): approved scope, constraints, and pending decisions.
- [Architecture](docs/architecture.md): directory responsibilities and proposed dependency boundaries.
- [Roadmap](docs/roadmap.md): milestones and review criteria.
- [RTK design notes](docs/rtk-design-notes.md): reviewed references, ideas adapted, and independent implementation scope.

## Development

Run the checks without installing a test framework:

```console
python -m unittest discover -s tests -v
```

The draft has been exercised on Windows with Python 3.12. Broader platform
validation and production packaging are pending. Review this draft and select the
production language and build system before expanding implementation.

## License

TokenOptimizer is licensed under the [MIT License](LICENSE).
