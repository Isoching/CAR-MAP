# Captured carbon allocation: source data and reproducibility record

**Associated manuscript:** Rethinking captured carbon allocation across storage, fuels and chemicals under resource and policy constraints.

**Authors:** Yuanjing Zhao, Jin Xuan and Lei Xing, University of Surrey.

**Release:** V7 numerical source-data release, 2 November 2026. Prepared as a supporting-data attachment for the Perspective submitted to *Energy*.

## Start here

- `DISPLAY_DATA_MAP.csv` maps the four main figures, six supplementary figures and sixteen tables to files in this archive, using the current display numbering.
- `FILE_INDEX.csv` inventories every data, metadata, code and verification file. It identifies format, record count, purpose and precision class.
- `DATA_DICTIONARY.csv` explains CSV fields and their units. `metadata/FILE_SCHEMAS.json` lists the exact fields present in each CSV.
- `metadata/VARIABLES_AND_UNITS.csv` and `metadata/ABBREVIATIONS.csv` provide manuscript notation and terminology. Mathematical subscripts and superscripts use braces in these plain-text exports, such as `E_{ir}`.
- `metadata/CONTROL_COUNTS.csv` distinguishes scenario rows, paired comparisons and individual LP solves.
- `metadata/SOURCE_PROVENANCE.json` records source hashes and any packaging transformations. `CHECKSUMS.sha256` and `MANIFEST.json` identify the delivered files.

## Scientific and monetary boundaries

The technical comparisons concern annualised new routes in 2030. The regions are Amsterdam–Rotterdam–Antwerp (ARA), Teesside–Endurance (UK), the US Gulf Coast (US) and Yulin, China (CN). Fixed source cohorts are 2.5, 2, 2 and 0.4 Mt CO2/y, respectively. The common final services are 300,000 t/y chemical methanol and 5,000,000 GJ/y shaft work. Conventional backfills complete those services. Source-normalised denominators use the fixed admitted source cohort, not the optimised captured quantity. Some explicitly labelled legacy controls use alternative scale or institutional conditions.

Costs in the active numerical model use September 2026 USD. `model/MONEY_LOOKUP.json` and `model/MONETARY_PARAMETER_REGISTER.csv` retain the original currencies, price periods and conversion path. The archived ECB and HICP inputs are in `data/evidence/monetary_sources`. Source-year exchange conversion, inflation adjustment and the final USD expression are separate operations. The euro-area HICP convention is retained from the model. No additional inflation adjustment is applied during packaging.

`data/evidence/SOURCE_INPUT_LEDGER_USD.csv` contains 209 evidence rows with source URLs, page or cell locators, transformations, evidence classes, model boundaries and conditional assumptions. Published input evidence and author-defined assumptions remain labelled separately. The single obsolete temporary screenshot path in one source locator has been removed while retaining the publication URL and table/page locator. All numerical entries remain unchanged.

## Folders

| Folder | Contents |
|---|---|
| `data/evidence` | Evidence ledger, external delivery evidence and archived monetary source series |
| `data/main/Figure1` | Physical balances, ribbon inputs, route coefficients and resource–abatement frontiers |
| `data/main/Figure2` | Four-region central cases, ARA price response, inventory scans, storage-access cases and saved LPs |
| `data/main/Figure3` | Published retention endpoints, connection states, route contributions and production-cohort calculations |
| `data/main/Figure4` | Payment-object, transmission and matched-actual-outlay scans, with saved policy LPs |
| `data/supplement/Figures_S1_S2` | Complete paired gas/coal budget–electricity-access–price grids and solver evidence |
| `data/supplement/policy_accounts` | Fiscal and recipient reconciliation, including the source data for Figure S5 |
| `data/supplement/Figure_S4_SUPPORT_DEFINITIONS.json` | Definitions underlying the support-delivery schematic |
| `data/controls` | Six V7 control datasets, 1700 full-precision solutions, explicit LP matrices and summary checks |
| `data/original_scenario_grids` | Retained original model-suite grids and engineering/institutional alternatives |
| `data/tables` | Current main and supplementary tables exported as CSV and JSON at display precision |
| `model` | Unchanged allocation and engineering kernels, engineering snapshots, registered protocol and monetary inputs |
| `code` | Portable control calculation, comparison, matrix reconstruction, replay and archive-validation scripts |
| `metadata` | Display/equation maps, notation, references, evidence types, schemas and provenance |
| `validation` | Checks performed on this release, including fresh control reproduction |

