# 全量 HTML 表格：本地站点验收记录

## 验收结论

**ACCEPTED**。用户于 2026-09-04（Asia/Shanghai）确认“这组站点表格可以接受”。本记录据此关闭全量 HTML 表格转换计划中的**本地站点视觉验收门**。

该结论只覆盖本地 MkDocs 站点中代表性表格在桌面端与 390px 移动端的实际显示，不扩大解释为 CHM、DOCX、PDF、线上部署或整项计划已经验收。

## 任务边界

- **TaskType**：人工验收记录。
- **Goal**：固化用户对本地站点表格显示效果的接受结论。
- **OutOfScope**：CHM 编译与显示、DOCX 渲染、PDF 渲染、线上部署、Git 提交或推送，以及规则语义改写。
- **Provides**：站点构建、DOM 结构回归、桌面端与移动端截图，以及用户明确接受意见。
- **AcceptanceChecks**：canonical 结构通过；站点构建通过；369 个规则正文表的渲染 DOM 可定位且结构一致；代表性桌面端与移动端页面无页面级横向溢出；用户确认可接受。

## 验收证据

- canonical 审计：[`../engineering/canonical-table-final-audit.json`](../engineering/canonical-table-final-audit.json)，`PASS`，问题数 0。
- 渲染 DOM 审计：[`../engineering/rendered-table-audit.json`](../engineering/rendered-table-audit.json)，369/369 个稳定表格 ID 可定位，结构差异 0。
- 转换与构建摘要：[`../engineering/local-html-conversion-preview.md`](../engineering/local-html-conversion-preview.md)。
- 桌面端截图：[`../../output/evidence/table-html-conversion/重创与疯狂-desktop.png`](../../output/evidence/table-html-conversion/重创与疯狂-desktop.png)。
- 390px 移动端截图：[`../../output/evidence/table-html-conversion/重创与疯狂-mobile.png`](../../output/evidence/table-html-conversion/重创与疯狂-mobile.png)。
- 人工结论：用户在当前任务中明确回复“这组站点表格可以接受”。

## 尚未关闭的门禁

- CHM：需要真实编译、资源/主题计数、解包检查和代表性页面显示证据。
- DOCX：需要 OOXML span 检查、实际渲染逐页检查和图片可见性证据。
- PDF：需要逐页图像检查，确认表格不越界、不重叠、不丢文本，并记录必要降级。
- 最终验收：需要汇总四种分发格式的证据和遗留风险后另行确认。

## 基线说明

验收发生在 `Halcyon'edit` 工作树与 `origin/hotFix` 同步至 `d3fc747d6ad36c0d8cba61fda37d19246482bfe3` 的基线上。工作树仍含本计划转换及用户既有的未提交改动；本验收记录本身不授权提交、推送或清理这些改动。
