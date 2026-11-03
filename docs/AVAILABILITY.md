# Submission availability text

## Data availability

The numerical source data supporting this study are available in the CAR-MAP repository at https://github.com/Isoching/CAR-MAP, release v1.0.0. The repository includes the V7 source-data attachment dated 2 November 2026, full-precision scenario results, saved linear-programming models, input evidence and monetary-conversion records, data dictionaries, and a crosswalk linking files to the main and supplementary figures and tables. Author-generated data are licensed under CC BY 4.0; third-party material retains its original rights. Original third-party sources are identified in the input evidence ledger and reference export. Published geological-retention endpoints are supplied as summary evidence; the source study's underlying Monte Carlo draws are not included.

## Code availability

The engineering and carbon-allocation kernels, declared regional inputs, control-calculation scripts and reproduction instructions are available under the MIT License in CAR-MAP release v1.0.0 at https://github.com/Isoching/CAR-MAP. The retained environment uses Python 3.12, NumPy 1.26.4, SciPy 1.13.1, CoolProp 8.0.0 and openpyxl 3.1.5. The reproduction runner regenerates and compares all 1,700 V7 control allocations, performs sampled replay across eight saved-matrix families and checks derived carbon and financial accounts. Its scope and verification reports are documented in the repository.

## Version identification

Use the immutable `v1.0.0` tag or the corresponding commit when citing the submission version. `CITATION.cff` supplies the software authors and release metadata. No repository DOI or article DOI is claimed. A future archival DOI may be added only after a persistent repository record has actually been deposited and assigned an identifier.

## 中文核对

- 当前数值版本为 2026 年 11 月 2 日 V7，仓库发布版本为 v1.0.0。
- 代码完整重跑范围为 1,700 个控制配置；八类矩阵重放为明确标注的 40 个示例。
- 图表数据已保存；完整重跑入口不重新生成所有历史网格与投稿图稿。
- 代码与文档采用 MIT，作者生成数据采用 CC BY 4.0；第三方权利及冻结元数据说明见 RIGHTS.md。
- 本文档不声称已有 DOI。GitHub 版本链接与持久归档 DOI 是不同标识。
