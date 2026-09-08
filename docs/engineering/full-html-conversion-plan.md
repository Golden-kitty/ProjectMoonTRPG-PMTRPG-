# 全量 HTML 表格转换计划（Halcyon'edit）

> 状态：执行中。阶段 0–6 已完成；用户于 2026-09-05 确认四格式试点、新版 PDF 正文可见性和技能花色修正“通过”，并确认后续批次无需重复审核产物样例，原文 HTML 只重点审核高风险项。阶段 7 的语义/来源门已闭合：369 张正文表已形成 12 个文档原子批次，每批 27–34 张；19 张试点表已记录为用户接受，7 张非重叠表已由既有 PDF 直接对照证据闭合，24 张高风险源表已由 Codex 完成 PDF/CHM 对照，319 张普通表按用户确认的复核策略关闭，待核为 0。阶段 7 仍保留混合工作树的独立回滚边界门。基于 `Halcyon'edit` 已合入完整 `hotFix` 历史后的工作树。
> 本文不是规则裁定，也不授权直接改写全部文档；后续批次仍必须经过机器门禁和实施者抽样，高风险源表必须逐项对照原文，只有证据无法消除的语义歧义才提交用户裁决。

## 1. 任务边界

**TaskType**：文档格式架构、跨格式分发适配和分批迁移计划。

**Goal**：将所有 `source-content` 表格最终统一为单一、可审计的 canonical HTML 表格表示，并让站点、CHM、DOCX、PDF 各自通过明确的适配器消费该表示，消除隐式 HTML→Markdown 的有损回写。

**OutOfScope**：当前清单/规范阶段不直接执行全量转换；不修改 `originFab/` 原始 PDF/CHM；不借格式迁移顺便重写规则、数值、章节顺序或图片资源；不承诺任意 HTML/CSS 高级特性能在 PDF 中等价呈现。全量 HTML 转换是本计划后续分批阶段的明确目标。

**EditableAreas**：`docs/` 中已确认的表格内容、转换/导出脚本、验收记录和本计划。

**ForbiddenAreas**：原始二进制、`site/` 等生成目录、未列入批次的章节，以及没有来源证据的语义内容。

## 2. 合入后的事实基线

- `Halcyon'edit` 当前为 `d3fc747`，与 `origin/hotFix` 指向同一提交；`35ada7c` 的 HTML 表恢复历史以及后续 `d3fc747` 的资源表更新均已包含在当前基线中。
- `35ada7c` 恢复了 82 个文档中的 343 个 HTML 表格（含嵌套表格），并保留了 `0ca326d` 的规则更新；对应验收记录见 [`docs/acceptance/hotfix-html-table-restoration.md`](../acceptance/hotfix-html-table-restoration.md)。
- 本次冲突处理保留 hotFix 的表格结构签名（`rowspan`/`colspan`/嵌套关系），同时带回 Halcyon 工作树中确认过的语义修改；`docs/核心规则/创建角色/技能.md` 的默认技能为“棍棒”。
- 重新屏蔽代码块和行内代码后，转换前真实表格基线为 343 个 HTML 表、45 个 Markdown 管线表，共 388 个对象；其中 369 个属于规则正文，19 个属于当时的工程/验收证据。高风险复核记录后来新增 1 张证据用 Markdown 表，因此最新清单为 369 个 canonical HTML 正文表、20 个工程/验收 Markdown 表，共 389 个对象；正文目标数未变化。旧计数 `391/84` 把说明文字中的 48 个字面量标签算进了结果，详见阶段 0 盘点记录。
- `python scripts/build_site.py build` 已成功。当前仍有 `project-terminology.md` 未纳入 nav 的既有警告，以及 Material for MkDocs 未来版本警告；二者不应与表格转换结果混为一谈。
- 工作树中原有的 Halcyon 编辑、工程草稿和脚本改动已通过 stash 保护并恢复；备份 `stash@{0}`（`5b4acbfc6b9c168df83ed3423463bdedd29cb159`）在完成最终核对前保留，不得删除。

## 3. 规范决策：统一“表格表示”，而非强行 HTML 化一切文本

