# 32㎡二手房翻新项目

这是从二手房购入、拆旧、设计、采购、施工、验收到最终入住的全流程项目仓库。业主同时是实际策划人；仓库用于保存事实、方案、预算、采购、工期、风险和决策历史。

## 当前目标

- 在不改墙体和结构的前提下完成一室一厅一厨一卫及转角阳台翻新。
- 优先低成本和高性价比，同时守住燃气、强电、防水、排烟和宠物安全底线。
- 所有已确认事实、计划、TODO 和风险分开记录，避免把设想误当成施工依据。

## 仓库结构

```text
.
├── house.yaml              # 户型、点位、家具和现场事实的主数据
├── data/
│   ├── ledger.csv          # 所有支出、收入、退款和待收款
│   ├── budget.yaml         # 总预算和分类预算目标
│   ├── project.yaml        # 阶段、任务和项目状态
│   ├── inventory.yaml      # 已有材料、余料和可复用物品
│   └── risks.yaml          # 安全、质量、成本和工期风险
├── diagrams/               # 当前分层 SVG 图纸
│   └── archive/            # 已被替代但需要保留的历史图纸
├── docs/
│   ├── decisions/          # 类 ADR 的装修决策记录
│   └── plans/              # 设计与实施计划
├── scripts/                # 校验和汇总工具
└── artifacts/previews/     # 可再生成的本地预览，不纳入 Git
```

## 使用方式

```bash
make check      # 校验必需文件、CSV 金额和 SVG/XML
make summary    # 输出当前收支摘要
git log --oneline --decorate
```

## Git 工作流

小而明确的更新直接提交到 `main`；存在多个备选方案或会大幅改图时使用 `design/<topic>` 分支。提交格式：

```text
<类型>(<范围>): <中文摘要>
```

常用类型：`建档`、`更新`、`修正`、`设计`、`记账`、`采购`、`进度`、`风险`、`规范`、`文档`、`维护`。类型、范围和摘要优先使用中文；范围通常是房间或领域，如 `卫生间`、`厨房`、`弱电`、`预算`。

示例：

```text
记账(强电): 录入入户线及配电箱费用
修正(厨房): 更新台面深度与燃气管走向
风险(卫生间): 登记浴霸触水与无地线问题
```

## 数据规则

| 信息 | 唯一真源 |
|---|---|
| 空间、门窗、固定点位 | `house.yaml` |
| 实际收支 | `data/ledger.csv` |
| 总预算和分类目标 | `data/budget.yaml` |
| 材料余量 | `data/inventory.yaml` |
| 阶段和任务 | `data/project.yaml` |
| 风险及处置状态 | `data/risks.yaml` |
| 方案取舍原因 | `docs/decisions/` |

SVG 是用于讨论的派生图纸，不代替现场复测、燃气验收或电气施工图。

当前图纸：

- `diagrams/house-plan-v2-framework.svg`：空间框架与门窗；
- `diagrams/house-plan-v3-furniture.svg`：家具、厨房台面与阳台设施；
- `diagrams/house-plan-v3-services.svg`：燃气、电气、空调、浴霸和穿墙点位。
