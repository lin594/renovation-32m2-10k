# 人类编辑指南

目标是让小修改不必理解整个仓库，也不必依赖 AI。

## 1. 记录实际收支

推荐使用命令行，它会生成 ID、保持 CSV 列顺序并刷新状态页：

```bash
python3 scripts/ledger.py expense --amount 89.90 --item "厨房排水配件" --category plumbing --room kitchen --date 2026-10-01
python3 scripts/ledger.py income --amount 120 --item "旧铁门回收" --category recycling --room whole_house --date 2026-10-01
```

可选参数：`--counterparty`、`--note`、`--payment-status`、`--project-status`。用 `--dry-run` 先预览，不写文件。

也可以直接编辑 `data/ledger.csv`。保留表头和列顺序；ID 不重复，支出使用 `EXP-四位数字`，收入使用 `INC-四位数字`；金额只写大于 0 的数字，方向由 `expense`/`income` 表示；新账日期使用 `YYYY-MM-DD`。历史八笔缺失日期允许暂时留空，不能凭猜测补录。

提交后，CI 会把错误直接标在 CSV 对应行，并说明修改方法；校验通过后再重建 `PROJECT_STATUS.md`。标准表头如下，表格软件意外改列时可据此恢复：

```csv
id,date,flow,category,room,item,counterparty,amount_cny,payment_status,project_status,note
```

## 2. 更新物资和采购

- 已经拥有、拆下后可复用或有剩余量：编辑 `data/inventory.yaml`。
- 还要购买、询价、定制、到货或验收：编辑 `data/procurement.yaml`。
- 已有物资需要配件才能安装时，设备进库存，配件包进采购，不重复把设备记成待买。

新增条目沿用当前最大 ID 的下一号，并明确 `status`。不知道的尺寸写 `null` 或 `TBD`，不要猜。

## 3. 更新空间和方案

空间、固定点位、家具和设备位置只在 `house.yaml` 维护。电气、饰面、预算、工期、风险等专业细节分别放在对应 `data/*.yaml`。改完运行：

```bash
make diagrams
make status
make check
```

## 4. 导入现场照片

HEIC 原件只保存在本地 `.local/photos-original/<日期>-<阶段>/`，公开仓库只提交去元数据后的 JPEG。安装 ImageMagick 后使用：

```bash
python3 scripts/photo.py import SOURCE \
  --date 2026-10-01 \
  --stage progress \
  --room kitchen \
  --view overview \
  --caption "厨房施工中全景" \
  --dry-run
```

确认预览信息后去掉 `--dry-run`。`stage` 只能是 `before|progress|after`；`room` 可用值为 `bedroom|kitchen|living|hall_a|hall_b|balcony|bath`；`view` 使用小写英文、数字和短横线。若画面中有可识别人像，先在 1800px 画布上确定区域，再重复传入 `--blur WxH+X+Y`。命令会自动旋转、压缩、清除元数据、登记 `data/photos.csv`、刷新图库并执行校验；重复原图、重名或失败不会留下半成品。

拍摄前后对比时，尽量站在同一门口、保持相近焦段和方向。全景用于展示空间变化，管线、基层和收口另拍细节，不用效果图代替完工实景。

## 5. 哪些文件不要手改

- `PROJECT_STATUS.md`：由 `make status` 生成。
- `diagrams/*.svg`：由 `make diagrams` 生成。
- `media/photos/README.md`：由 `make gallery` 生成；照片说明和阶段修改 `data/photos.csv`。
- 旧图纸副本：不再保存；需要时使用 `git log`、`git show` 或 GitHub 历史。

## 6. 提交格式

```text
<类型>(<范围>): <中文摘要>
```

例如：`记账(厨房): 录入洗碗机接管配件`、`更新(客厅): 调整沙发床展开净空`。