1. **一个表格只允许一种表示**：复杂表格（合并单元格、嵌套、图片、跨行标题、需要精确列宽的表格）以 HTML 为规范源；同一表格中不再混用 Markdown 管线语法和 HTML。
2. **正文仍可使用 Markdown，表格不保留 Markdown 终态**：统一表格表示不等于把所有段落、列表、代码块改成 HTML；这些非表格正文继续使用 Markdown。所有 `source-content` 表格（包括简单表、无合并表和仅供站点阅读的辅助表）都必须在后续批次中迁移为 canonical HTML；“暂缓”只表示证据或适配器未齐时的临时状态，不是永久保留 Markdown 的方案。导出脚本不得隐式把 HTML 写回 Markdown。
3. **语义先于外观**：表格标题、列标题、前提、消耗、行动类型、骰值、效果和图片替代文本是语义字段；`rowspan`/`colspan` 只表达已核对的重复关系，不能通过“相邻单元格看起来一样”自动推断规则。
4. **来源分层**：当前 `docs/` 是编辑源；`originFab/` 只作 PDF/CHM 对照。任何数值、名称、前提或效果差异都要记录来源和人工裁定，不能把渲染器输出反写成规则源。

## 4. 目标 HTML 子集（Canonical HTML Subset）

每个 `source-content` 表格最终都应符合以下最小契约：

- `<table>` 必须使用 `class="pmtrpg-table"` 和稳定、唯一的 `data-table-id`；标题使用 `<caption>` 或表格首行标题；列标题使用 `<th scope="col">`，行标题使用 `<th scope="row">`。
- 只使用经过适配器测试的 `rowspan`、`colspan`、`<thead>`、`<tbody>`、`<br>`、图片 `alt` 和有限的 class；不把浏览器专属脚本、外部字体、浮动定位、复杂伪元素或交互组件塞进规范表格。
- 图片使用仓库内相对路径，保留尺寸和替代文本；导出器负责复制资源并校验存在性。
- 单元格内换行使用 `<br>`，不用不可见空格模拟布局；长文本允许自然换行，不以固定像素高度裁切。
- 必须保留可读的源文本。若某个视觉效果没有在 DOCX/PDF 适配器中实现，输出应降级为可读文本，而不是静默丢失。
- 为每个表格生成稳定的 `data-table-id`，并与清单 ID 建立一一对应，用于跨站点、CHM、DOCX、PDF 的计数、截图和回归对照。

## 5. 分阶段实施与门禁

统一执行顺序为：机器清单与来源候选 → 本地转换 → 静态结构校验 → 本地站点/分发构建 → 渲染截图与结构差异 → 风险路由。代表性四格式试点经用户接受后，后续批次不再重复设置用户产物审核门；普通表由全量机器证据和实施者抽样闭合，高风险源表由 Codex 对照 PDF，只有仍无法判定的语义差异才进入用户裁决。

### 阶段 0：冻结与清单（1–2 个工作日，低置信度）

生成 `table-inventory.json`，逐表记录路径、章节、ID、表示方式、行列数、span 签名、嵌套层级、图片、特殊 HTML、来源页码、目标输出和风险等级。分类为：简单表、合并单元格、嵌套表、图片表、特殊/人工表、暂缓表；所有分类的最终目标都是 canonical HTML。

门禁：清单覆盖率 100%；所有源内容表都有来源页候选和稳定 ID；任何“自动推断合并”的表先进入人工队列；历史计数差异有可复现解释。精确页码和 `review_owner` 在对应本地转换批次开始时补齐，不再作为阻止阶段 1 工具开发的前置条件。

### 阶段 1：规范与校验器（2–3 个工作日，中置信度）

实现 canonical HTML 校验器和结构签名比较器，检查标签闭合、span 总列数、表头 scope、图片路径、禁止 CSS/脚本和稳定 ID。将 [`scripts/semantic_table_merges.py`](../../scripts/semantic_table_merges.py) 视为候选工具：必须先补测试和人工样例，不能直接作为规则迁移器。

门禁：对 hotFix 的 343 个恢复表零结构回归；对故意破坏的 rowspan/colspan、图片和嵌套样例能稳定失败；`rebuild_html_tables_to_pipe.py`、`rebuild_tables_from_checklist.py` 继续默认拒绝有损转换，仅在显式 `--allow-lossy` 下运行。

### 阶段 2：站点适配器（1–2 个工作日，高置信度）

以 `scripts/build_site.py`、`scripts/generate_mkdocs_config.py`、`scripts/mkdocs_hooks.py` 为入口，统一 CSS 和响应式策略。构建后用 DOM 检查表格 ID、行列/span 签名、图片加载和横向滚动；对复杂表至少保留一张截图或 HTML 快照。

