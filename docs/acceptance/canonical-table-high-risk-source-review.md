# Canonical HTML 高风险原文复核记录

## 当前结论

**PASS**。依据 2026-09-05 用户确认的“代表性产物样例通过后不再逐批审核，原文 HTML 重点审核高风险部分”策略，已完成 24/24 张高风险 canonical HTML 表的原 PDF/CHM 对照。复核覆盖 17 个文档；没有剩余需要用户裁决的语义歧义。

本轮发现并修正 5 类源树问题，共涉及 6 个正文位置；另在 7 个高风险文档中修复 105 个不配对的 `<b>` 起止标签。修改后不改变表格 ID，完整高风险集合以文档 SHA-256 钉定在 [`canonical-table-high-risk-review-registry.json`](../engineering/canonical-table-high-risk-review-registry.json)。

## 任务边界

- **TaskType**：阶段 7 高风险 canonical HTML 源表核对与错误修复。
- **Goal**：只复核会因嵌套、纵向合并、超宽结构或页码映射歧义而难以由普通机器门禁充分判断的表；消除明确的抄录、重复和标签配对错误。
- **OutOfScope**：重复要求用户验收后续批次产物；把旧版 PDF 的术语和动作模型无条件覆盖到当前规则；修改 `originFab/`；拆分或提交当前混合工作树。
- **Provides**：24 张表的精确 PDF 文件页、原 CHM 对照、源文件哈希、修复记录和全量再验证入口。
- **AcceptanceChecks**：24/24 均有来源定位；嵌套/rowspan/超宽结构可由 PDF 或 CHM 解释；明确差异已修正；当前规则的成体系语义更新未被误回退；无未决用户裁定项。

## 风险选择规则

已接受的试点表和此前直接按 PDF 修正的 12 张表优先排除，不重复复核。其余 canonical 表满足以下任一条件时进入本队列：

- 嵌套深度大于 0；
- 任一单元格 `rowspan > 1`；
- 10 列及以上；
- 有多个章节页候选，且行数乘列数至少为 80。

该规则从 369 张正文表中选出 24 张。普通表仍由 369/369 canonical、结构回归和站点 DOM 机器证据，以及已经由用户接受的站点/CHM/DOCX/PDF 代表性试点覆盖。

## 复核范围与精确来源

下表页码均指原 PDF 的文件页序号（与 `assets/pdf_pages_small/page_NNN.jpg` 一致），不是书页底部印刷页码。

| 风险组 | 表格 ID | 文档 | PDF 文件页 | 结论 |
| --- | --- | --- | --- | --- |
| 超宽 | `html-1790361cb39e` | `基本规则/等级.md` | 15 | 4×11 数值和列序一致 |
| 超宽/rowspan | `html-6d6638bed69c` | `创作指南/属性平衡.md` | 342 | PDF 可见区与 CHM 完整列共同核对；数值完整，标签配对已修复 |
| 超宽 | `html-1e9c2fc9263c`、`html-08f555e92e86` | `可选规则/等级晋升变体.md` | 110–111 | 两张表的等级、经验值、评级区间和跨页关系一致 |
| 超宽 | `html-f6958ba1b28c` | `基本规则/晋升.md` | 17 | 网格和数值一致；修复 7–8 级阶位文字 |
| rowspan | `html-d07d4e9f6624` | `心灵之光/变格之路.md` | 72 | 具现检定纵向表头和四项字段一致 |
| rowspan | `html-29399a3bb2c7` | `效果/如何使用.md` | 108 | “效果”纵向表头、箭头和三参数关系一致 |
| rowspan | `html-b85688655258` | `效果/强度表.md` | 107 | 三组纵向加值、L/E/R/P 数值一致 |
| 超宽 | `html-dbcc847c56b7`、`html-024f6ca4cb78` | `速查图表/经历与晋升一览表.md` | 118 | 两张表均与对应正文表一致；修复镜像阶位文字 |
| 页码歧义 | `html-069b29169b9a`、`html-4c04222ef893`、`html-0a1f10d22aa8` | 传闻机体强攻/堡垒/侦查型 | 166、167、168 | 由表内评级和型号消除双候选歧义；完整文本由 CHM 交叉核对，标签配对已修复 |
| 页码歧义 | `html-2790cb0afe1a`、`html-730705d7c89f`、`html-b293619bd3ca` | 怪谈机体强攻/堡垒/侦查型 | 170、171、172 | 由表内评级和型号消除双候选歧义；修复一处“燃料耗尽”，标签配对已修复 |
| rowspan/跨页 | `html-5666db891fb4` | `装备/武器/巨兵.md` | 230–231 | “共鸣之镰”两行纵向合并一致；修复货币单位和“战技骰值” |
| 嵌套/rowspan | `html-dc93205acefe`、`html-714a027e148f`、`html-a7ec4531de8f` | `心灵之光/同调.md` | 63–64 | 外表跨页、两张内表数值和排他性梯度一致；移除表外重复段落 |
| 嵌套/rowspan | `html-1cd1b60b1b6d`、`html-ca176667b32d`、`html-41d827e47578`、`html-80e34fa456ff` | `速查图表/检定一览表.md` | 116–117 | 主表跨页、同调/压迫内表和侵蚀附表关系一致 |

