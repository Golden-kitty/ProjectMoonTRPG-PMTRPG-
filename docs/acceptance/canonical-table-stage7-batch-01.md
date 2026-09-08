# Canonical HTML 阶段 7 第 1 批验收记录

## 当前结论

**SOURCE/ARTIFACT REVIEW CLOSED**。`stage7-batch-01` 包含 14 个文档、30 张表；机器结构与四格式生成均通过，Chromium PDF 和 Word 实际分页也已完成实施者视觉检查。用户于 2026-09-05 明确确认代表性产物样例通过后不再逐批审核 CHM/DOCX/PDF，因此本批不再保留 28 张用户语义复核门：2 张试点表为 `accepted_by_user`，27 张普通表为 `closed_by_user_review_policy`，`等级.md` 的 11 列宽表 `html-1790361cb39e` 已按原 PDF 文件页 15 和原 CHM 完成核对，标为 `source_verified_by_high_risk_review`。

## 任务边界

- **TaskType**：阶段 7 批次产物回归与高风险源表路由。
- **Goal**：证明本批仍可由已通过的分发适配器消费，并把真正需要原文核对的结构风险转入集中队列。
- **OutOfScope**：要求用户重复审核本批产物、修改规则机制、再次验收已接受的 2 张试点表、把当前混合工作树冒充独立批次提交、推送或部署。
- **Provides**：独立 HTML、CHM、DOCX、PDF，Word 实际打印结果，全页渲染总览，表级 JSON manifest 与按风险分类的 CSV 队列。
- **AcceptanceChecks**：30/30 表结构存在；125/125 个正文块在 PDF 与 Word 打印中可提取；中文字体嵌入；页面无正文丢失、表格越界、裁切或异常空白；高风险源表进入集中原文复核记录。

## 批次范围

- `docs/创作指南/强化类设计.md`：3 张，章节页候选 P331。
- `docs/核心规则/创建角色/战斗配置/战技与战技栏.md`：1 张，章节页候选 P36。
- `docs/核心规则/创建角色/战斗配置/物品与物品栏.md`：1 张，章节页候选 P35。
- `docs/核心规则/创建角色/战斗配置/特质与特质栏.md`：3 张，章节页候选 P37。
- `docs/核心规则/基本规则/等级.md`：1 张，章节页候选 P15。
- `docs/核心规则/心灵之光/心灵侵蚀.md`：1 张，章节页候选 P68。
- `docs/核心规则/心灵之光/情感.md`：2 张，章节页候选 P66。
- `docs/核心规则/心灵之光/神备和扭曲.md`：1 张，章节页候选 P70。
- `docs/核心规则/战斗/战后.md`：1 张，章节页候选 P94。
- `docs/核心规则/战斗/拼点.md`：2 张，章节页候选 P88。
- `docs/核心规则/购买项/强化类/义体与植入物类.md`：2 张，章节页候选 P48。
- `docs/核心规则/购买项/装备类/武器类与武器属性.md`：5 张，章节页候选 P41。
- `docs/核心规则/速查图表/战斗速查.md`：5 张，章节页候选 P125。

另有 `docs/核心规则/战斗/重创与疯狂.md` 的 2 张表，已由 `canonical-table-pilot-20260905` 接受。其余普通表不再要求用户逐表复核；`docs/核心规则/基本规则/等级.md` 的 `html-1790361cb39e` 因 11 列宽度进入集中高风险队列后也已完成核对。

以上页码是现有章节映射候选，用于定位原 PDF；只有高风险项在实际对照后才写入表级精确页码和复核结论，不把章节入口页伪装成已经逐表核准的精确页码。

## 机器与实施者证据

- 全量 canonical 审计：`PASS`，369 张正文表问题数 0。
- 站点 DOM：`PASS`，369/369 张表、92 个页面，结构差异 0。
- 本批跨格式审计：`PASS`，30/30 张表，问题数 0。
- CHM：14 个主题、30 张表，真实编译成功，47,067 字节。
- DOCX：30 张表，真实 Word 打开并打印为 15 页；125/125 个正文块存在。
- PDF：23 页、10,223 个可提取字符、125/125 个正文块、3 个嵌入的 Microsoft YaHei 字体子集，未嵌入 CJK 字体为 0。
- 实施者逐页检查：PDF 23 页和 Word 打印 15 页均无正文丢失、表格越界、裁切或异常空白；跨页表在 Word 下一页保留表头。

## 成品与清单

- HTML：`output/export_samples/stage7-batch-01/pdf/stage7-batch-01.html`
- CHM：`output/export_samples/stage7-batch-01/chm/stage7-batch-01.chm`
- DOCX：`output/export_samples/stage7-batch-01/docx/stage7-batch-01.docx`
- PDF：`output/export_samples/stage7-batch-01/pdf/stage7-batch-01.pdf`
- Word 打印：`output/evidence/table-html-conversion/stage7-batch-01-word-print-20260905.pdf`
- PDF 总览：`output/evidence/table-html-conversion/stage7-batch-01-pdf-20260905/contact-sheet.png`
- Word 总览：`output/evidence/table-html-conversion/stage7-batch-01-docx-word-print-pages-20260905/contact-sheet.png`
- 表级 manifest：`docs/engineering/table-rollout-batches/stage7-batch-01.json`
- 跨格式审计：`docs/engineering/table-rollout-batches/stage7-batch-01-audit.json`
- 全量人工复核队列：`output/spreadsheet/canonical-table-stage7-review-queue.csv`

## 未关闭门禁

1. 当前工作树混有既有转换和用户改动；本批尚未形成干净独立提交，因此 `independent_commit_status` 仍为 `pending_clean_batch_boundary`。
