## Context

当前仓库的强项是站点优先构建链，而不是导出就绪链。

这意味着：

- `mkdocs.yml` 能保证站点导航，但不能保证 PDF / CHM 的目录结构
- `scripts/mkdocs_hooks.py` 能修正站点图片路径，但导出器不会自动继承这层修正
- 站点分组页可接受为占位节点，但在 PDF / CHM 中会退化为空白章节

## Goals

- 为 PDF / CHM 样本导出建立独立于站点的质量门禁
- 将最小样本集从“站点可看”修到“导出可用”
- 为后续整书导出保留清晰的施工清单和恢复状态

## EditableAreas

- `openspec/specs/**`
- `openspec/changes/export-ready-docs/**`
- `docs/tasks/T-003-export-ready-docs.md`
- `docs/acceptance/AC-003-export-ready-docs-acceptance.md`
- `docs/**/*.md` 中纳入样本与阻塞修复的文件
- `scripts/**`
- `WORKFLOW_GUIDE.md`

## ForbiddenAreas

- `originFab/**`
- `assets/**`
- `output/**`
- 未纳入样本与阻塞修复清单的正文批量重写

## Decisions

### Decision 1: 以样本导出而非整书导出作为本次通过线

当前最大风险来自源文档结构债务，而不是最终打包参数。因此先建立覆盖复杂表格、图片、叙述页和资源页的样本集，优先验证兼容性。

### Decision 2: 将问题分为阻塞项、退化项和站点占位项

同样是“站点没问题”的现象，背后的导出风险不同：

- 阻塞项必须优先修复，如关键图片路径、无 H1、HTML table
- 退化项可以在样本导出中先确认是否接受，如 `\xa0`、表格内 `<br>`
- 站点占位项必须明确是否补概览正文或从导出中排除

### Decision 3: 导出链与站点链并行存在，但验证口径分离

保留 Site-First 基线不变，同时新增独立审计与样本导出脚本。站点构建继续作为回归点，但不再充当导出通过证据。

## Work Packages

### WP1: Longflow Baseline

- 新增 export-ready spec、任务文档、验收文档和 change 图纸
- 建立 `longflow.md` 与 `longflow-state.json`

### WP2: Export Audit

- 新增导出审计脚本
- 统计并分桶 HTML table、标题结构、编码工件、空壳页和图片路径依赖

### WP3: Sample Fixes

- 先修样本集与阻塞共性问题
- 目标文件：
  - `docs/核心规则/基本规则/等级.md`
  - `docs/核心规则/速查图表/技能列表.md`
  - `docs/核心规则/战斗/战斗流程.md`
  - `docs/资源目录/装备/武器/奇门.md`

### WP4: Sample Export & Verification

- 新增 PDF 样本导出脚本
- 新增 CHM 样本导出脚本 / 项目文件生成
- 记录人工对照结果，并更新 `longflow-state.json`

## Acceptance

- export-ready change 文档与 spec 已落盘
- 导出审计脚本能产出稳定结果
- 样本页的关键图片路径、H1、关键表格和编码问题已处理
- PDF 样本导出成功
- CHM 样本项目文件生成成功；若编译器可用，则编译成功
- `build_site.py build` 仍可成功

## Open Questions

当前没有阻断本次 change 的设计级问题；CHM 编译器是否安装属于执行环境差异，需在验证阶段如实记录。