## 已修正问题

1. `同调.md`：同调表跨页末行在表格结束后又重复出现一次；PDF P63–64 只存在表内内容，已移除表外副本。
2. `晋升.md` 与 `经历与晋升一览表.md`：7–8 级阶位误写为第二个“七阶收尾人”；PDF P17/P118 明确为“六阶收尾人”，两处镜像一并修正。
3. `怪谈/侦查型.md`：“涡轮全开”每幕消耗燃料，但结束条件误写为“烧伤耗尽”；PDF P172 和原 CHM 均为“燃料耗尽”，已修正，同时保留当前规则使用的“烧伤”效果名。
4. `巨兵.md`：“回响镰刃”价格单位误写为“限”，原文为“眼”；效果公式漏掉“骰”字，原文为“触发战技骰值×触发倍数”，均已修正。
5. `属性平衡.md` 及 6 个机体表：旧 Word HTML 遗留 45 个缺失的 `</b>` 与 60 个无匹配起点的 `</b>`；已限定在这 7 个高风险文档内配平，不改变任何可见文字、数值、rowspan 或 colspan。

## 保留的当前规则差异

原 PDF/CHM 是 1.8.4 参考材料，不是覆盖当前 `docs/` 的唯一权威。以下差异在当前规则中成体系出现，且并非本次 HTML 转换引入，因此予以保留：

- 机体/武器表使用“动作 + 类型”双列及“计划/交锋/攻击”等当前动作术语，而旧版原文使用“骰子”列和旧分类；
- 当前规则统一使用“突刺”，旧版部分位置写作“穿刺”；
- 属性平衡表使用“角色评级”，旧版写作“角色阶位”；
- 速查表使用“报酬（经历点）”以明确字段含义，旧版速查页只写“经历点”；
- 等级晋升变体的 canonical 表按 PDF 可见网格表示，不恢复 CHM Word 布局中用于排版的空白“参考经验值”行。

这些保留项在同仓库相邻规则中有一致用法，故判定为当前规则语义/规范化差异，不作为转换缺陷回退。

## 证据

- 高风险状态与精确页：[`canonical-table-high-risk-review.json`](../engineering/canonical-table-high-risk-review.json)
- 哈希钉定复核集合：[`canonical-table-high-risk-review-registry.json`](../engineering/canonical-table-high-risk-review-registry.json)
- 复核策略：[`canonical-table-review-policy.json`](../engineering/canonical-table-review-policy.json)
- 原 CHM 文本比较：`output/evidence/table-html-conversion/high-risk-source/chm-text-comparison.json`
- PDF 高分辨率页：`output/evidence/table-html-conversion/high-risk-source/page_166.png` 至 `page_172.png`、`page_230.png`、`page_231.png`、`page_342.png`
- 原 CHM 解包：`output/evidence/table-html-conversion/origin-chm-decompiled-20260905/`

## 剩余门禁

高风险原文语义门已关闭，无需用户再次审核这些表或批次产物。阶段 7 仍保留混合工作树的独立回滚/提交边界门；阶段 8 的 CI 防回归接入尚未完成，不能据此宣称整项计划已经结束。
