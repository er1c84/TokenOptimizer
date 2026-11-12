# RTK notes

References reviewed on November 12, 2026:

- [RTK repository](https://github.com/rtk-ai/rtk)
- [RTK architecture](https://github.com/rtk-ai/rtk/blob/develop/docs/contributing/ARCHITECTURE.md)

Useful ideas: small processing steps, shared logic behind tool adapters, visible
before/after estimates, and access to the unfiltered input.

TokenOptimizer applies those ideas to project files. The scanner, selector,
estimator, and CLI are separate modules. `--raw` returns eligible context without
a budget. No RTK source code was copied or added as a dependency.
