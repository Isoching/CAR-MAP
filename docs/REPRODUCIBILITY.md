# Reproduction guide

## Environment

Use Python 3.12; the retained local environment is Python 3.12.7, NumPy 1.26.4, SciPy 1.13.1, CoolProp 8.0.0 and openpyxl 3.1.5. Install `requirements.txt` in a virtual environment. `environment.yml` is an alternative for conda users. The numerical run does not require Microsoft Office, proprietary solvers or plotting fonts. Allow disk space for the original ZIP, approximately 342 MB of expanded source files and regenerated outputs; parsing the largest JSON also requires additional memory.

## Full reproduction

From the repository root:

```bash
python scripts/reproduce.py --mode full
```

The runner executes the following stages and stops with a non-zero exit code on failure:

1. Verify the original ZIP and six gzip hashes; restore the six original files.
2. Run `paper/code/validate_archive.py`: check 184 manifest-listed file hashes, CSV/JSON structure, display links, 209 evidence rows, scenario dimensions and frozen kernel hashes.
3. Run `paper/code/replay_matrix_examples.py`: solve five deterministic examples from each of eight saved LP families, for 40 examples in total.
4. Run `paper/code/check_derived_accounts.py`: reconstruct published retention complements, 216 delay scenarios, cohort shortfalls and public/recipient financial identities.
5. Run `paper/code/run_control_calculations.py`: regenerate all 1,700 V7 control allocations from the packaged engineering and allocation kernels.
6. Run `paper/code/compare_controls.py`: compare all 1,700 scenario keys and 49,300 scalar numerical metrics with the frozen controls; also report byte-identical output files.
7. Run `paper/code/export_control_matrices.py`: rebuild the 1,700 explicit control matrices from the archived scenarios and kernels and check the retained solutions' feasibility.

Reports and logs are written to `reproduced/`. `RUN_SUMMARY.json` records the environment, stages and elapsed time. Use `--output /path/to/new/results` to select another output directory outside `paper/`. All commands preserve the frozen scientific payload.

The smaller `--mode quick` command runs stages 1–4. It is an integrity and sampled replay check, not the complete control regeneration.

## Control counts

| Group | Scenario rows | Allocations regenerated |
|---|---:|---:|
| Literature inventory controls | 24 paired | 48 |
| Normalised electricity | 36 paired | 72 |
| Joint inventory/electricity/synthesis-cost controls | 720 paired | 1,440 |
| Hydrogen access | 36 paired | 72 |
| Inventory extension | 28 paired | 56 |
| Entry-calibrated private support | 12 individual | 12 |
| **Total** | **844 paired + 12 individual** | **1,700** |

Each paired row includes independently optimised all-route and storage-only allocations. The primary and secondary lexicographic LP calls within one allocation are not counted as separate scenario observations.

## Tolerances and what is compared

The original comparison script uses absolute tolerances of USD 1 for USD-valued scalar metrics, 0.05 for tonnes and service-GJ metrics, and 1e-5 for other scalar metrics, plus a 1e-9 relative allowance. It also requires matching scenario keys, parameter records and feasible results. The report's 49,300 comparisons refer to scalar numerical metrics; the comparator does not recursively compare every nested flow vector or dual dictionary. Byte identity is an additional stronger check when achieved.

For control-matrix examples, the saved secondary-refined primary objective is compared with a freshly solved primary optimum within the declared lexicographic tolerance. Joint-grid examples additionally compare retained primary values. Other saved policy examples establish primary-solve feasibility; they do not establish identity with every saved policy optimum. Retained decimal vectors may have machine-level residuals after reconstruction. See `matrix_replay.json` and the script for exact tolerances.

The full runner does **not** regenerate every historical main/supplementary figure grid or figure artwork. It preserves the complete current figure/table source-data crosswalk and their saved optimisation evidence. Published geological endpoints are external summary evidence, not draws from a new Monte Carlo simulation. These scope distinctions are part of the reproducibility record.

## Running a new scenario

```bash
python examples/run_scenario.py --help
python examples/run_scenario.py --region ARA --inventory 0.85
python examples/run_scenario.py --region ARA --inventory 4.81 --output reproduced/coal.json
python examples/run_scenario.py --region ARA --regional-price --output reproduced/figure1_reference.json
python examples/run_scenario.py --region US --inventory 0.85 --output reproduced/us.json
python examples/run_scenario.py --region ARA --objective private --support utilization --rate 800 --fiscal-cap 20 --output reproduced/policy.json
```

The common gas-reference ARA example gives approximately **974,083.681 tCO₂e/y** abatement for both portfolios. The common high-coal ARA example gives approximately **981,864.612 tCO₂e/y** all-route abatement, **974,083.681 tCO₂e/y** storage-only abatement, and a **7,780.931 tCO₂e/y** increment. The ARA regional-price gas reference underlying Figure 1 instead gives approximately **965,052.567 tCO₂e/y** for both portfolios. Compare full-precision report values rather than rounded table cells.

The private example uses a generic mechanism with a fiscal ceiling. It does not impose the mitigation resource-spending ceiling. Every output includes the complete parameter record and effective electricity assumptions. Changing these values defines a new scenario; it does not overwrite the publication data.

## Original attachment alone

The byte-identical ZIP can be downloaded from `datasets/Energy_Source_Data_V7_20261102.zip`, extracted and run independently using its own `REPRODUCE.md`. Its README and metadata describe the attachment at its original preparation date. Repository additions and current rights information are documented separately at the repository root.