门禁：站点构建成功；表格数量不下降；所有 ID 可定位；移动宽度和桌面宽度均无裁切；复杂表先由实施者完成本地渲染抽查，再提交用户人工验收。构建警告（如未纳入 nav 的既有页面）单独记录，不得掩盖表格失败。

执行结果：**已通过**。369/369 个规则正文表的渲染 DOM 与冻结结构一致；代表性桌面端与 390px 移动端页面完成实测，用户于 2026-09-04 确认“这组站点表格可以接受”。2026-09-05 按原 PDF 的“创建角色／技能”与“技能列表”章节，把技能属性的 24 处旧式括号标记恢复为实际花色图标，其中试点“技能列表”新增 19 个图标引用；站点重新构建成功，`技能列表.html` 的 42 个图标和 `技能.html` 的 5 个图标均可解析且无缺失，截图见 [`canonical-table-pilot-site-skill-markers-20260905.png`](../../output/evidence/table-html-conversion/canonical-table-pilot-site-skill-markers-20260905.png)。验收范围和未关闭门禁见 [`docs/acceptance/html-table-site-acceptance.md`](../acceptance/html-table-site-acceptance.md)。

### 阶段 3：CHM 适配器（2–4 个工作日，中置信度）

CHM 可视层接近浏览器，但编译器、主题、相对路径和本地资源仍有约束。导出 HHP/HHC 时复制图片、CSS 和主题页，确保 TOC、主题数、资源索引和编码正确；使用现有 CHM 样例流程检查编译日志、解包后的 HTML/CSS/图片和实际页面截图。

门禁：CHM 编译成功；主题数与清单一致；Graphics/资源条目非零且图片可显示；至少抽查一个 rowspan、一个 colspan、一个嵌套表和一个图片表。CHM 的“像浏览器”不能替代实际编译和截图验收。

执行结果：真实编译、解包、19 张代表表结构核对和解包负载浏览器检查均通过。用户确认正文内容无误后，发现旧版左侧目录标题乱码；根因为 HTML Help Workshop 4.x 按 Windows ANSI 代码页读取 UTF-8 `.hhc`/`.hhp`。控制文件改为 GBK 并声明 `gb2312` 后重新编译，真实 Windows HTML Help 查看器中五个中文目录标题均正常，且用户已确认该问题修复，截图见 [`canonical-table-pilot-chm-viewer-20260905.png`](../../output/evidence/table-html-conversion/canonical-table-pilot-chm-viewer-20260905.png)。技能属性标记修正后再次编译并解包，4 个唯一 JPG、42 次引用均完整。编译器日志仍错误显示 `0 Graphics`，已用解包后的实际资源交叉验证；技能花色修正的用户复核归入阶段 6。

### 阶段 4：DOCX 适配器（3–5 个工作日，中低置信度）

明确选择 Pandoc 或自定义 `python-docx` 适配器，并把 HTML span 映射为 OOXML `gridSpan`/`vMerge`。处理页宽、重复表头、长文本换页、图片锚点和字体回退；通过 LibreOffice/Word 渲染后逐页检查，而不是只检查 XML 存在字段。

门禁：复杂表的 gridSpan/vMerge 数量与清单匹配；图片资源存在且可见；无被截断的单元格；DOCX 打开无修复提示；代表性页面人工确认。当前 hotFix 样例已显示“OOXML span 存在但图片缺失”的风险，必须作为回归用例。

执行结果：已实现 `python-docx` 适配器；代表样本的 19 张表、26 个 `gridSpan`、35 个 `vMerge`、42 个 drawing 和 4 个媒体文件与源端一致。用户确认旧版表格行距偏松及 `[黑桃]`、`[梅花]` 等重复文字问题已经修复。本地图片不输出重复 alt，图标在源顺序位置进入同一段落，小图标宽度为 0.17 英寸，表格段落使用单倍行距和 0 段前/段后；全部显式分页符和 `pageBreakBefore` 已移除。新增的技能属性花色图标也按源位置混排：手术/内科等梅花、攀爬等红心、侦查方块均紧随技能名，而 `外科（蜥蜴人）` 等备注不变。真实 Word 打印得到 11 页，11/11 页无空白页、裁切、越界或图片丢失；41/41 个正文块与 4 个唯一图片对象存在。打印过程由 `scripts/print_docx_with_word.ps1` 复现，证据见 [`canonical-table-pilot-docx-word-print-pages-20260905-v8/contact-sheet.png`](../../output/evidence/table-html-conversion/canonical-table-pilot-docx-word-print-pages-20260905-v8/contact-sheet.png)。技能花色修正的用户复核归入阶段 6。

