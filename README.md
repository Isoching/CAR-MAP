# CAR-MAP

**Carbon Allocation under Resource constraints for Mitigation Assessment and Policy**

资源约束下的碳分配、减排评价与政策决策框架

[中文说明](README.zh-CN.md) · [Reproduction guide](docs/REPRODUCIBILITY.md) · [Data guide](docs/DATA_GUIDE.md) · [Methods](docs/METHODS.md) · [References](docs/REFERENCES.md)

CAR-MAP evaluates how captured industrial CO₂ should be allocated among geological storage, fuel methanol and chemical methanol when carbon, electricity, hydrogen, storage access and expenditure compete. It compares portfolios supplying the **same final services**, calculates **net lifecycle abatement**, and measures the additional mitigation from allowing utilisation relative to an **independently reoptimised storage-only portfolio**. Its policy experiments distinguish resource expenditure, private expense, public outlay and support received.

This repository provides the numerical kernels and source data supporting *Rethinking captured carbon allocation across storage, fuels and chemicals under resource and policy constraints*, a Perspective prepared for submission to **Energy** by **Yuanjing Zhao, Jin Xuan and Lei Xing**, University of Surrey. The repository release is **v1.0.0**, based on the **V7 numerical source-data attachment dated 2 November 2026**. No article DOI has been assigned in this record.

## What the framework does

| Component | Question addressed |
|---|---|
| Carbon allocation under resource constraints | How do source treatment, electricity, hydrogen, storage connections, conversion capacity and spending limit the feasible portfolio? |
| Mitigation | What net lifecycle emissions are avoided after supplying the same fuel and chemical services and accounting for eventual product-carbon release? |
| Assessment | Does utilisation add mitigation relative to the best storage-only portfolio under matching conditions? |
| Policy | How do payment objects, qualification, realisation, pass-through and fiscal ceilings affect private allocation and policy rankings? |

The prospective annualised 2030 settings are Amsterdam–Rotterdam–Antwerp (**ARA**), Teesside–Endurance (**UK**), the **US Gulf Coast**, and **Yulin, China (CN)**. They combine project evidence with declared comparison assumptions. They are deterministic model scenarios; they do not represent observed project operation or a forecast of a regional procurement mix.

## Install and reproduce

Use **Python 3.12**. The recorded numerical environment uses NumPy 1.26.4, SciPy 1.13.1, CoolProp 8.0.0 and openpyxl 3.1.5. SciPy supplies the HiGHS LP interface; no separate commercial solver is required.

```bash
git clone https://github.com/Isoching/CAR-MAP.git
cd CAR-MAP
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/reproduce.py --mode full
```

On Windows, activate the environment with `.venv\Scripts\activate`. Run commands from the repository root. The runner restores the six losslessly compressed files, checks the frozen payload, replays 40 matrix examples, reconstructs derived accounts, **regenerates all 1,700 V7 control solutions**, compares them with the retained results and rebuilds the control matrices. Fresh outputs go to `reproduced/`; the frozen source data remain unchanged. A smaller check is available with `--mode quick`.

```bash
# Independently optimise both portfolios under the ARA common gas reference.
python examples/run_scenario.py --region ARA --inventory 0.85

# Change the displaced methanol inventory to the high-coal reference.
python examples/run_scenario.py --region ARA --inventory 4.81 --output reproduced/ara_coal.json

# Use the ARA regional electricity price underlying Figure 1.
python examples/run_scenario.py --region ARA --regional-price --output reproduced/ara_figure1.json

# Private allocation under a generic CO2-use payment and a fiscal ceiling.
python examples/run_scenario.py --region ARA --objective private --support utilization --rate 800 --fiscal-cap 20 --output reproduced/policy.json
```

The default example uses the **common electricity price of 69.07936363636365 USD/MWh**. Figure 1 instead uses the **ARA regional reference of 70.64842559228472 USD/MWh**. Keeping this distinction is necessary to reproduce the two sets of results. Costs use **September 2026 USD**; `--budget` and `--fiscal-cap` are normalised by the fixed admitted source cohort, not by the optimised captured quantity. Hydrogen-support rates use USD/tH₂; other example support rates use USD/t eligible CO₂-feed equivalent.

