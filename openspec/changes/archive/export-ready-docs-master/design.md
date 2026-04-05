## Context

当前仓库已经具备：

- 导出审计脚本
- 批次 PDF / CHM 导出脚本
- 真实 CHM 编译能力
- 第一批 `核心规则` A 桶清理经验

接下来的主要问题不再是“工具是否存在”，而是“如何以低返工方式，按目录和结构类型持续消耗剩余 A/B 桶”。

## Goals

- 为 Batch-3 到 Batch-10 建立统一 longflow 基线
- 把高密度表格页、资源条目页、概览页与 B 桶收口分批推进
- 让每个 batch 都具备 manifest、导出记录与 acceptance 证据

## EditableAreas

- `openspec/changes/export-ready-docs-master/**`
- `openspec/changes/export-ready-docs-batch-2/**`
- `docs/acceptance/**`
- `docs/**/*.md` 中被纳入各批 manifest 的文件
- `scripts/**`
- `WORKFLOW_GUIDE.md`

## ForbiddenAreas

- `originFab/**`
- `assets/**`
- `output/**`
- 未纳入当前 batch 的无关正文批量重写

## Decisions

### Decision 1: 继续按 batch 推进，而不是在一个 change 中做整书一次性清洗

剩余问题的主要风险来自目录差异和表格复杂度差异。继续按 batch 推进，可以保持验收口径稳定，并避免一次性大改导致语义漂移。

### Decision 2: 优先清 A 桶，再收 B 桶与概览页

A 桶决定导出器是否能稳定吃下页面；B 桶与 `Need Overview` 决定整书是否可读。两者不能混成一个批次统一验收。

### Decision 3: 每个 batch 都必须留下独立 acceptance 记录

后续批次体量大、会跨多个会话恢复。只有把审计差异、批次导出结果和剩余风险独立落盘，后续 longflow 才可恢复。

## Work Packages

### WP1: Master Longflow Baseline

- 新增 master change 的 `proposal.md`、`design.md`、`tasks.md`、`longflow.md`、`longflow-state.json`

### WP2: Batch-3 to Batch-8 A-Bucket Drain

- 继续按目录清理 `核心规则`、`创作指南`、`资源目录` 的高密度表格和无标题正文页

### WP3: Batch-9 Overview Convergence

- 收口顶层入口与 `Need Overview` 页面，只补最小概览正文

### WP4: Batch-10 Final B-Bucket Convergence

- 清理剩余无 H1、编码工件、标题噪音，并形成整书候选验证记录

## Acceptance

- master change 文档齐备
- Batch-3 到 Batch-10 均有 manifest / acceptance / state 记录
- A 桶持续下降并接近清零
- B 桶显著收敛
- 至少完成一轮整书候选级批次导出验证
