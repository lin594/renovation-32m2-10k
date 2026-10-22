# 房间详图与下一步行动指南 Implementation Plan

**Goal:** 修复跨平台 CI，撤销厨房架空瓷砖层，并把水气、电气、阳台、门和瓷砖改色深化成可继续校对的房间级图纸与行动清单。

**Architecture:** `house.yaml` 与 `data/*.yaml` 继续作为事实真源；`scripts/generate_diagrams.py` 生成按六系列编号的现行 SVG；`data/project.yaml#next_actions` 作为后续行动单一真源，由 `scripts/generate_actions.rb` 生成 `NEXT_ACTIONS.md`。房间图把已确认事实、建议点位、TBD 和安全门禁分层显示，不把建议点位写成已施工事实。

**Tech Stack:** YAML、Ruby 状态生成器、Python SVG/Markdown 生成器、`unittest`、GitHub Actions。

---

### Task 1: 修复跨平台 CI 确定性

**Files:**
- Modify: `scripts/generate_status.rb`
- Create: `tests/test_generate_status.py`

**Step 1: 写失败测试**

读取 `data/ledger.csv` 计算分类金额，断言 `PROJECT_STATUS.md` 中的分类顺序严格按“金额降序、分类名升序”排列，覆盖 `plumbing` 与 `windows` 同为 500 元的情况。

**Step 2: 验证失败根因**

以 GitHub Actions 运行 `37482261601` 为证据：Linux 生成结果把 `plumbing` 放在 `windows` 前，而已提交文件相反。

**Step 3: 最小修复**

把状态生成器排序改为确定性复合键：`[-amount, category]`。

**Step 4: 验证**

运行 `make status && python3 -m unittest discover -s tests -p 'test_generate_status.py' -v`，预期通过且 `git diff -- PROJECT_STATUS.md` 仅包含稳定顺序修正。

### Task 2: 更新空间、材料与方案真源

**Files:**
- Modify: `house.yaml`
- Modify: `data/project.yaml`
- Modify: `data/procurement.yaml`
- Modify: `data/finishes.yaml`
- Modify: `data/risks.yaml`
- Modify: `data/schedule.yaml`
- Modify: `data/electrical.yaml`

**Step 1: 删除架空瓷砖层**

从当前布局、燃气遮蔽、承重风险、待购方案和开放问题中删除或标记 `cancelled_by_owner_2026_10_07`；保留历史文档，不改写历史事实。

**Step 2: 更新门窗**

记录厨房窗与客厅、卧室窗同尺寸，但精确洞口数值仍待实测；厨房窗继续保持固定封闭、无纱窗。卧室门改为本阶段不做；厨房门和卫生间门改为阳光板候选，轨道、框料、厚度和防潮仍待确认。

**Step 3: 更新阳台与瓷砖改色**

阳台采用 30×30cm 拼接格栅/菠萝格地板候选，保留排水缝与可掀开清洁条件；周边墙面暂定猫抓板贴纸。厨卫瓷砖改色进入“小样—验收—再采购”规划，不直接下单全量材料。

**Step 4: 更新电气中文名**

给九个机器节点 ID 增加中文短号和中文名称，保留旧 ID 作为跨文件引用键。

**Step 5: 验证**

运行 `ruby scripts/check_yaml.rb`；确认当前真源中不存在仍为 planned/todo 的架空瓷砖层。

### Task 3: 展开水气房间详图

**Files:**
- Modify: `scripts/generate_diagrams.py`
- Modify: `tests/test_generate_diagrams.py`
- Modify: `scripts/check_project.py`
- Modify: `diagrams/README.md`
- Generate: `diagrams/11-kitchen-water-gas-elevations.svg`
- Generate: `diagrams/12-bathroom-water-elevations.svg`

**Step 1: 先写输出与语义测试**

测试 11 图包含水槽冷水分支、洗碗机独立止水、软管直排水槽、堵塞状态及检修边界；12 图包含马桶、淋浴、浴室柜已确认冷水及热水/排水TBD、地漏、立管和整体找坡关系。

**Step 2: 实现 11 厨房水气详图**

显示既有水槽、洗碗机建议位置、从水槽进水支路牵引到洗碗机的冷水管和独立阀、排水软管抬高固定后直排水槽；不把尚未实测的管径和标高写死。

