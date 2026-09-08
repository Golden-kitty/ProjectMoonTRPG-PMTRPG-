# 阶段 0 清单盘点记录

## 目的与边界

本记录对应 [`full-html-conversion-plan.md`](full-html-conversion-plan.md) 的阶段 0。扫描只读取 `docs/**/*.md`，不改写规则正文，不执行 HTML/Markdown 转换，也不把 `originFab/` 当作编辑源。最终目标是所有 `source-content` 表格均为 canonical HTML；工程/验收证据文档不属于迁移对象。

> **历史快照说明（2026-09-05）**：本页保留阶段 0 当时的发现与计数口径；实时逐表状态以 [`canonical-table-stage7-batches.json`](canonical-table-stage7-batches.json) 和 [`table-inventory.json`](table-inventory.json) 为准。当前 369 个 `source-content` 表已经全部成为 canonical HTML，高风险原文复核 24/24 完成，待 Codex 复核、待用户裁定和未解决迁移状态均为 0。已通过的代表性 CHM/DOCX/PDF 样例不再触发逐批用户复核。

## 队列术语（按最终目标重新定义）

- **待迁移**：当前仍是 Markdown 管线表，或是需要按 canonical HTML 子集规范化的 HTML 表；最终必须变成/保持 canonical HTML。
- **待验收**：已经转换为 canonical HTML，并通过当前机器校验，但尚未完成全部分发抽查与人工接受。
- **已迁移 HTML**：表格已经符合 canonical HTML 契约，并通过对应批次的结构和分发验收；不是“只要出现 `<table>` 就算完成”。
- **暂缓**：临时阻塞状态，例如来源页、语义裁定、图片资源或某个输出适配器证据尚未齐全。暂缓不是永久保留 Markdown；证据补齐后仍回到“待迁移”，直到“已迁移 HTML”。
- **保留 Markdown**：这是原计划草案曾允许的可选终态，不符合你当前确认的全量 HTML 目标，因此不再作为 `source-content` 的合法最终状态。

机器清单由 [`scripts/generate_table_inventory.py`](../../scripts/generate_table_inventory.py) 生成，逐表结果见 [`table-inventory.json`](table-inventory.json)。扫描器会屏蔽 fenced code 和 inline code，再统计真实 HTML 标签；这是为了避免表格清单、验收记录和工程说明中的字面量 ``<table>`` 被算作源表。

## 历史计数追查

对以下提交使用同一套扫描口径重算：

| 提交 | 未屏蔽的 `<table>`（表/文档） | 屏蔽代码与说明后的真实 HTML 表（表/文档） | Markdown 管线表（表/文档） | 解释 |
| --- | ---: | ---: | ---: | --- |
| `8a5359f` | 0 / 0 | 0 / 0 | 384 / 93 | HTML 表恢复前的基线 |
| `35ada7c` | 391 / 84 | 343 / 82 | 27 / 17 | hotFix 恢复提交；391/84 多出的 48 个标签、2 个文档来自说明性字面量 |
| `d3fc747` | 391 / 84 | 343 / 82 | 27 / 17 | 仅更新 `资源设计表格.md`，不改变表格计数 |
| 当前工作树（排除本记录自身） | 394 / 85 | 343 / 82 | 45 / 20 | 当前新增工程计划本身含 3 个字面量 `<table>`；新增工程草稿带来 18 个管线表 |

因此，计划正文中的 `391/84` 可以复现，但它是“未屏蔽文本引用”的统计口径，不代表 391 个真实 HTML 表。`343/82` 与 [`hotfix-html-table-restoration.md`](../acceptance/hotfix-html-table-restoration.md) 的恢复记录一致。计划中的第三个数字“约 84 个 Markdown 管线式表格头”无法用当前可复现的管线表解析口径重现：历史提交得到 `384/93`，恢复后的提交得到 `27/17`，当前工作树得到 `45/20`。该数字应由维护者确认其原始筛选条件，不能直接作为迁移对象数量。

在 `d3fc747` 中，未屏蔽统计多出的 48 个标签可以逐文件复现：`docs/表格重建清单.md` 的 47 个和 `docs/acceptance/AC-001-document-work-acceptance.md` 的 1 个，全部位于 Markdown 代码/说明文字中，屏蔽后均为 0 个真实标签。这解释了“391 → 343”和“84 → 82”的差异，并没有证据表明 48 个 HTML 源表从树中丢失。

初版章节映射解析器还曾把“同一页码对应多个文档链接”的行只取成第一个文档，造成 6 个资源文件的 13 个表暂时无候选。现已改为将该行页码关联到全部 `docs/...md` 链接；重生成后所有 369 个源内容表均有章节级候选，未再发现源内容表的映射缺口。

## 当前阶段 0 结果

- 清单覆盖率：真实 HTML 表 343/343，HTML 表文档 82/82；Markdown 管线表另列，不与 HTML 表重复计数。
- 章节映射：使用 [`PDF章节页码映射.md`](../PDF章节页码映射.md) 生成来源页候选；候选是章节级入口页，不等同于表格精确页码。修复“一页对应多个文档链接”的解析后，369 个 `source-content` 表全部获得候选；剩余 19 个无候选项全部是工程/验收证据文档。
- 复核队列：`output/spreadsheet/table-review-queue.csv`，共 388 行；其中 369 行是 `source-content`，19 行是工程/验收证据（`review_required=False`），每行包含稳定 ID、路径、行号、表示方式、span/嵌套/图片风险、来源页候选、负责人和裁定字段。
- 队列口径：369 个 `source-content` 表的最终目标均为 canonical HTML；阶段 0 初始状态为 `待迁移`，完成本地转换和机器校验后现已统一推进为 `待验收`，仍不等于用户已经接受最终输出。
- 自动合并推断：禁止。所有 `rowspan`/`colspan`/嵌套表必须人工确认。
- 当前机器门禁：`PASS_MACHINE`。真实表计数、稳定 ID、章节候选和人工队列均已覆盖；精确来源页、维护者裁定和 `review_owner` 在对应本地转换批次开始时补齐，不再要求用户在看到渲染结果前逐表审核原始标记。

## 复核字段约定

| 字段 | 初始值 | 维护者填写要求 |
| --- | --- | --- |
| `source_page_candidates` | 章节映射得到的一个或多个页码 | 对照 PDF 缩略图确认精确页码；一对多映射不得擅自合并 |
| `source_page` | 空 | 仅填已人工核对的页码 |
| `review_owner` | 空 | 指定实际负责语义核对的人或角色 |
| `target_state` | `canonical-html` | `source-content` 的最终目标，不得改成 Markdown |
| `disposition` | `待迁移` | 中途可填写 `暂缓`，完成全部验收后填写 `已迁移 HTML`；不得填写“保留 Markdown”作为最终状态 |
| `review_notes` | 空 | 记录语义差异、降级或回滚理由 |

阶段 0 的机器门禁通过后可以进入校验器和本地转换开发。这里记载的是阶段 0 当时的门禁设想；后续已经用代表性多格式样例验收和高风险原文复核取代逐批用户验收。现行口径见 [`canonical-table-high-risk-source-review.md`](../acceptance/canonical-table-high-risk-source-review.md)：只有无法从 PDF/CHM 判定的语义歧义才升级给用户。
