# Canonical HTML 表格分发试点验收记录

## 当前结论

2026-09-05 的连续用户成品检查确认：CHM 正文内容无误，目录标题编码修复有效；DOCX 行距与 `[黑桃]`、`[梅花]` 等重复替代文字问题也已修复。用户随后确认旧 PDF 在其查看器中依然只显示表格边框和图标，并指出“手术〔双倍〕、内科〔双倍〕、攀爬〔勇气〕、侦查〔自律〕”等写法应使用原书花色图标，而“外科（蜥蜴人）”“考古（废墟发掘）”等括号内容属于技能子类或备注。两项新增问题均已定位并修复，新批次已重新生成；用户在同一任务中复核后明确回复“通过”。

新成品的机器审计为 `PASS`。PDF 已改用 Chromium 从同源 HTML 打印，三个中文字体对象全部嵌入，正确 Unicode 文本层与页面可见性均已验证，11/11 页完成实施者复核；CHM 已在真实 Windows HTML Help 查看器中确认五个中文目录标题正常；DOCX 已在真实 Word 中无修复提示打开，并通过 Microsoft Print to PDF 得到 11 页真实分页结果，11/11 页均已检查。CHM、DOCX、PDF 与技能花色修正现均已获得用户明确接受，试点状态为 **ACCEPTED**。

## 任务边界

- **TaskType**：跨格式分发适配器缺陷修复与成品复核。
- **Goal**：修复 CHM 目录标题编码、PDF 用户端文字不可见、DOCX 行距与图片替代文字重复；按原 PDF 恢复技能属性花色标记，并重新生成可审阅成品。
- **OutOfScope**：修改规则数值或机制、修改 `originFab/`、线上部署、Git 提交或推送、以结构字段存在代替用户视觉确认。
- **Provides**：新版 CHM、DOCX、PDF，CHM 解包与真实查看器截图，DOCX OOXML 指标与 Word 原生渲染证据，PDF 全页渲染和正文覆盖审计。
- **AcceptanceChecks**：表格 ID/数量一致；rowspan/colspan、嵌套表、图片资源保留；CHM 目录中文可读；PDF 中文字体嵌入、Unicode 文本层正确、所有源正文块可提取且页面无丢失；DOCX 表内无重复花色替代文字、图标按原位置混排、行距紧凑；源文件与成品均不残留 `〔勇气〕`、`〔自律〕`、`〔双倍〕` 等旧式标记；备注性括号文本保持不变；未关闭的人工作业独立记录。

## 代表样本

- `核心规则/战斗/重创与疯狂.md`：普通表、长文本和四级标题。
- `创作指南/具现化特性设计.md`：表格前后连续正文与复杂 colspan 模板。
- `资源目录/种族/基本种族.md`：长 rowspan 与 8 列表。
- `核心规则/心灵之光/压迫.md`：嵌套表。
- `核心规则/速查图表/技能列表.md`：42 次图片引用与 colspan 分区。

该集合共包含 19 张表、26 个 colspan 单元格、35 个 rowspan OOXML 槽位、1 张嵌套表、42 次图片引用、4 个唯一图片资源，以及 41 个表格外正文块。

## 缺陷根因与修复

### CHM 目录标题

HTML Help Workshop 4.x 通过 Windows ANSI 代码页读取 `.hhc`/`.hhp` 控制文件。旧导出器把控制文件写成 UTF-8，导致主题 HTML 正文正确、左侧目录标题却乱码。新版将控制文件改为 GBK，并在 `.hhc` 中声明 `gb2312`；主题 HTML 仍保持 UTF-8。

新版编译成功：5 个主题、5 个本地链接、成品约 40.0 KB。生成前控制文件以 GBK 回读时五个中文标题全部精确存在，编译后的 CHM 也已重新解包，19/19 个表格 ID、4 个唯一图片文件和 42 次图片引用均完整。

用户已接受 CHM 正文内容。2026-09-05 用真实 Windows HTML Help 查看器打开新版 CHM，左侧目录中的“重创与疯狂”“具现化特性设计”“基本种族”“压迫”“技能列表”均正常显示，实施者状态为 `PASSED_BY_IMPLEMENTER`。截图见 [`../../output/evidence/table-html-conversion/canonical-table-pilot-chm-viewer-20260905.png`](../../output/evidence/table-html-conversion/canonical-table-pilot-chm-viewer-20260905.png)。

成品：[`../../output/export_samples/canonical-table-pilot/chm/canonical-table-pilot.chm`](../../output/export_samples/canonical-table-pilot/chm/canonical-table-pilot.chm)。

### DOCX 行距与图标重复

旧适配器先把每个 `<img>` 写成 `[alt]` 文本，又把真实图片插入新段落，因此出现 `[黑桃] [梅花]` 与图标重复、图标纵向堆叠和单元格行高增大。

新版行为：

- 本地图片存在时不再输出 `[alt]`；只有图片缺失时才保留文字回退。
- 表格图标改为插入原单元格的同一段落，不再为每个图标新建段落。
- 小图标宽度调整为 0.17 英寸。
- 表格内全部段落设为单倍行距，段前/段后均为 0；正文 Normal 样式为单倍行距、段后 3 磅。

OOXML 审计结果：19 张表、26 个 `gridSpan`、35 个 `vMerge`、42 个 drawing/blip、4 个媒体文件；所有图标均按源顺序进入对应段落，四种花色的方括号替代文字与 `〔勇气〕`、`〔自律〕`、`〔双倍〕` 等旧式标记均为 0。

