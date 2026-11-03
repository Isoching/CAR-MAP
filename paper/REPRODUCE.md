# Reproduction guide

Run commands from the extracted `Energy_Source_Data_V7` directory. Paths are relative to this directory and no author-specific filesystem is required.

## 1. Check the archive using the Python standard library

```bash
python code/validate_archive.py
```

The checker verifies manifest hashes, CSV structure, JSON syntax, display-file links, all 209 evidence rows, the six control counts, the 1700 retained solutions and the frozen allocation/engineering hashes. It writes its report outside the frozen payload, under `reproduced`.

## 2. Install the numerical environment

Use Python 3.12. The retained versions are in `model/requirements.txt`.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r model/requirements.txt
```

On Windows, activate `.venv\Scripts\activate` instead. Matplotlib and Word-processing software are not required to reproduce the calculations.

## 3. Recalculate the 1700 V7 controls

```bash
python code/run_control_calculations.py --output reproduced/controls
python code/compare_controls.py --candidate reproduced/controls
```

Published data in `data/controls` remain unchanged. The runner uses the packaged `model/allocation.py` and `model/engineering.py`, the retained monetary lookup and the declared scenarios. Only its input/output path handling has been adapted for this archive. The numerical kernels are byte-identical to the retained versions.

`CENTRAL_LITERATURE_CONTROLS.csv` contains six literature inventory anchors in each of four regions. `NORMALISED_ELECTRICITY.csv` contains three power-to-source levels and three inventory anchors. `JOINT_INVENTORY_ELECTRICITY_COST.csv` contains 720 crossed scenarios. `HYDROGEN_ACCESS.csv` contains physical-access controls. `INVENTORY_EXTENSION.csv` contains the upper inventory extension. `ENTRY_CALIBRATED_SUPPORT.csv` contains all three premiums for four payment objects.

`FULL_CONTROL_SOLUTIONS.json` stores the scenarios and full-precision metric/flow dictionaries. `SUMMARY.json` stores the counts, original residuals and numerical-kernel hashes. The comparison script checks matching scenario keys and outputs, and additionally reports byte-identical files. Its stated tolerances allow for solver and floating-point differences on other platforms.

## 4. Reconstruct and replay explicit matrices

```bash
python code/export_control_matrices.py
python code/replay_matrix_examples.py
python code/check_derived_accounts.py
```

The reconstruction creates `reproduced/CONTROL_LP_MATRICES.json` from the archived scenarios without changing the kernels. The submission copy is in `data/controls/CONTROL_LP_MATRICES.json`. Each matrix record includes the primary and secondary objective vectors, final inequalities, bounds, variable names, units, saved refined solution and objective tolerance.

The replay script checks five deterministic examples from each of eight matrix families. For retained control solutions, the saved secondary-refined objective is compared with the independently replayed primary optimum within the declared lexicographic tolerance. Gas/coal grid primary values are also compared where saved. Other policy examples check primary feasibility. The original 1700-control reproduction is the full regenerated-results check; the matrix-family replay is a separately labelled sample check.

## 5. Reconstruct figure and table values

Use `DISPLAY_DATA_MAP.csv` as the authoritative current-numbering crosswalk. Select cases using the exact scenario fields rather than averaging across regions or input nodes. Figure 2c uses `PANEL_C_COMPLETE_INVENTORY_RESPONSE.csv`, which retains the 404 original inventory nodes and 28 extension nodes. Figure S3a–b selects ARA and UK at `synthesis_cost_multiplier = 1`. Figure S3c selects `inventory = 4.81` in the normalised-electricity controls.

For the published retention endpoints, use the original percentile convention stated in the source record. The connection shortfall is reconstructed from the annual interim-state abatement and the prescribed number of delayed cohorts. For the policy accounts, reconcile actual public payment with converter and upstream receipts separately from unused authorisation. Rounded table cells do not replace full-precision inputs.