## Code and datasets

| Location | Contents |
|---|---|
| [`paper/model/allocation.py`](paper/model/allocation.py) | LP construction, lexicographic optimisation, matched-service backfills and reconciled carbon/financial accounts |
| [`paper/model/engineering.py`](paper/model/engineering.py) | Source treatment, real-fluid compression, methanol utilities, annualisation and monetary conversions |
| [`paper/model/inputs/`](paper/model/inputs/) | Four regional engineering snapshots |
| [`paper/code/`](paper/code/) | Original portable control generation, matrix reconstruction, replay and verification scripts |
| [`paper/data/`](paper/data/) | Main/supplementary figure data, controls, evidence extracts and full-precision saved optimisation records |
| [`paper/DISPLAY_DATA_MAP.csv`](paper/DISPLAY_DATA_MAP.csv) | Exact file crosswalk for four main figures, six supplementary figures and sixteen tables |
| [`paper/DATA_DICTIONARY.csv`](paper/DATA_DICTIONARY.csv) | CSV field definitions and units |
| [`datasets/Energy_Source_Data_V7_20261102.zip`](datasets/Energy_Source_Data_V7_20261102.zip) | Byte-identical original V7 attachment: 186 files, with its original manifest and checksums |
| [`PACKAGING.json`](PACKAGING.json) | Original ZIP hash and hashes of the six gzip storage transformations |
| [`validation/`](validation/) | Checks produced for this repository release; see the [validation record](validation/README.md) |

For a standard-library-only integrity check, run `python scripts/prepare_data.py`, followed by `python paper/code/validate_archive.py`. The large JSON/CSV files use ordinary gzip compression to keep Git downloads manageable; preparation restores their original bytes. Git LFS and external dataset downloads are unnecessary.

## Reproduction coverage and interpretation

The full runner regenerates **844 paired scenarios (1,688 LP allocations) and 12 private-allocation calibration cases**. These are 1,700 deterministic allocations, not statistical replicates. Matrix replay covers five fixed examples from each of eight matrix families. That sampled check is distinct from the complete control regeneration. The repository preserves source data for all current displays; the runner does not regenerate every original figure grid or the publication artwork. See [coverage and expected results](docs/REPRODUCIBILITY.md).

The storage comparator is separately optimised with utilisation disabled. Product-carbon cycling is distinguished from geological retention. Future changes to source specifications, electricity supply, conventional methanol inventories or policy conditions define new scenarios and should be reported as such. See [model boundaries](docs/METHODS.md).

## References and citation

The methodological background includes the [CCU lifecycle-assessment guideline](https://doi.org/10.3389/fenrg.2020.00015) and [CCU techno-economic assessment guidelines](https://doi.org/10.3389/fenrg.2020.00005). The implementation uses [SciPy `linprog`](https://docs.scipy.org/doc/scipy-1.13.1/reference/generated/scipy.optimize.linprog.html), [HiGHS](https://highs.dev/) and [CoolProp](https://coolprop.org/citation.html). The [reference guide](docs/REFERENCES.md) links the scientific background, regional anchors and software citations. The [complete reference export](paper/metadata/REFERENCES.csv) and [209-row input evidence ledger](paper/data/evidence/SOURCE_INPUT_LEDGER_USD.csv) retain source URLs and locators.

Please cite the software version and the V7 dataset version when using this release. [`CITATION.cff`](CITATION.cff) supplies machine-readable software citation metadata. The article citation can be added when a publication identifier is available. [Data and code availability wording](docs/AVAILABILITY.md) is supplied for submission.

## Rights

Code and reproduction documentation are licensed under [MIT](LICENSE). Author-generated simulation data and numerical records are licensed under [CC BY 4.0](LICENSE-DATA.txt). Third-party material retains its original rights; see [RIGHTS.md](RIGHTS.md) for scope and attribution. The frozen V7 metadata are preserved as historical records. Full third-party publications, commercial reports, manuscripts, browser caches and local environments are not part of the repository payload.
