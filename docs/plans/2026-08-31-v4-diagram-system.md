# V4 Diagram System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 建立职责明确、共享同一户型底图、可重复生成的六张 v4 装修 SVG。

**Architecture:** 使用一个纯 Python 生成器维护公共坐标、墙体、房间底色、门窗和 SVG 样式；六个渲染函数只添加各自专业图层。生成物写入 `diagrams/v4/`，历史 v2/v3 图移入 archive。所有 SVG 由现有校验器解析，并增加针对文件集合、标题和关键图层的单元测试。

**Tech Stack:** Python 3 标准库、SVG/XML、Ruby YAML 校验、Make、Git。

---

### Task 1: 固化六张图的职责

**Files:**
- Create: `diagrams/v4/README.md`
- Modify: `README.md`

**Step 1:** 写明六张图各自回答的问题和禁止出现的信息。

**Step 2:** 规定总体图不画会挡住通道的待定卫生间移门；门窗图用局部详图表达定制约束。

**Step 3:** 提交：`设计(图纸): 固化v4六图职责`

### Task 2: 为生成器编写失败测试

**Files:**
- Create: `tests/test_generate_diagrams.py`

**Step 1:** 测试生成结果必须包含六个指定文件。

**Step 2:** 测试每个 SVG 的标题、用途说明和根元素可解析。

**Step 3:** 测试卫生间移门不在家具/动线图中以开启门扇占据走廊。

**Step 4:** 运行：`python3 -m unittest tests/test_generate_diagrams.py -v`

**Expected:** 在生成器不存在时失败。

### Task 3: 实现公共 SVG 底图

**Files:**
- Create: `scripts/generate_diagrams.py`

**Step 1:** 实现坐标换算、SVG 文档、墙体、房间、窗户、标签和图例助手。

**Step 2:** 实现 `generate_all(output_dir)`，先输出六个最小可解析文档。

**Step 3:** 运行单元测试，确认文件集合和 XML 测试通过。

### Task 4: 实现六个专业图层

**Files:**
- Modify: `scripts/generate_diagrams.py`

**Step 1:** `00-existing-survey.svg`：墙体、洞口、窗户、固定点位与已拆门状态。

**Step 2:** `10-furniture-circulation.svg`：家具、家电、采购状态和通行净宽；不画挡路门扇。

**Step 3:** `20-plumbing-gas.svg`：冷热水、排水、地漏、马桶坑位、燃气灶/热水器两支路。

**Step 4:** `30-electrical-low-voltage.svg`：配电箱、暗盒、穿墙洞、空调、浴霸、网线、光猫和 Wi-Fi。

**Step 5:** `40-doors-windows-cats.svg`：门窗采购状态、防猫纱窗、猫抓板及移门定制局部说明。

**Step 6:** `50-kitchen-bath-details.svg`：厨房台面立面与卫生间放大图，显示关键尺寸和安全待核验项。

### Task 5: 接入仓库命令和校验

**Files:**
- Modify: `Makefile`
- Modify: `scripts/check_project.py`
- Modify: `README.md`

**Step 1:** 增加 `make diagrams` 和 `make test`。

**Step 2:** 把六个 v4 文件列为必需文件。

**Step 3:** 运行：`make diagrams && make test && make check`。

**Expected:** 六张 SVG 生成成功；单元测试、YAML 引用、账本和 XML 全部通过。

### Task 6: 视觉检查并提交

**Files:**
- Generate: `diagrams/v4/*.svg`
- Move: `diagrams/house-plan-v2-framework.svg`、`diagrams/house-plan-v3-*.svg` 到 `diagrams/archive/`

**Step 1:** 渲染六张本地预览，检查遮挡、比例、图例和职责越界。

**Step 2:** 修正发现的问题后重新生成和校验。

**Step 3:** 提交：`设计(图纸): 生成v4六类专业图`