### 阶段 5：PDF 适配器（3–6 个工作日，中低置信度）

先选定渲染器和 CSS 子集（例如浏览器打印/WeasyPrint 等），再实现页眉页脚、分页、重复表头、字体嵌入和图片策略。不要假设任意高级 HTML/CSS 都能等价落到 PDF：脚本、交互、悬浮定位、复杂 flex/grid、滤镜、动画、外部字体和部分嵌套 span 通常需要降级或专门测试。

门禁：渲染后逐页转图片进行人工检查；验证表格不越界、不重叠、不丢文本，合并单元格语义可读；对不支持特性产生显式降级记录。当前报告中已观察到复杂 rowspan/colspan 的 PDF 退化，不能以“PDF 生成成功”作为通过条件。

执行结果：旧 ReportLab 适配器先后修复了字面 `<br/>` 和有限标签遍历，但仍用未嵌入的 `STSong-Light` CID 字体；本机字体代换掩盖了问题，用户查看器中会只剩表格边框和图标。正式 PDF 路径现改为 Chromium 从同源 HTML 打印。新版为 11 页、约 809 KB，嵌入 3 个 Microsoft YaHei 子集，未嵌入 CJK 字体为 0；五个章节标题、41/41 个表格外正文块、正确 Unicode 文本层、19 张表和 4 个唯一图片对象均存在。11/11 页以 2 倍分辨率逐页检查，未发现裁切、重叠、越界、乱码、正文或资源丢失，技能属性图标也处于正确语义位置。证据见 [`canonical-table-pilot-pdf-20260905-v5/contact-sheet.png`](../../output/evidence/table-html-conversion/canonical-table-pilot-pdf-20260905-v5/contact-sheet.png)。用户于 2026-09-05 复核后确认“通过”。

### 阶段 6：小规模试点（2–3 个工作日，中置信度）

选取 10–15 张代表性表：简单表、横向 colspan、纵向 rowspan、嵌套表、含图表、长文本、跨页表和已在 hotFix 中受损后恢复的表。每张表同时跑站点、CHM、DOCX、PDF，生成清单、结构 diff、截图和人工结论。

门禁：四种输出均有可追溯证据；任何语义差异有裁定记录；失败样例形成“暂缓或降级”规则；本地转换、构建、结构 diff 和截图齐全后再交给产品负责人验收，验收通过后才扩大批次。

执行结果：**已通过**。五个代表文档覆盖 19 张表，包括普通表、横向 colspan、纵向 rowspan、嵌套表、图片表、长文本和跨页内容。站点、CHM、DOCX、PDF 的机器与实施者门全部通过；用户依次确认站点表格、CHM 内容与目录、DOCX 行距与重复替代文字、新版 PDF 正文可见性，以及技能花色修正，并于 2026-09-05 最终回复“通过”。完整记录见 [`canonical-table-distribution-pilot.md`](../acceptance/canonical-table-distribution-pilot.md)。该接受只覆盖试点 5 个文档中的 19 张表，不扩大解释为阶段 7/8 已完成。

### 阶段 7：全量分批迁移（每批 20–40 个表）

按风险和章节分批，顺序建议为：无合并简单表 → 单层 colspan/rowspan → 图片表 → 嵌套/跨页特殊表。每批独立提交、独立 manifest、独立回滚点；禁止在一个提交中同时改规则、导航、资源目录和转换逻辑。批次完成后运行站点构建和至少一组 CHM/DOCX/PDF 样例。

