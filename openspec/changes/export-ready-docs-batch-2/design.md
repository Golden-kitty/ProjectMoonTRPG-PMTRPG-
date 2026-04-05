## Context

上一条 `export-ready-docs` change 已完成 baseline：

- 导出审计脚本与报告已存在
- 样本 PDF 已能生成
- CHM 项目文件已能生成
- 样本页 `等级.md`、`战斗流程.md`、`技能列表.md`、`奇门.md` 已做第一轮修复

Batch-2 的重点不再是“证明问题存在”，而是把剩余风险转化为可持续推进的批次。

## Goals

- 收敛两个最危险的复杂样本页
- 完成真实 CHM 编译验证，或明确记录环境阻塞
- 启动第一批 A 桶处理
- 把导出脚本提升到批次导出能力

## EditableAreas

- `openspec/changes/export-ready-docs-batch-2/**`
- `docs/核心规则/速查图表/技能列表.md`
- `docs/资源目录/装备/武器/奇门.md`
- `docs/acceptance/**`
- `scripts/**`
- `WORKFLOW_GUIDE.md`
- 第一批 A 桶所涉及文件

## ForbiddenAreas

- `originFab/**`
- `assets/**`
- `output/**`
- 未纳入 batch-2 的大规模正文重写

## Decisions

### Decision 1: 继续以批次推进，而不是扩展 baseline change

`export-ready-docs` 已完成，不再继续向其追加大规模后续工作。Batch-2 独立记录自己的 phase、证据与恢复点。

### Decision 2: 先处理样本页，再扩 A 桶

`技能列表.md` 和 `奇门.md` 仍然是最能代表后续整批导出风险的页面。先把最复杂的样本页收敛，再把经验复制到 A 桶第一批。

### Decision 3: CHM 编译验证必须独立留痕

CHM 真编译是当前 baseline 中唯一未闭环的部分。即使外部工具安装失败，也必须在验收记录和 state 中保留真实证据。

## Work Packages

### WP1: Batch-2 Longflow Baseline

- 新增 batch-2 的 `proposal.md`、`design.md`、`tasks.md`、`longflow.md`、`longflow-state.json`

### WP2: Critical Sample Pages

- 进一步重构 `技能列表.md`
- 进一步重构 `奇门.md`
- 重跑样本导出并记录前后差异

### WP3: Real CHM Verification

- 检查并尝试安装 `hhc`
- 用 `scripts/export_sample_docs.py --format chm --compile-chm` 做真实验证

### WP4: First A-Bucket Batch

- 从 `docs/acceptance/export-readiness-audit.md` 中挑选 `核心规则` 第一批 10-20 个文件
- 修复 HTML table / 标题结构 / 编码问题
- 重跑审计并记录差异

### WP5: Export Scaling

- 补空壳页导出策略
- 扩展批次导出脚本，使其支持指定文件列表或批次

## Acceptance

- batch-2 change 文档齐备
- `技能列表.md` 与 `奇门.md` 导出质量显著改善
- CHM 真编译已完成，或明确记录环境阻塞
- A 桶已完成至少第一批清理
- 批次导出脚本可针对指定页面集运行
- batch-2 的 `longflow-state.json` 已记录最近验证结果

## Open Questions

当前没有阻断实施的设计问题；若 `hhc` 不可安装，将以“环境阻塞但证据充分”方式收束该阶段。
