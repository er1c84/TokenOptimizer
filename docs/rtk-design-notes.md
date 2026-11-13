# RTK notes

References reviewed on November 12, 2026:

- [RTK repository](https://github.com/rtk-ai/rtk)
- [RTK architecture](https://github.com/rtk-ai/rtk/blob/develop/docs/contributing/ARCHITECTURE.md)

Useful ideas: small processing steps, shared logic behind tool adapters, visible
before/after estimates, and access to the unfiltered input.

TokenOptimizer applies those ideas to project files. The scanner, selector,
estimator, and CLI are separate modules. `--raw` returns eligible context without
a budget. No RTK source code was copied or added as a dependency.

RTK's core workflow routes assistant commands through command-specific output
filters. For example, it condenses test results while keeping failure details,
or formats Git output more compactly. It also provides bypass and savings
reporting. These are useful patterns for future command filters here.

TokenOptimizer currently selects whole project files, with optional task-keyword
ranking. It does not yet filter command output or hook into an assistant. Keep
future filters separate, add one command at a time, preserve access to full
output, and measure complete tasks before claiming comparable savings.
