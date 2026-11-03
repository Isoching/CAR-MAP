# CAR-MAP

**Carbon Allocation under Resource constraints for Mitigation Assessment and Policy**

**资源约束下的碳分配、减排评价与政策决策框架**

[English](README.md) · [复现说明](docs/REPRODUCIBILITY.md) · [数据说明](docs/DATA_GUIDE.md) · [方法与边界](docs/METHODS.md) · [参考文献](docs/REFERENCES.md)

CAR-MAP 比较捕集的工业 CO₂ 在地质封存、燃料甲醇和化学品甲醇之间的分配。在 CO₂、电力、氢气、封存接入、转化产能及预算等共同约束下，框架以相同终端服务为基础评价生命周期净减排，并以独立重新优化的仅封存组合为对照，计算允许利用路径后增加的系统减排。政策分析分别核算资源支出、私人费用、实际公共支付及补贴接收。

本仓库支持准备向 *Energy* 投稿的 Perspective：*Rethinking captured carbon allocation across storage, fuels and chemicals under resource and policy constraints*。作者为英国萨里大学 Yuanjing Zhao、Jin Xuan 和 Lei Xing。仓库版本为 **v1.0.0**，数值依据为 **2026 年 11 月 2 日 V7 源数据包**。

## 快速运行

建议使用 Python 3.12。依赖版本已固定，无须商业求解器。

```bash
git clone https://github.com/Isoching/CAR-MAP.git
cd CAR-MAP
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/reproduce.py --mode full
```

Windows 环境激活命令为 `.venv\Scripts\activate`。输出保存在 `reproduced/`，不覆盖冻结的原始结果。只运行文件校验、40 个矩阵示例及衍生账户检查，可使用 `--mode quick`。

```bash
# ARA：统一电价、天然气制常规甲醇基准；独立优化全路径与仅封存组合
python examples/run_scenario.py --region ARA --inventory 0.85

# 改为高排放煤制常规甲醇基准
python examples/run_scenario.py --region ARA --inventory 4.81 --output reproduced/ara_coal.json

# Figure 1 使用的 ARA 地区电价参考
python examples/run_scenario.py --region ARA --regional-price --output reproduced/ara_figure1.json

# 具有财政支付上限的通用 CO2 利用补贴情景
python examples/run_scenario.py --region ARA --objective private --support utilization --rate 800 --fiscal-cap 20 --output reproduced/policy.json
```

## 数据与结果的对应关系

- `paper/model/`：未经修改的工程及分配核心代码、四地区输入和货币转换记录。
- `paper/data/`：四幅主图、六幅补充图、十六张表对应的数值数据、控制实验、矩阵和证据。
- `paper/DISPLAY_DATA_MAP.csv`：图表编号到数据文件的精确映射。
- `paper/DATA_DICTIONARY.csv`：变量、字段和单位说明。
- `datasets/Energy_Source_Data_V7_20261102.zip`：与提供的 V7 附件字节一致的完整原包。
- `validation/`：本次发布实际执行的校验记录。

六个较大的文件以 `.gz` 无损压缩存储，运行入口会自动还原并核对 SHA-256；不需要 Git LFS。源数据包中的原有文件内容及校验信息保持不变。

## 必须区分的情景和核验范围

Figure 1 的数值面板采用 ARA 地区电价参考 **70.64842559228472 USD/MWh**；跨地区统一比较使用 **69.07936363636365 USD/MWh**。默认示例采用后者，`--regional-price` 采用前者。全部成本采用 **2026 年 9 月美元**。预算和财政上限的分母是固定准入源端 CO₂ 总量，不是优化后的捕集量。

完整复现会重新计算并比较 **1,700 个控制求解结果**，包括 844 对全路径／仅封存比较和 12 个私人配置校准算例。它们是确定性情景，不是统计重复。另有八类矩阵各五个示例的独立重放，以及碳留存、生产队列和财政账户检查。保存全部图表数据不等同于已重新生成所有历史网格和投稿图稿，具体覆盖范围见英文复现说明。

四地区均为结合项目资料与明确比较假设构建的 2030 年度化前瞻情景，不能直接解释为项目实际运行结果。政策模块中的通用机制和历史制度控制也不构成项目合规认定。

参考文献、软件来源和地区项目链接见 [REFERENCES.md](docs/REFERENCES.md)。使用时请注明 CAR-MAP 版本及 V7 数据版本。代码与使用文档采用 [MIT](LICENSE)，作者生成的数据采用 [CC BY 4.0](LICENSE-DATA.txt)，第三方资料保留原权利；具体范围见 [RIGHTS.md](RIGHTS.md)。
