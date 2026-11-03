# References and input sources

The full main-text and supplementary bibliography is preserved in [`paper/metadata/REFERENCES.csv`](../paper/metadata/REFERENCES.csv). Exact input values, source URLs, locators, transformations and evidence classes are recorded in the [209-row input ledger](../paper/data/evidence/SOURCE_INPUT_LEDGER_USD.csv). This guide selects the references most useful for understanding and using CAR-MAP; it does not replace that parameter-level provenance record. Bibliographic labels below follow the V7 attachment, not older draft numbering.

## Scientific and methodological background

1. **Mac Dowell N, Fennell PS, Shah N, Maitland GC (2017).** The role of CO₂ capture and utilization in mitigating climate change. *Nature Climate Change* 7, 243–249. [DOI](https://doi.org/10.1038/nclimate3231). Background for distinguishing carbon utilisation, sequestration and mitigation.
2. **Hepburn C et al. (2019).** The technological and economic prospects for CO₂ utilization and removal. *Nature* 575, 87–97. [DOI](https://doi.org/10.1038/s41586-019-1681-6). Carbon-use and removal context.
3. **Ueckerdt F et al. (2021).** Potential and risks of hydrogen-based e-fuels in climate change mitigation. *Nature Climate Change* 11, 384–393. [DOI](https://doi.org/10.1038/s41558-021-01032-7). Electricity and hydrogen opportunity costs.
4. **Müller LJ et al. (2020).** A guideline for life cycle assessment of carbon capture and utilization. *Frontiers in Energy Research* 8, 15. [DOI / open article](https://doi.org/10.3389/fenrg.2020.00015). Comparative services, boundaries and lifecycle accounting.
5. **von der Assen N, Jung J, Bardow A (2013).** Life-cycle assessment of carbon dioxide capture and utilization: avoiding the pitfalls. *Energy & Environmental Science* 6, 2721–2734. [DOI](https://doi.org/10.1039/C3EE41151F). Avoided-emissions accounting and comparison boundaries.
6. **Zimmermann AW et al. (2020).** Techno-economic assessment guidelines for CO₂ utilization. *Frontiers in Energy Research* 8, 5. [DOI / open article](https://doi.org/10.3389/fenrg.2020.00005). Transparent process and economic comparisons.
7. **González-Garay A et al. (2019).** Plant-to-planet analysis of CO₂-based methanol processes. *Energy & Environmental Science* 12, 3425–3436. [DOI](https://doi.org/10.1039/C9EE01673B). Methanol process and lifecycle context.
8. **Ravikumar D, Keoleian GA, Miller SA (2020).** The environmental opportunity cost of using renewable energy for carbon capture and utilization for methanol production. *Applied Energy* 279, 115770. [DOI](https://doi.org/10.1016/j.apenergy.2020.115770). Renewable-electricity opportunity costs.
9. **Alcalde J et al. (2018).** Estimating geological CO₂ storage security to deliver on climate mitigation. *Nature Communications* 9, 2201. [DOI / open article](https://doi.org/10.1038/s41467-018-04423-1). Source of the published retention endpoints; CAR-MAP does not redistribute or regenerate the original Monte Carlo draws.

## Engineering and regional evidence

| Source | Repository role | Link |
|---|---|---|
| Danish Energy Agency, energy carrier generation and conversion data sheets, August 2026 | Methanol/hydrogen process reference and technology inputs | [Catalogue landing page](https://ens.dk/en/analyses-and-statistics/technology-data-renewable-fuels), [workbook cited in V7](https://ens.dk/media/6444/download) |
| Porthos | ARA industrial CO₂ transport/storage project anchor | [Project](https://www.porthosco2.nl/en/project/) |
| Net Zero Teesside Power, 10 December 2024 | UK source/capture project anchor | [Project announcement](https://www.netzeroteesside.co.uk/news/greenlight-for-net-zero-teesside-power/) |
| CF Industries, 14 July 2025 | US Donaldsonville dehydration/compression and storage anchor | [Company announcement](https://www.cfindustries.com/newsroom/2025/donaldsonvilleccs) |
| Xiao J, Song S, Liu L, Bai Z (2024), *Coal Science and Technology* 52(5), 316–323 | Yulin CO₂ capture/storage case evidence | [DOI](https://doi.org/10.12438/cst.2023-0808) |
| Shell hydrogen projects | ARA hydrogen design anchor | [Project information](https://www.shell.com/what-we-do/hydrogen/shell-hydrogen-projects.html) |
| Protium, 26 September 2022 | Historical Tees Valley hydrogen design anchor | [Project announcement](https://protium.green/protiums-flagship-tees-valley-net-zero-hydrogen-project-expands-to-nearly-70mw-capacity/) |
| Yulin Chemical EPC tender, 20 August 2025 | Yulin electrolytic-hydrogen design reference | [Original Chinese tender](https://qyzb.shccmg.com/cms/default/webfile/1ywgg/20250820/1142855481363005440.html) |

These sources anchor selected model inputs. They do not independently establish all assumed methanol access, storage availability, electricity procurement or investment conditions. Use the ledger's evidence/assumption labels and original access dates; project pages can change after the numerical data freeze.

## Numerical software

- **SciPy:** `scipy.optimize.linprog`, version 1.13.1, with the HiGHS interface. [Versioned API documentation](https://docs.scipy.org/doc/scipy-1.13.1/reference/generated/scipy.optimize.linprog.html). General software citation: Virtanen P et al. (2020), SciPy 1.0: fundamental algorithms for scientific computing in Python, *Nature Methods* 17, 261–272. [DOI](https://doi.org/10.1038/s41592-019-0686-2).
- **HiGHS:** Huangfu Q, Hall JAJ (2018), Parallelizing the dual revised simplex method, *Mathematical Programming Computation* 10, 119–142. [DOI](https://doi.org/10.1007/s12532-017-0130-5), [official project and citation](https://highs.dev/).
- **CoolProp:** Bell IH, Wronski J, Quoilin S, Lemort V (2014), Pure and Pseudo-pure Fluid Thermophysical Property Evaluation and the Open-Source Thermophysical Property Library CoolProp, *Industrial & Engineering Chemistry Research* 53, 2498–2508. [DOI](https://doi.org/10.1021/ie4033999), [official citation](https://coolprop.org/citation.html).

Dependencies are installed from their own distributions; their licences remain separate from CAR-MAP. CAR-MAP citations should identify the framework release and V7 dataset, alongside the relevant methodological and software sources. This reference guide preserves supplied bibliographic details and adds official software links; it is not a new exhaustive citation audit.
