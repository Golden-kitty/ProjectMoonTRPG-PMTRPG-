# export-ready-docs-master

## Why

`export-ready-docs` 与 `export-ready-docs-batch-2` 已完成导出基线、真实 CHM 编译验证与第一批 A 桶清理，但仓库中仍剩余大量成批出现的导出结构债务。

当前需要的不是再开一条短期样本修复线，而是一条覆盖后续所有 batch 的主 longflow，用于持续消耗：

- `核心规则` 中的高密度规则表
- `创作指南` 与 `资源目录` 中的大量条目表
- 顶层概览页与 `Need Overview` 结构页
- 剩余 B 桶中的无 H1、编码工件与标题噪音

## What Changes

- 新建 master change，统领 Batch-3 到 Batch-10
- 为每个 batch 建立文件清单、验收记录与状态推进规则
- 扩展批量清洗与批次导出能力，支持持续回归
- 在不改动 `originFab/` 的前提下，把剩余 A/B 桶推进到整书候选可验证状态

## OutOfScope

- 不直接交付最终 PDF / CHM 成品样式
- 不做整仓视觉美化
- 不编辑 `originFab/`、`assets/` 原始素材本体

## Provides

- 一条覆盖后续所有 batch 的导出就绪主 longflow
- 一组可恢复的 batch manifests 与 acceptance 证据
- 面向整书候选验证的阶段性收口路线