**Step 3: 实现 12 卫生间水气详图**

显示入户冷水、热水器回水、马桶冷水、淋浴冷热水、浴室柜已确认冷水接口、地漏与西北排水立管；浴室柜热水和排水路径必须标为 TBD，并注明完成面尺寸、坡度和设备接口仍须复测。

**Step 4: 验证**

运行 `make diagrams` 与图纸测试；解析所有 SVG XML。

### Task 4: 展开中文友好电气房间图

**Files:**
- Modify: `scripts/generate_diagrams.py`
- Modify: `tests/test_generate_diagrams.py`
- Modify: `scripts/check_project.py`
- Modify: `diagrams/README.md`
- Generate: `diagrams/21-kitchen-electrical.svg`
- Generate: `diagrams/22-bathroom-electrical.svg`
- Generate: `diagrams/23-living-electrical.svg`
- Generate: `diagrams/24-bedroom-electrical.svg`
- Generate: `diagrams/26-hall-electrical.svg`
- Update: `diagrams/20-electrical-overview.svg`
- Update: `diagrams/27-electrical-nodes.svg`

**Step 1: 先写图纸清单和中文节点测试**

断言各图存在、主节点优先显示 `卧01/厨01/玄01/客01/卫01` 等中文短号，并保留括号内旧 ID；房间图必须含“建议点位/TBD/未施工”和对应安全门禁。

**Step 2: 生成厨房、卫生间图**

厨房显示基础灯、门边开关、洗碗机、台面电器、油烟机和热水器点位；卫生间显示浴霸、镜柜/镜灯和基础灯，不新增通用插座，全部置于双极不大于 30mA 保护下游。

**Step 3: 生成客厅、卧室、玄关图**

客厅显示洗烘、小厨电、投影、书桌、沙发/扫地机、空调、冰箱和主灯/餐灯；卧室显示空调、床南北常电、主灯和床下灯专用点；玄关显示设备架常电、光猫/路由/EVE V 和走廊灯带。未实测高度统一标 TBD。

**Step 4: 验证**

运行图纸单测，人工渲染关键 SVG，检查文字重叠、越界和错误状态。

### Task 5: 建立下一步行动指南

**Files:**
- Modify: `data/project.yaml`
- Create: `scripts/generate_actions.rb`
- Create: `NEXT_ACTIONS.md`
- Modify: `Makefile`
- Modify: `.github/workflows/project.yml`
- Modify: `scripts/check_project.py`
- Create: `tests/test_generate_actions.py`
- Modify: `README.md`

**Step 1: 建立行动数据**

在 `data/project.yaml#next_actions` 中登记优先级、领域、房间、状态、动作、完成标准、依赖/阻断和证据要求。首版覆盖厨房疏通及洗碗机水路、房间电气放样与专业验收、瓷砖改色小样、阳台地面/墙贴、阳光板厨卫门、卧室门延期和1月涂装/环氧收口。

**Step 2: 写生成器与测试**

按 `P0 → P1 → P2 → ID` 稳定排序，分“安全门禁、现在可细化、等待采购/复测、延期”输出；测试确定性和关键动作存在。

**Step 3: 接入本地与 CI**

增加 `make actions` 和 `make generated`；CI 一次生成全部派生文件再做 `git diff --exit-code`，`make check` 校验 `NEXT_ACTIONS.md` 未过期。

**Step 4: 验证**

运行 `make generated && make check && git diff --check`，再检查派生文件无漂移。

### Task 6: 收口、视觉复核与交付

**Files:**
- Modify: `README.md`
- Modify: `PROJECT_STATUS.md`（生成）
- Modify: `diagrams/*.svg`（生成）
- Modify: `NEXT_ACTIONS.md`（生成）

**Step 1: 更新入口**

README 链接到图纸索引和下一步行动指南；项目状态突出本轮新增规划和仍未关闭的安全门禁。

**Step 2: 全量校验**

运行 `make generated`、`make check`、`git diff --check`，并在临时目录验证所有派生文件可重建。

**Step 3: 提交与推送**

按“CI/行动体系”和“空间/图纸深化”拆分为可读提交；再次拉取远端状态，无领先时推送 `main` 并等待 Actions 通过。
