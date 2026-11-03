# Dataset guide

## Versions and provenance

The scientific payload is the 186-file `Energy_Source_Data_V7_20261102.zip` supplied by the authors, preserved verbatim in `datasets/`. Its contents are also exposed under `paper/`. Six files larger than 5,000,000 bytes are stored as gzip streams; `scripts/prepare_data.py` restores their exact original bytes. `PACKAGING.json` records both compressed and decompressed hashes. `paper/MANIFEST.json` checks 184 payload files; the original manifest and checksum inventory account for the two remaining files.

The numerical kernels have not been edited for this repository. `paper/metadata/SOURCE_PROVENANCE.json` records the original packaging provenance. Repository-level scripts, examples, documentation and validation reports are additions around the frozen V7 payload. The attachment's historical statements about repository and licensing status are retained as records of the attachment date; current release information is in the root README and RIGHTS.md.

## Finding a display

Use [`DISPLAY_DATA_MAP.csv`](../paper/DISPLAY_DATA_MAP.csv) as the authoritative crosswalk. It maps the four main figures, six supplementary figures and sixteen tables (three main plus thirteen supplementary) to source files and selection rules.

| Display or data group | Main location | Content |
|---|---|---|
| Figure 1 | `paper/data/main/Figure1/` | Physical electricity/carbon balances, route coefficients and 820 frontier allocations |
| Figure 2 | `paper/data/main/Figure2/` | Four-region central cases, ARA price response, conventional-inventory response and storage-access response |
| Figure 3 | `paper/data/main/Figure3/` | Published geological-retention endpoints, connection states, route contributions, delayed cohorts and cumulative lifecycle accounts |
| Figure 4a | `paper/data/main/Figure4/panel_a/` | Generic support objects, rates, entry thresholds and fiscal response |
| Figure 4b | `paper/data/main/Figure4/panel_b/` | Hydrogen-support qualification, realisation and pass-through; large matrices and full scan are compressed |
| Figure 4c | `paper/data/main/Figure4/panel_c/` | Comparisons at matched actual public outlay |
| Figures S1–S2 | `paper/data/supplement/Figures_S1_S2/` | Gas/coal budget–power–price maps and matrix evidence |
| Figure S3 | `paper/data/controls/` | Selected joint-inventory and normalised-electricity controls; use the crosswalk's exact filters |
| Figure S4 | `paper/data/supplement/Figure_S4_SUPPORT_DEFINITIONS.json` | Definitions for the support-delivery schematic |
| Figure S5 | `paper/data/supplement/policy_accounts/` | Public/recipient payment reconciliation |
| Figure S6 | `paper/data/controls/ENTRY_CALIBRATED_SUPPORT.csv` | Support calibrated relative to each route's entry threshold |
| Tables 1–3 and S1–S13 | `paper/data/tables/` | CSV and JSON exports retaining display rounding |
| Input evidence | `paper/data/evidence/` | 209 source-input rows, time evidence and archived monetary series |
| Original model suite | `paper/data/original_scenario_grids/` | Retained frontier grids, engineering alternatives and institutional controls |

## Fields, units and missing values

`paper/DATA_DICTIONARY.csv` defines the fields and units, and `paper/metadata/FILE_SCHEMAS.json` records exact CSV schemas. `paper/metadata/VARIABLES_AND_UNITS.csv` and `ABBREVIATIONS.csv` retain manuscript notation. CSV encoding is UTF-8, generally with a BOM for spreadsheet use; JSON uses UTF-8. Plain-text mathematical subscripts use braces, for example `E_{ir}`.

Empty CSV cells, JSON `null` and explicitly labelled `NA` mean unavailable or inapplicable, not zero. Zero allocation is represented explicitly. Ratios at zero abatement may be undefined. Full-precision computational data should be used for calculations. `data/tables/` deliberately retains rounded displayed values and is unsuitable as a numerical input replacement.

Use exact scenario fields rather than averaging across regions or grid nodes. The Figure 2c complete response has 432 rows: 404 retained original nodes plus 28 extension nodes. The S1–S2 resource-map data contain 3,224 paired gas/coal scenario rows and eight additional switching-boundary records in the joint matrix evidence. Counts refer to different objects and must not be interpreted as independent statistical samples.

## Source attribution

`paper/data/evidence/SOURCE_INPUT_LEDGER_USD.csv` identifies source URLs, page/cell locators, transformations, evidence classes and author-defined assumptions. `paper/metadata/REFERENCES.csv` preserves main-text and supplementary reference labels. Legacy E-, R- and L-prefixed identifiers retain their original identifier systems; they are not current manuscript reference numbers.

The package includes numerical extracts, author-generated results and published summary endpoints. It excludes complete third-party articles and commercial reports. Third-party rights remain with their owners. See [RIGHTS.md](../RIGHTS.md).
