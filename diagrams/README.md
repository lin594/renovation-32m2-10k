# 现行图纸

仓库只保留当前方案。图纸编号表达职责，不表达版本；被替代的方案从 Git 历史查看。

| 编号 | 图纸 | 回答的问题 |
|---|---|---|
| 00 | [现状测量图](00-existing-survey.svg) | 房子原来有什么固定边界和点位？ |
| 10 | [家具与动线图](10-furniture-circulation.svg) | 改造后如何使用，哪些家具已有或待购？ |
| 20 | [给排水与燃气图](20-plumbing-gas.svg) | 水、排水和燃气分别如何连接？ |
| 30 | [强弱电点位图](30-electrical-low-voltage.svg) | 插座、设备、暗盒、穿线洞和网络在哪？ |
| 31 | [强电真实空间走线图](31-electrical-routes.svg) | 五回路实际从哪里经过？ |
| 32 | [五回路与分级漏保拓扑图](32-electrical-topology.svg) | 回路、分线节点和保护层如何组织？ |
| 33 | [卧室电气详图](33-bedroom-electrical-detail.svg) | 吊扇调速器与床边插座如何分开？ |
| 34 | [卫生间电气详图](34-bathroom-electrical-detail.svg) | 卫浴馈线怎样先保护再分支？ |
| 40 | [门窗与猫安全图](40-doors-windows-cats.svg) | 门扇、纱窗和三猫防逃如何处理？ |
| 50 | [厨卫详图](50-kitchen-bath-details.svg) | 小空间内的关键尺寸和冲突是什么？ |
| 60 | [墙地面饰面图](60-finishes-materials.svg) | 防水、涂装和地面材料如何分区？ |

README 的“前后对比”直接并列 00 与 10。所有图使用系统中文字体栈，由浏览器渲染；仓库不保存光栅预览。

重新生成：`make diagrams`。完整校验：`make check`。
