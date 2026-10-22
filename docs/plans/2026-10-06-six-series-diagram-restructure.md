# 六系列图册重构 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将现行 SVG 重构为“整体、水气、电气、瓦作、涂装、木作”六个二字系列，使图号稳定、职责单一，并与十月收口后的账目和项目事实同步。

**Architecture:** 图号第一位固定表示系列，第二位固定表示空间或图纸用途：`X0` 全屋总图，`X1` 厨房，`X2` 卫生间，`X3` 客厅，`X4` 卧室，`X5` 阳台，`X6` 玄关/走廊，`X7` 通用节点或专项，`X8` 表，`X9` 验收。只生成当前有信息价值的图；整体图负责空间协调，专业图负责本专业做法，跨专业信息仅保留接口和参见关系。

**Tech Stack:** Python 3 SVG 字符串生成器、Ruby/Python 数据校验、YAML/CSV 主数据、`unittest`、Make。

---

## 设计边界

| 系列 | 范围 | 不承载 |
|---|---|---|
| `0X 整体` | 现状边界、全屋布局、动线、房间协调、门窗与猫安全 | 完整管线路由、接线、材料施工层次 |
| `1X 水气` | 给水、热水、排水、燃气、热水器与油烟机排烟 | 电气保护、地面防水层次 |
| `2X 电气` | 回路、墙面路径、节点、灯控、弱电、保护与材料 | 给排水和饰面做法 |
| `3X 瓦作` | 基层、防水、找坡、闭水、硬质地面、SPC与收边 | 乳胶漆遍数和电气端接 |
| `4X 涂装` | 墙固、底漆、面漆、瓷砖改色、环氧与木器涂层 | 防水验收替代、木作承重 |
| `5X 木作` | 柜体、台面支撑、家具、门扇、轨道、窗框和纱窗构造 | 门洞尺寸真源、管线与接线 |

同一事实只设一个图纸主责。例如：卫生间移门洞口与开启净空由整体图负责，门扇/轨道构造由木作图负责；卫生间环氧的涂层状态由涂装图负责，防水基层与闭水由瓦作图负责。

### Task 1: 先冻结输出清单与职责测试

**Files:**
- Modify: `tests/test_generate_diagrams.py`
- Modify: `scripts/check_project.py`

**Step 1: 写失败测试**

将 `EXPECTED` 改为新图号，新增职责边界断言：整体厨房图不得出现完整电气端接；水气总图必须出现厨房堵塞状态；涂装图必须出现“一底一面”和1月补刷；旧文件名不得留在 `diagrams/`。

**Step 2: 运行测试确认失败**

Run: `python3 -m unittest tests.test_generate_diagrams -v`

Expected: FAIL，提示新 SVG 尚未生成或输出清单不匹配。

### Task 2: 重构 SVG 生成器

**Files:**
- Modify: `scripts/generate_diagrams.py`
- Delete via generator cleanup: `diagrams/40-doors-windows-cats.svg`
- Delete via generator cleanup: `diagrams/50-kitchen-bath-details.svg`
- Create: new numbered files under `diagrams/`

**Step 1: 提取可复用底图和统一页脚**

统一显示系列、图号、图纸属性、更新日期、上游真源、关联图和 `TBD` 说明。

**Step 2: 实现六系列当前图纸**

生成全屋协调、厨房/卫生间协调、水气系统、电气路线/节点、瓦作分区、涂装分区、木作与门窗等当前必要图；不为预留号创建空 SVG。

**Step 3: 重建图纸**

Run: `make diagrams`

Expected: `diagrams/` 只含新清单中的现行图纸。

### Task 3: 同步索引和引用

**Files:**
- Modify: `diagrams/README.md`
- Modify: `README.md`
- Modify: `docs/decisions/0011-five-route-electrical-freeze.md`
- Modify: `docs/plans/2026-09-29-five-route-electrical-plan.md`
- Modify: `docs/plans/2026-09-30-final-surface-electrical-plan.md`
- Modify: `docs/plans/2026-09-30-electrical-node-and-takeoff.md`

**Step 1: 更新图纸目录和编号规则**

写明六系列、尾号语义、当前已生成图、预留图号和唯一主责规则。

**Step 2: 原子更新所有 SVG 链接**

Run: `rg -n 'diagrams/.*\.svg|[0-9]{2} .*图' README.md diagrams docs scripts tests`

Expected: 不再存在指向已删除图名的现行引用；历史快照中的旧文字明确为历史。

### Task 4: 验证账目和项目状态未被图册重构遗漏

**Files:**
- Verify: `data/ledger.csv`
- Verify: `house.yaml`
- Verify: `data/*.yaml`
- Regenerate: `PROJECT_STATUS.md`

**Step 1: 核对十月事实**

确认一底一面/400元、角落粗糙及1月DIY；环氧2×1.4kg已铺并拟增购5kg；厨房漏点修复后堵塞；纱窗尾款300元付清；智能开关退货；厨房与门窗实测均已落盘。

**Step 2: 核对账目**

使用 `artifact_tool` 导入最终 CSV，抽查新增区间并交叉核对项目脚本汇总。

### Task 5: 全量验证与提交

**Files:**
- Verify: all changed files

**Step 1: 运行全量校验**

Run: `make check`

Expected: YAML、引用、账目、SVG/XML和全部单元测试通过。

**Step 2: 视觉检查关键图**

渲染整体、水气、厨房/卫生间、涂装图，确认无明显遮挡、越界或错误状态。

**Step 3: 提交并推送**

按仓库提交规范分别提交项目收口数据和图册重构；确认远端无领先后推送 `main`。
