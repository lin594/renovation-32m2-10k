# 32㎡二手房翻新：1万元、三只猫与一套可执行方案

[![项目校验](https://github.com/lin594/renovation-32m2-10k/actions/workflows/project.yml/badge.svg)](https://github.com/lin594/renovation-32m2-10k/actions/workflows/project.yml)

这是一个位于开封的 32㎡ 老房翻新实录。业主既是策划人，也是主要 DIY 执行者；目标是在约 ¥10,000 总预算内，把一室一厅一厨一卫改到三只猫可以安全入住，并尽量只进行一次北京—开封装修专项往返。

仓库同时服务两类读者：人可以从本页、图纸和状态页快速理解方案；程序和 AI 可以从结构化数据中校验账目、采购、工期、风险和空间冲突。

## 先看总体与重点空间

| 全屋协调：边界、布局与动线 | 厨房协调：设备、柜体与接口 |
|---|---|
| [![全屋协调总图](diagrams/00-overall-coordination.svg)](diagrams/00-overall-coordination.svg) | [![厨房协调图](diagrams/01-kitchen-coordination.svg)](diagrams/01-kitchen-coordination.svg) |

目标方案的核心变化包括：拆除四扇旧门、全屋明装电路、卫生间蹲厕改马桶、厨卫与墙地面低成本翻新、防猫纱窗、客厅沙发床临时客卧、玄关家庭中枢，以及在厨房西侧复用现有洗碗机。

图纸直接使用 SVG；中文由浏览器字体渲染，不再提交缺少中文字形、无法阅读的 PNG 预览。当前仓库只保留一套现行图纸，旧方案通过 Git 历史查看。

真实现场的装修前与施工中记录见 [现场照片档案](media/photos/README.md)。首页不直接加载照片，避免影响首次阅读；图库会按房间明确标出尚未拍摄的施工中或完工阶段。

## 当前状态

- 施工状态：2026-09-28～10-04 双人主窗口已结束；实际完成乳胶漆一底一面。明装电气、SPC、家电更换和原计划第二遍面漆未完成，转入后续收尾。
- 采购变化：电线、插座和若干施工材料已购；两只智能开关因物流时效退货、当前手头为0。卫生间原自铺地砖方案取消，闭水试验通过后已铺2组×1.4kg环氧地坪，1月拟再购5kg增厚；跨月复涂、排水和防滑仍待核验。
- 厨房下水漏点已修复，但随后疑似堵塞；2500ml管道疏通剂未改善，计划2027年1月定位后机械疏通或拆检。京东流水中同容量商品名为多功能清洁剂，两者是否同一件仍待确认。
- 安全边界：老小区户内已确认只有 L/N、无可用 PE；采用分级漏保降低风险，但不把漏保写成接地替代。
- 入住门槛：三猫理想入住日 2027-01-15，硬截止 2027-02-07；防猫、地面、固化、用电和保洁任一项未通过就延期。
- 资金、任务和采购的实时汇总见 [PROJECT_STATUS.md](PROJECT_STATUS.md)；可执行顺序和验收证据见 [下一步行动指南](NEXT_ACTIONS.md)。
- 现行图纸职责见 [diagrams/README.md](diagrams/README.md)。水气以 [10 全屋系统图](diagrams/10-water-gas-overview.svg) 为入口，厨房/卫生间分别看 [11](diagrams/11-kitchen-water-gas-elevations.svg) 与 [12](diagrams/12-bathroom-water-elevations.svg)；电气以 [20 全屋路线总图](diagrams/20-electrical-overview.svg) 为入口，按 21–24/26 展开房间点位，再以 [27 节点与材料专项](diagrams/27-electrical-nodes.svg) 核对端子和材料。
- 重要方案的现行/已替代关系见 [决策记录索引](docs/decisions/README.md)。
- 本轮整合与一次性答复入口：[2026-09-30 多渠道核对及待确认清单](docs/reviews/2026-09-30-channel-reconciliation.md)。当前为整合稿，未决事项不等于施工已批准。

## 最容易修改的入口

| 要更新什么 | 修改哪里 |
|---|---|
| 新增支出或收入 | 推荐运行 `python3 scripts/ledger.py expense ...`；也可直接编辑 `data/ledger.csv` |
| 户型、固定点位、家具布局 | `house.yaml` |
| 已有物资与余料 | `data/inventory.yaml` |
| 待购、询价、下单、到货 | `data/procurement.yaml` |
| 阶段和任务 | `data/project.yaml` |
| 工期与入住门槛 | `data/schedule.yaml` |
| 风险与安全门禁 | `data/risks.yaml` |
| 下一步行动、优先级与验收证据 | `data/project.yaml#next_actions`（运行 `make actions` 生成阅读页） |
| 新增现场照片 | `python3 scripts/photo.py import ...`；目录为 `data/photos.csv` |

完整字段说明和示例见 [人类编辑指南](docs/editing-guide.md)。`PROJECT_STATUS.md`、`NEXT_ACTIONS.md` 和 SVG 都是派生文件，不应手改。

## 记一笔账

```bash
python3 scripts/ledger.py expense \
  --amount 89.90 \
  --item "厨房排水配件" \
  --category plumbing \
  --room kitchen \
  --date 2026-10-01
```

命令会自动生成下一条 ID、追加 CSV 并刷新公开状态页。若直接在 GitHub 上编辑 CSV，主分支 CI 会重新计算状态页并由机器人提交；原始账本不会被 CI 改写。

## 本地校验

```bash
make status     # 从账本和 YAML 生成 PROJECT_STATUS.md
make actions    # 从项目任务生成 NEXT_ACTIONS.md
make diagrams   # 从生成器重建现行 SVG
make gallery    # 从照片目录重建按房间图库
make generated  # 重建以上全部派生文件
make check      # 数据、引用、预算、照片、图纸和测试的完整校验
```

## 数据设计

`data/ledger.csv` 是实际收支唯一真源，`data/budget.yaml` 只保存预算上限和预留规则；剩余金额由脚本实时计算，不在多个文件手抄。空间事实以 `house.yaml` 为准，专业方案以 `data/*.yaml` 为准，重要取舍保存在 `docs/decisions/`，历史变化交给 Git。

SVG 是讨论图，不代替现场复测、电气施工图、燃气验收或防水验收。

## 公开互动与版权

欢迎通过 [GitHub Issues](https://github.com/lin594/renovation-32m2-10k/issues) 提出建议；本仓库不主动征集 Pull Request。仓库未采用开源许可证，代码、文档、图纸和公开照片的权利边界见 [COPYRIGHT](COPYRIGHT)。
