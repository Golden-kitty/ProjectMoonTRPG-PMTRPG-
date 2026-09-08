# 本地全量 HTML 表示转换与站点预览

## 当前结论

规则正文的表格表示层已经完成本地全量转换：369/369 个 `source-content` 表均为 HTML，并具有稳定、唯一的 `data-table-id`。当前仍存在的 20 个 Markdown 管线表全部位于工程或验收记录中，不是规则正文迁移对象；较阶段 0 多出的 1 张是本轮高风险复核记录中的证据表。

严格 canonical 审计曾剩 83 项，集中在 12 张表；现已对照 PDF P119、P136、P138、P213、P334、P340 完成复核与修正，严格审计已清零。用户于 2026-09-04 接受了本地站点中这组表格的桌面端与移动端表现，并于 2026-09-05 接受修复后的 CHM、DOCX、PDF 四格式试点和技能花色标记；随后确认代表性产物样例通过后不再逐批审核产物，原文 HTML 仅重点审核高风险项。阶段 6 已关闭；阶段 7 已把 369 张表分成 12 个文档原子批次，其中 19 张由用户接受、7 张非重叠表由既有 PDF 对照证据闭合、24 张高风险源表由 Codex 完成 PDF/CHM 对照、319 张普通表按策略关闭，当前待核为 0。高风险修正与保留差异见 [`canonical-table-high-risk-source-review.md`](../acceptance/canonical-table-high-risk-source-review.md)。

## 已执行的本地转换

- 将 16 个规则文档中的 26 个 Markdown 管线表转换为带 `<thead>`、`<tbody>`、`scope` 和稳定 ID 的 HTML。
- 为 82 个文档中的 343 个既有 HTML 表写入冻结 ID 和 `pmtrpg-table` class。
- 从 326 个表移除 `border`、`width` 等旧表现属性，表现统一转入站点 CSS。
- 修复 5 个文档中的 6 处明显行/单元格闭合错误；修复 8 个旧单元格表现属性，不改变规则文本、span 或图片。
- 增加响应式表格 CSS；桌面与 390px 移动宽度均无页面级横向溢出。

## 机器证据

- 单元测试：15/15 通过。
- 源结构回归：`PASS`，369 个规则表相对冻结清单 0 个结构变化。
- MkDocs 严格构建：成功；保留既有的 `project-terminology.md` 未进入导航提示和 Material 未来版本提示。
- 渲染 DOM：`PASS`，369/369 个稳定 ID 均可定位，覆盖 92 个页面；行列数、span、嵌套关系和图片引用 0 个差异。
- 严格 canonical 审计：从转换前 1369 项降至 0，当前 `PASS`。

机器结果分别见 [`table-structure-regression.json`](table-structure-regression.json)、[`rendered-table-audit.json`](rendered-table-audit.json) 和 [`canonical-table-audit.json`](canonical-table-audit.json)。

## 已由 PDF 证据闭合的 12 张表

已结合 PDF 复核并修正网格宽度的 11 张表分布如下：

- `docs/创作指南/具现化特性设计.md`：1 张，章节候选 P333；局部行宽 6/7。
- `docs/创作指南/资源设计表格.md`：1 张，章节候选 P335；局部行宽 6/7。
- `docs/资源目录/出身/传统武人.md`：2 张，章节候选 P138；主体行宽 7、末两行宽 8。
- `docs/资源目录/出身/基础出身.md`：4 张，章节候选 P136；主体行宽 7、末两行宽 8。
- `docs/资源目录/种族/基本种族.md`：3 张，章节候选 P213；含一个单独起行的纵向合并说明格，需要确认这是刻意留白还是遗漏单元格。

已按 PDF 图例补齐图片替代文本的 1 张表：

- `docs/核心规则/速查图表/技能列表.md`：精确来源 P119；同一表内 23 个技能图标承载花色信息，已分别填写“黑桃、红心、方块、梅花”短文本。

修正均以 PDF 视觉结构为依据：具现化模板按 6 列网格重建，基础/传统出身按 8 列网格补齐 span，基本种族将纵向说明格与首个属性行置于同一行；技能图标按 PDF 图例写入“黑桃、红心、方块、梅花”替代文本。修正前后的 12 项结构差异保存在 [`pdf-confirmed-structure-diff.json`](pdf-confirmed-structure-diff.json)，没有把规则文字或数值作为格式副作用改写。

## 可视证据

代表性页面“重创与疯狂”原来包含两个 Markdown 管线表，现已在本地站点渲染为 canonical HTML：

- [桌面截图](../../output/evidence/table-html-conversion/重创与疯狂-desktop.png)
- [390px 移动端截图](../../output/evidence/table-html-conversion/重创与疯狂-mobile.png)

用户已于 2026-09-04 确认这组站点表格可以接受，详见 [`html-table-site-acceptance.md`](../acceptance/html-table-site-acceptance.md)。该结论只关闭站点视觉门；CHM、DOCX、PDF 仍须分别提供实际分发成品与渲染证据。

## 分发试点进展

站点接受后，已选取普通表、colspan、rowspan、嵌套表和图片表共五个代表文档，生成 CHM、DOCX、PDF 成品并完成跨格式结构审计。修复后的 PDF 为 11 页并嵌入中文字体；CHM 完成真实编译、解包和 Windows HTML Help 查看；DOCX 完成 OOXML 对照、Word 原生打开和 11 页打印复核。用户已确认新版产物“通过”，完整记录见 [`canonical-table-distribution-pilot.md`](../acceptance/canonical-table-distribution-pilot.md)。后续分批状态见 [`canonical-table-stage7.md`](canonical-table-stage7.md)。
