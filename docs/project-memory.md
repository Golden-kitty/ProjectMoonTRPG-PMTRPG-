# Project Memory

> 只保留当前阶段仍有效、已确认、值得复用的信息。

## Current Phase
- WinCHM / PDF 到 Markdown 的持续清洗基础上，进入站点优先工作流落地阶段

## Current Focus
- 以 `docs/**/*.md` 为主，持续消除残留 HTML table、占位文档和路径 / 映射漂移
- 保持 Markdown 内容与原始 PDF / CHM 的语义对齐
- 先落地 `MkDocs + GitHub Pages` 站点基线，再为后续 `CHM + Word` 复用导航顺序

## Active Consensus
- 仓库当前可编辑正文位于 `docs/`；`README.md` 将 `docs/PM_TRPG.md` 作为正文入口
- `originFab/Project Moon Trpg Rule Book V1.8.4.pdf` 与 WinCHM 导出结果是关键参考源
- 仓库当前以 GitHub Markdown 渲染为准
- `docs/PDF章节页码映射.md` 用于章节 / 页码 / Markdown 文件之间的核对
- `docs/表格重建清单.md` 是当前最明确的批处理施工清单
- 复杂表格、编码和自动匹配结果仍需要人工复核
- 产物优先级为 `CHM > 在线站点 > Word`，但工程实施顺序采用“先在线站点，后 CHM + Word”
- 特殊背景页 / 样式页暂缓，不进入当前实现范围

## Open Risks
- 复杂 HTML table 无法完全依赖 Pandoc 自动转换
- 个别 PDF 目录项与 Markdown 文件映射仍可能存在歧义或重复候选
- `docs/PDF章节页码映射.md` 中少量一对多映射需要保守处理，避免导航误链到错误页面
- 站点构建采用根目录 `assets/` 复制策略，后续接入 CHM / Word 时仍需确认是否要进一步拆分公开 / 内部资源

## Open Questions
- 站点导航中的少量歧义章节应保持分组节点，还是追加更正式的显式映射表
- 哪些术语和章节结构约束值得提升为长期 `decisions`

## Explicitly Out of Scope
- 不在日常清洗任务中直接编辑 `originFab/` 二进制源文件
- 当前阶段不实现特殊背景页 / Frontmatter 样式体系
- 当前阶段不直接产出 CHM 或 Word

## Recently Accepted Changes
- 在 `Halcyon'edit` 分支接入最小工作流治理层
- 为现有导入说明、清单、映射和审计材料建立工作流映射
- 将新工作流调整为“站点优先”的实施顺序，并以 GitHub Pages 作为第一落地点

## Last Updated
- 2026-03-14
- 引入 `workflow#3` 的 PMTRPG 适配基线
- 确认“先在线站点，后 CHM + Word”的实现顺序