## Precision, units and missing values

Computational CSV and JSON values retain their saved precision. The files under `data/tables` deliberately preserve the rounded values transcribed from the current review documents. They are a reading aid and should not be substituted for full-precision computational inputs. Values may differ in their last displayed digit when rounded operands are recomputed.

JSON `null`, empty CSV cells and explicitly labelled `NA` values denote an unavailable or inapplicable quantity. They do not mean zero. For example, an abatement-per-cost ratio at zero abatement is undefined. Boolean fields and explicit zero-allocation solutions are retained. No interpolation, averaging or replacement of solved nodes is introduced. CSV files are UTF-8, generally with a byte-order mark for spreadsheet compatibility. JSON files use UTF-8. Archived JSON Lines model streams have been losslessly converted to standard JSON arrays. No archive contains an embedded ZIP or gzip file.

The LP uses kt source CO2/y and ktH2/y internally. Power constraints use GWh/y, lifecycle objectives use ktCO2e/y, and financial objectives use MUSD/y. Reported source-data metrics generally use tonnes, MWh and USD. Matrix files retain their explicit constraint and objective units. The qualified-hydrogen decision variable uses hydrogen mass rather than CO2 mass.

## Evidence types

Allocation, connection and support scans are deterministic prospective scenarios. Geological retention intervals are published Monte Carlo summary outputs with the source study's definitions. The archive contains the published endpoints used here, not that study's underlying Monte Carlo draws. Hydrogen maturity and pipeline values are external observations with their stated cohorts and dates. Evidence types are defined in `metadata/EVIDENCE_TYPES.json`.

The 3224 paired resource-map cases comprise 1612 gas-reference and 1612 coal-reference cases. Each panel has 403 combinations of 31 prices and 13 spending ceilings. The additional eight switching-boundary cases are retained in the joint LP evidence, giving 3232 matrix records there. Figure S1a and S2a have zero methanol allocation at all tested nodes. The reference point in panel c is 69.07936363636365 USD/MWh, 57.566136363636375 USD/t source CO2 and 1.2 TWh/y electricity access.

Figure S3 uses subsets of the full joint and normalised controls. Figure S4 is an accounting schematic and has definitions rather than quantitative observations. Figure S5 is the explicit monetary reconciliation. Figure S6 compares uniform-rate support with route-entry-calibrated support. `DISPLAY_DATA_MAP.csv` provides the exact files.

The 1700 control solves comprise 24, 36, 720, 36 and 28 paired scenarios in the literature, normalised-electricity, joint, hydrogen-access and inventory-extension groups, plus 12 individual private-allocation calibration cases. The first five groups have independently reoptimised all-route and storage-only solutions. They therefore represent 844 paired scenarios and 12 calibration scenarios, not 1700 independent statistical samples.

## Reproduction and verification

See `REPRODUCE.md`. The retained numerical environment is Python 3.12, NumPy 1.26.4, SciPy 1.13.1 with HiGHS and CoolProp 8.0.0. The fresh release check reruns all 1700 control solves from the packaged kernels and inputs. `validation/CONTROL_REPRODUCTION.json` reports the comparison with the saved full-precision files. Matrix replay examples cover eight saved-matrix families. This sampled matrix check is separate from the complete 1700-control reproduction.

The original control record reports maximum absolute carbon closure error of 9.313225746154785e-10 t, financial-identity error zero and scaled primal violation zero. Reconstruction of a saved vector from decimal text can yield additional machine-level residuals, which are reported separately in matrix verification.

## References, rights and release status

`metadata/REFERENCES.csv` preserves reference labels and citation text from the main and SI documents. E-, R- and L-prefixed identifiers retained in the evidence and original model records belong to those records' original identifier systems. They are not substituted for current manuscript reference numbers. Source URLs, publication titles, table/cell locators and the current reference exports allow the evidence to be located.

The package contains numerical input extracts and derived results. It does not redistribute full third-party articles or commercial reports. Original third-party rights remain with their owners. No additional data or software licence is assigned by this packaging operation. No DOI, public repository deposit or persistent identifier is claimed. This release is an upload attachment for journal review. It does not modify the manuscript or SI documents.

