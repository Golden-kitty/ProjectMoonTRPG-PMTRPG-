# 分发表格结构审计补强（2026-09-08）

- TaskType：全量 HTML 表格分发验证器修复核验与结构审计补强。
- Goal：准确解释 `rowspan + colspan` 对 Word 续行的影响，并按逐表合并坐标检查实际产物，防止总数一致掩盖跨度损失。
- EditableAreas：分发验证器、精准测试，以及已授权标题空白修复所影响的清单定位和批次哈希。
- OutOfScope / ForbiddenAreas：正文语义改写、导出器修改、原始二进制、stash、提交推送、代替视觉和用户验收。
- Provides：验证器补强、9 项精准测试、v2 独立证据、标题格式修复的哈希追溯。
- AcceptanceChecks：源表 ID 覆盖、逐表行列/合并起点/跨度/嵌套一致、CHM 解包资源、Word 打印文本、清单与源文件哈希。

## 旧误报与既有 WIP

接手时 `scripts/validate_distribution_tables.py` 已有 `docx_gridspan_slots` 修正，`tests/test_export_table_adapters.py` 已有联合跨行跨列测试。本轮保留这些既有 WIP，不将其记为新增修复。

旧报告 `output/evidence/html-release-20260908/distribution-audit.json` 将 1983 个 HTML 跨列起始格直接与 1995 个 Word `gridSpan` 比较，产生 `docx_gridspan_count_mismatch`。跨行且跨列的 Word 单元格在每个垂直合并续行继续携带 `gridSpan`；正确预期是对每个 `colspan > 1` 的源格累计其 `rowspan`。额外的 12 个续行标记有源结构依据。

## 本轮新增检查

- 保留表数量、`gridSpan`、`vMerge`、图片与正文完整性检查。
- 独立从 HTML 重建合并起点与二维跨度，不调用导出器的表布局函数。
- 从 DOCX 原始 OOXML 的每行物理单元格重建垂直合并链，检查续行宽度、行网格宽度、合并起点及跨度。
- 按源文顺序核对 DOCX 的每表行数、列数和嵌套深度；DOCX 不含源表 ID，该关联不宣称是从 DOCX 读取的 ID。
- 按保留的 `data-table-id` 对 CHM 生成 HTML 和实际解包 HTML 逐表核对几何结构；源 ID 缺失或重复也报错。
- 新增 9 项测试，包含续行宽度变动、断开垂直链、移除续行跨度、移动合并起点、嵌套表，以及 CHM 的 ID 顺序与跨度破坏。总标记数仍相同的破坏也必须失败。

运行：

```powershell
python -m unittest discover -s tests -p test_distribution_table_structure.py -v
python -m unittest discover -s tests -p test_export_table_adapters.py -v
```

结果分别为 9/9、10/10 通过。

## v2 机器证据及限制

证据目录：`output/evidence/html-release-20260908/v2/`。所有新报告与旧报告并存。

- `canonical-structure-audit-initial.json`：canonical 与源结构均 PASS。
- `rendered-audit-initial.json`：正向与反向覆盖 370 表、92 个表格正文页，0 issue。
- `distribution-audit-word-chm.json`：v2 机器审计 PASS；DOCX 370 表、1995 个 `gridSpan`、114 个 `vMerge`，6 张嵌套表的结构一致；CHM 解包 161 篇 HTML、370 表、47 次图片引用、4 个图片文件，无资源缺失。
- 同一报告中的真实 Word 打印 PDF 为 192 页，独立 PDF 为 244 页；两者均匹配 1523/1523 个源正文块，未发现未嵌入的 CJK 字体。
- 这些检查不等同于所有表格单元格文字的逐字语义审计、版面视觉验收或查看器验收；报告的人工门槛保持 `pending`。

可复现命令：

```powershell
python scripts/validate_distribution_tables.py --pilot-dir output/export_samples/pmtrpg-html-review-20260908-v2 --batch-name pmtrpg-html-review-20260908-v2 --file-list output/export_samples/pmtrpg-html-review-20260908-v2/source-files.txt --chm-decompiled output/evidence/html-release-20260908/v2/chm-decompiled-audit-direct --docx-word-print output/evidence/html-release-20260908/v2/docx-word-print.pdf --report output/evidence/html-release-20260908/v2/distribution-audit-word-chm-rerun.json
```

## 已授权标题格式修复后的来源状态

协调任务在 `docs/资源目录/工坊/后巷/好棒棒快餐连锁.md` 的首个四级标题前补空行并移除两个缩进空格，以修复 PDF 露出原始 `####`。本子任务未编辑该正文。逆向还原这两项空白差异后的 SHA-256 精确命中原清单哈希，证明没有额外文字或数值变化，五张表的结构也完全一致。

- 旧源 SHA-256：`f0a16bbcf84809b2bd0f8bbff06ec51ec044f790109d07caeddec13e9d4696d6`
- 新源 SHA-256：`512c4d675a19963548c7a00d192a072288ee7cb57889d73efc1da1bdfb633fea`
- `heading-format-hash-sync.json`：记录该验证及变更清单；写前副本位于 `before-heading-hash-sync/`。
- 清单仅更新此五表的 `line/end_line`；batch 03 更新该文档哈希、五表行号和批次快照；12 批及汇总同步清单新指纹。没有相应文档的既有接受/高风险注册哈希，接受状态保持原记录。
- `batch-hash-audit-after-heading.json`：12 批、370 表、92 文档、全部文档哈希、批次快照和清单指纹 PASS。
- `canonical-structure-audit-after-heading.json`：源结构与 canonical PASS。

