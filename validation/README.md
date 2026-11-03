# Repository-release validation

These reports were produced by a fresh run of the repository-level reproduction command. They are distinct from the original attachment's `paper/validation/` records.

- `RUN_SUMMARY.json`: actual environment, completed stages and runtime.
- `CLEAN_CHECKOUT.json`: a separate full run from staged repository files, with all six compressed files restored from a clean checkout.
- `archive_validation.json`: 184 frozen file hashes, CSV/JSON integrity, 209 evidence rows, display links and control dimensions.
- `control_comparison.json`: all 1,700 regenerated allocations and 49,300 scalar numerical metric comparisons; also reports byte-identical output files.
- `matrix_replay.json`: 40 deterministic primary-solve examples across eight archived matrix families; the report states which families also compare saved objectives.
- `derived_accounts.json`: published-retention complements, 216 cohort-delay scenarios and financial-account reconciliation.
- `example_checks.json`: gas/coal common-reference examples, the ARA regional-price Figure 1 reference, and the private-allocation example checked against retained V7 records.

The original kernels and frozen payload remain unchanged. Full-control regeneration and sampled-matrix replay have different coverage. These deterministic checks are reproducibility evidence, not statistical confidence intervals or a new independent scientific peer review.
