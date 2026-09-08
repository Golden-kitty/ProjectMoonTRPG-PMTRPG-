# 阶段 1：Canonical HTML 校验器基线

## 结论

阶段 1 的工具门禁已通过，可以进入本地转换与渲染试点。这里的“通过”表示校验器与回归比较器已经可用，不表示当前 369 个源内容表已经完成转换。当前旧 HTML 的严格规范审计仍为 `FAIL`，它正是后续转换必须清零的基线。

## 工具与边界

- [`scripts/validate_canonical_tables.py`](../../scripts/validate_canonical_tables.py) 只读扫描源文件，不改写 Markdown 或 HTML。
- `structural` 模式把当前 HTML 与冻结清单比较，检查表格增删、行列数、`rowspan`/`colspan` 签名、嵌套层级和图片引用。
- `canonical` 模式检查必需的 `class="pmtrpg-table"`、稳定 `data-table-id`、ID 唯一性、表头 `scope`、合法 span、网格宽度、图片路径/`alt`、禁用标签、内联样式和标签闭合。
- [`scripts/semantic_table_merges.py`](../../scripts/semantic_table_merges.py) 仍只视为候选工具，未接入自动转换路径；不得据相邻文本自动推断合并单元格。
- 两个旧 HTML→Markdown 脚本继续默认拒绝有损转换；只有显式提供 `--allow-lossy` 才可能改写文件。

## 可复现结果

运行：

```powershell
python -m unittest discover -s tests -p 'test_*.py' -v
python scripts/generate_table_inventory.py --docs docs --mapping "docs/PDF章节页码映射.md" --output "docs/engineering/table-inventory.json" --queue-output "output/spreadsheet/table-review-queue.csv"
python scripts/validate_canonical_tables.py --mode structural --report "docs/engineering/table-structure-regression.json"
python scripts/validate_canonical_tables.py --mode canonical --report "docs/engineering/canonical-table-audit.json"
```

结果：

- 单元测试：9/9 通过，覆盖有效规范表、非法 span、缺失图片/`alt`、未闭合嵌套表、跨文件重复 ID、结构签名变化和默认拒绝 HTML→Markdown。
- 冻结结构回归：343 个旧 HTML 表，`PASS`，0 个结构变化。
- 严格规范基线：82 个文档中的 343 个旧 HTML 表，`FAIL`，共 1369 个待处理项。该失败是转换前的预期结果，不是回归失败。

严格基线按问题类型汇总：

| 问题 | 数量 | 后续处理 |
| --- | ---: | --- |
| 缺少 `pmtrpg-table` class | 343 | 本地转换器统一补齐 |
| 缺少 `data-table-id` | 343 | 写入与清单 ID 一一对应的稳定 ID |
| 旧 `<table>` 属性 | 585 | 326 个 `border`、258 个 `width`、1 个畸形属性；迁移到受控 CSS 或修复语法 |
| 有效列宽不一致 | 60 | 对照 span 与 PDF 来源逐表核对，禁止自动猜测合并 |
| 旧单元格属性 | 8 | 转为允许的 class 或删除纯表现属性 |
| 内联样式 | 1 | 转为受控 class |
| 图片缺少 `alt` | 23 | 在批次中根据图片语义补齐，不用文件名冒充人工描述 |
| 行/单元格闭合异常 | 6 | 先修正源 HTML，再进入渲染比较 |

闭合异常目前集中在以下 5 个文档（6 个问题）：

- `docs/资源目录/工坊/后巷/好棒棒快餐连锁.md`
- `docs/资源目录/消耗品/成瘾品/生理成瘾品.md`
- `docs/资源目录/消耗品/食物/包装食物.md`
- `docs/资源目录/消耗品/食物/碳酸饮料.md`
- `docs/资源目录/课程/流派战技/臼齿事务所.md`

完整逐项结果见 [`canonical-table-audit.json`](canonical-table-audit.json)，结构回归见 [`table-structure-regression.json`](table-structure-regression.json)。

## 人工审核输入

此阶段不要求用户阅读 343 份 HTML 源码。下一阶段先在本地完成转换试点、规范审计、站点构建和浏览器渲染；提交人工审核时应同时提供：

1. 实际页面或页面截图；
2. 转换前后的结构签名差异；
3. PDF 精确页码和可能的语义差异；
4. 仍需裁定的少量问题，而不是整张未筛选队列。