v2 manifest 作为旧候选来源快照保留。标题修复后再次校验，`manifest-source-audit-after-heading.json` 正确报告仅该文件发生哈希漂移；v2 不能直接作为当前源的最终交付候选。此前 `manifest-source-audit.json` 是字段探索报告，其中 `canonical_target` 使用了不存在的 `final_target` 键；正式复核工具使用清单实际字段 `target_state`，对应检查通过。最终候选须另行生成 manifest 并复验。

只读清单复核工具为 `output/evidence/html-release-20260908/v2/audit_release_manifest.py`，支持 `--manifest` 和 `--report`，检查源文件顺序/哈希、清单 ID、实际源 ID 与 inventory ID；不会覆盖既有报告。

## v5 最终候选机器复核与独立原文检查

当前候选目录：`output/export_samples/pmtrpg-html-review-20260908-v5/`。新证据均写入 `output/evidence/html-release-20260908/v5/`，不覆盖 v2/v4 历史报告。

v4 的初版机器检查 PASS 存在明确盲点：正文覆盖的预期文本与导出器共用 Markdown 解析，`attr_list` 吞掉连续花括号行时，预期文本也一并丢失。协调任务发现森语三文缺失 20 段，移除了导出器、站点配置与配置生成器中的该扩展；本子任务未修改这三处或正式正文。

本轮在 `scripts/validate_distribution_tables.py` 新增独立的 `raw_brace_blocks` 检查，直接从原始源行提取包含中文的花括号片段。按对应源文件的 HTML section、PDF/Word 原文路径标识划定局部范围，比较规范化可见文字及出现次数，其他章节同句不能补位；HTML 属性、style、script 不算可见证据。该检查验证文字与数字存在，规范化会忽略标点，不宣称逐字节语义等价。

- 全部 161 篇源文共 43 条原始中文花括号片段；v5 的源渲染、PDF HTML、CHM 生成/解包、DOCX、独立 PDF、Word 打印均为 43/43，无缺失。
- 实际构建站点的对应三个 article 另行核验，`site-raw-brace-audit.json` 为 43/43 PASS。
- 对旧 v4 二进制和 HTML 的回归审计准确 FAIL，局部缺失 20 条：车卡说明 13、战斗说明 4、非战斗说明 3。证据 `v4/distribution-audit-raw-brace-regression.json` 保留，不能以旧初版 PASS 覆盖缺陷结论。
- 新增 `tests/test_distribution_raw_braces.py` 的 8 项测试覆盖同源解析漏报、连续花括号与公式、跨章节假匹配、局部重复次数、非可见属性/script、路径换行、DOCX 局部分段，以及显式 HTML 属性和 rowspan/colspan 保留。

`v5/distribution-audit.json` 为 PASS：DOCX 370 表、1995 个 gridSpan、114 个 vMerge、6 张嵌套表几何正确；独立 PDF 275 页、Word 真实打印 195 页，两者正文块 1524/1524。保留原表结构、图片、字体和文本检查，没有降低门槛。

- v5 DOCX SHA-256：`fa9e09f9c4268e7e7fe9efc15a121f5d80f1212a54468d1212cfdf86800739ab`
- v5 Word 打印 PDF SHA-256：`243afde91b5ae5269934e1cad0d0d5f1d87ce73bbf8ce3244ae8d8ab30bb91b1`
- `manifest-source-audit.json`：161 源文件顺序及原始构建输入哈希、370 个 manifest/实际源/inventory ID、canonical-html 最终状态全部一致。
- `canonical-structure-audit.json`：PASS，0 issue。
- `rendered-audit.json`：370/370 表，92 篇表格正文，0 issue。
- `table-integrity.json`：370 表/92 文档 PASS；比较 HEAD `d3fc747d6ad36c0d8cba61fda37d19246482bfe3` 时 Git 追溯仍为 BOOTSTRAP，原因是旧提交尚无首次冻结清单，不能将其解释成每项历史语义改动已获机器批准。

独立提交 review 发现验证依赖清单缺少 PyMuPDF，而新增审计测试会导入 `fitz`。本轮在 `requirements-validation.txt` 增加与导出依赖一致的 `PyMuPDF>=1.24,<2`。按该清单新建并安装的隔离环境中，最终全量 **94 项 unittest PASS**，日志为 `v5/unittest-clean-ci-env.txt`；环境为本机 Windows/Python 3.14，不冒充远端 Ubuntu/Python 3.11 已运行。

候选清单与依赖 review 位于 `v5/git-candidate-inventory.json` 和 `v5/git-candidate-review.md`，当前候选 186 文件，比 v4 多一份原始花括号测试；没有发现遗漏的本地脚本依赖。验收门槛、发布、Git 提交后的来源绑定仍由协调任务单独处理。本子任务仅记录 v4 Word 第 1–97 页逐页视觉结果于 `v4/word-review-001-097.md`，其中分页留意项不因机器 PASS 自动关闭。