执行进展：当前 369 张 canonical HTML 正文表已按文档原子性生成 12 个表级 manifest，每批 27–34 张，覆盖 92 个文档且没有表格或文档跨批重复；分组顺序按简单表、span 表、图片表、嵌套/高风险表排列。新复核策略已写入 [`canonical-table-review-policy.json`](canonical-table-review-policy.json)：19 张试点表标为 `accepted_by_user`，7 张非重叠表标为 `source_verified_by_pdf_evidence`，24 张嵌套、纵向合并、十列以上或大表页码映射歧义项已标为 `source_verified_by_high_risk_review`，319 张普通表标为 `closed_by_user_review_policy`，待核为 0。高风险复核发现并修正同调重复段、晋升阶位、燃料结束条件、货币单位、公式漏字及旧 HTML 粗体标签配对问题；完整结论见 [`canonical-table-high-risk-source-review.md`](../acceptance/canonical-table-high-risk-source-review.md)。清单、批次与复核队列见 [`canonical-table-stage7.md`](canonical-table-stage7.md)、[`canonical-table-stage7-batches.json`](canonical-table-stage7-batches.json)、[`canonical-table-high-risk-review.json`](canonical-table-high-risk-review.json) 和 `output/spreadsheet/canonical-table-stage7-review-queue.csv`。当前混合工作树尚未形成批次独立提交，因此 manifest 明确将回滚能力标为“独立提交前仅能检测漂移”；阶段 7 状态仍为 `IN_PROGRESS`。

第 1 批已经生成独立 HTML、CHM、DOCX、PDF：30/30 张表和 125/125 个正文块通过机器检查，CHM 真实编译为 14 个主题，Chromium PDF 23 页与 Word 实际打印 15 页完成实施者逐页检查。用户产物审核门已按新策略关闭；该批 2 张表沿用试点接受、27 张普通表按策略关闭，`等级.md` 的 11 列宽表也已在集中高风险原文复核中闭合。范围、来源页和成品链接见 [`canonical-table-stage7-batch-01.md`](../acceptance/canonical-table-stage7-batch-01.md)。

### 阶段 8：收口与长期防回归（1–2 个工作日）

把表格清单和结构检查接入 CI；检测表格数量下降、span 签名变化、图片缺失、冲突标记、隐式 Markdown→HTML/HTML→Markdown 转换和未经授权的规则文本变化。将有损脚本保留为显式应急工具，并在文档中标注风险；删除“默认自动转换”的调用路径。

## 6. 分发结论和风险登记

| 输出 | HTML 适配能力 | 主要风险 | 必须的验收 |
| --- | --- | --- | --- |
| 站点 | 高，浏览器可直接展示大部分规范子集 | 响应式宽度、CSS 覆盖、图片路径 | DOM/截图/构建 |
| CHM | 中高，渲染模型接近浏览器但资源和编译器受限 | 相对路径、编译索引、旧内核兼容 | 编译、解包、截图、资源数 |
| DOCX | 中，需要 OOXML 表格映射 | 合并单元格、分页、图片锚点、字体 | OOXML + 渲染逐页 |
| PDF | 取决于选定渲染器，不能承诺任意 HTML | CSS 子集、分页、字体、复杂嵌套/合并 | 页面图像 + 文本/边界检查 |

因此，“CHM 像浏览器”只能说明 HTML 是合理的规范源，不能推出 DOCX/PDF 会自动无损。正确做法是统一源表示、分别实现适配器，并把不支持的高级特性限制在经过验证的子集内。

## 7. 回滚与证据要求

- 每批转换前保存 Git 提交和清单快照；失败时回滚该批，不回滚其他章节或用户未授权改动。
- 保留 hotFix 恢复提交和 `hotfix-html-table-restoration.md` 作为基线证据；不删除原始 stash，直到冲突解决、构建和抽样分发验收完成。
- 验收报告必须分开陈述：源语义一致性、静态结构一致性、站点行为、CHM 编译/显示、DOCX 渲染、PDF 渲染和人工接受。脚本通过不等于视觉或人工接受。
- 全量转换完成的定义是：清单覆盖、所有 `source-content` 表均已迁移为 canonical HTML、所有批次门禁通过、四种分发格式均有抽样证据；未解决风险可以在中途标为暂缓，但不能作为最终永久保留 Markdown 的理由，也不是“所有文件都出现了 `<table>`”这么简单。

## 8. 下一步

1. 高风险源表 24/24 已闭合；继续对本轮修正运行全量 canonical、结构回归、站点 DOM、构建和测试门禁，不再生成用户逐批产物审核任务。
2. 为已闭合的批次形成干净、独立的提交或等价可恢复快照，再把 manifest 中的 `independent_commit_status` 从 `pending_clean_batch_boundary` 升级；不得把当前混合工作树直接冒充独立批次提交。
3. 独立回滚门闭合后，把全量表格数量、结构签名、图片、冲突标记和有损转换保护接入 CI，进入阶段 8。
4. 在最终审计前不删除保留的同步 stash，也不提交或推送未经确认的混合改动。