2026-09-05 用真实 Word 打开新版 DOCX，文件无修复提示。逐页检查首先发现人工章节分页会在自然分页边界制造空白页；现已移除所有强制分页，OOXML 审计确认显式分页符和 `pageBreakBefore` 均为 0。最终由 Word 通过 Microsoft Print to PDF 生成 11 页真实分页结果，11/11 页均已转图检查：空白页 0，未发现单元格裁切、表格越出页面或图片丢失；41/41 个表格外正文块均可提取，4 个唯一图片对象存在。

真实 Word 打印结果进一步确认：“视觉”和“同调率”原有图标仍在同一行；新增修正的“手术/内科/外科/精神”梅花、“攀爬/跳跃/游泳”红心、“侦查”方块，以及四项社会技能梅花均紧随技能名原位显示。`外科（蜥蜴人）`、`考古（废墟发掘）` 等备注仍为普通括号文本。Word 打印结果见 [`../../output/evidence/table-html-conversion/canonical-table-pilot-word-print-20260905-v8.pdf`](../../output/evidence/table-html-conversion/canonical-table-pilot-word-print-20260905-v8.pdf)，11 页总览见 [`../../output/evidence/table-html-conversion/canonical-table-pilot-docx-word-print-pages-20260905-v8/contact-sheet.png`](../../output/evidence/table-html-conversion/canonical-table-pilot-docx-word-print-pages-20260905-v8/contact-sheet.png)。用户最终状态为 `ACCEPTED_BY_USER`。

成品：[`../../output/export_samples/canonical-table-pilot/docx/canonical-table-pilot.docx`](../../output/export_samples/canonical-table-pilot/docx/canonical-table-pilot.docx)。

### PDF 正文完整性

旧 ReportLab 导出器曾存在两层问题：早期版本只遍历 HTML 根层的部分节点，四级至六级标题、容器中的块和其他可见块会被静默跳过；补齐递归遍历后，仍使用未嵌入的 `STSong-Light` CID 字体。本机渲染器会字体代换，所以文字提取和本地截图曾误判为正常，但用户查看器无法代换时只剩表格边框和图标。正式 PDF 适配器现改用本机 Chromium 从同源 HTML 打印，不再使用 ReportLab 作为交付路径。

新版 PDF 为 11 页、约 809 KB，嵌入 3 个 Microsoft YaHei 字体子集，未嵌入的 CJK 字体为 0。五个章节标题、41/41 个表格外正文块和正确 Unicode 文本层均存在；4 个唯一图片对象完整；旧式技能括号标记和方括号替代文字均为 0。

新版 11/11 页已按 2 倍分辨率渲染并逐页检查，正文、表格和图标均可见，未发现裁切、重叠、乱码或空白替代表格；技能标记按原位置显示。用户已在此前发生文字缺失的查看器中完成复核并回复“通过”，最终状态为 `ACCEPTED_BY_USER`。

成品：[`../../output/export_samples/canonical-table-pilot/pdf/canonical-table-pilot.pdf`](../../output/export_samples/canonical-table-pilot/pdf/canonical-table-pilot.pdf)。新版逐页图像与总览见 [`../../output/evidence/table-html-conversion/canonical-table-pilot-pdf-20260905-v5/`](../../output/evidence/table-html-conversion/canonical-table-pilot-pdf-20260905-v5/)。

## 执行与审计

```powershell
$env:Path = 'D:\Database\Project\workrepo\PMTRPG\ProjectMoonTRPG\tools\htmlhelp-workshop;' + $env:Path
python scripts/export_sample_docs.py --format all --compile-chm --batch-name canonical-table-pilot --files '核心规则/战斗/重创与疯狂.md' '创作指南/具现化特性设计.md' '资源目录/种族/基本种族.md' '核心规则/心灵之光/压迫.md' '核心规则/速查图表/技能列表.md'
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/print_docx_with_word.ps1 -DocxPath output/export_samples/canonical-table-pilot/docx/canonical-table-pilot.docx -OutputPdf output/evidence/table-html-conversion/canonical-table-pilot-word-print-20260905-v8.pdf
python scripts/validate_distribution_tables.py --pilot-dir output/export_samples/canonical-table-pilot --batch-name canonical-table-pilot --files '核心规则/战斗/重创与疯狂.md' '创作指南/具现化特性设计.md' '资源目录/种族/基本种族.md' '核心规则/心灵之光/压迫.md' '核心规则/速查图表/技能列表.md' --chm-decompiled output/export_samples/canonical-table-pilot/chm-decompiled-20260905-v7 --docx-word-print output/evidence/table-html-conversion/canonical-table-pilot-word-print-20260905-v8.pdf --chm-payload-visual-status accepted_by_user --chm-viewer-status accepted_by_user --docx-open-status passed --docx-page-visual-status accepted_by_user --pdf-visual-status accepted_by_user --report docs/engineering/canonical-table-distribution-audit.json
python -m unittest discover -s tests -p 'test_*.py' -v
```

[`../engineering/canonical-table-distribution-audit.json`](../engineering/canonical-table-distribution-audit.json) 当前为 `PASS`、问题数 0；24/24 项试点相关单元测试通过。机器门、实施者门和用户产品门均已通过。

## 人工复核结论

用户已依次确认 CHM 内容与目录、DOCX 行距与重复替代文字、新版 PDF 正文可见性，以及技能花色标记修正，试点人工复核队列现为 0。该结论关闭阶段 6 的四格式试点门，并作为阶段 7 中这 5 个文档、19 张表的接受依据；其本身不自动扩展为其他表已完成人工语义复核。随后用户另行确认“产物样例通过后不再逐批审核，原文 HTML 重点审核高风险部分”，该后续范围调整由 [`canonical-table-review-policy.json`](../engineering/canonical-table-review-policy.json) 和 [`canonical-table-high-risk-source-review.md`](canonical-table-high-risk-source-review.md) 记录。
