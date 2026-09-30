# 图纸索引

所有SVG均由 `scripts/generate_diagrams.py` 生成，执行 `make diagrams` 可重建。

| 编号 | 图纸 | 用途 |
|---|---|---|
| 00 | [现状测量图](00-existing-survey.svg) | 固定边界和原始点位 |
| 10 | [家具与动线图](10-furniture-circulation.svg) | 家具、通道、临时客卧 |
| 20 | [给排水与燃气图](20-plumbing-gas.svg) | 水、排水、燃气 |
| **30** | [五路墙面走槽讨论图](30-five-route-electrical.svg) | 五路真实墙面路径、9主节点 |
| **31** | [九主节点接线与材料复算图](31-electrical-node-schedule.svg) | PCT选型、九节点进出线、材料 |
| 40 | [门窗与猫安全图](40-doors-windows-cats.svg) | 门窗、纱窗、防逃 |
| 50 | [厨卫详图](50-kitchen-bath-details.svg) | 厨卫尺寸和冲突 |
| 60 | [墙地面饰面图](60-finishes-materials.svg) | 防水、涂装、地面 |

2026-09-29以前30～37号强电SVG的**旧内容**已经退役，可通过Git历史追溯但不得作为现行施工依据。图号本身重新从30使用：30=现行五路路线，31=现行九主节点/材料，32～37留空。

现行文字真源为 [明装电路整合方案（待确认）](../docs/plans/2026-09-30-final-surface-electrical-plan.md) 和 [ADR 0011](../docs/decisions/0011-five-route-electrical-freeze.md)。关键语义：6mm²是前三路主干；2.5mm²是末端护套支线；全屋只编号9个主节点。
