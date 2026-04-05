# Requirement -> Verification Matrix

| Requirement ID | Test / Check |
|----------------|--------------|
| REQ-DER-002 | 各 batch 目标文件的 H1 / 标题结构回归 |
| REQ-DER-003 | 各 batch 的表格转化结果 + PDF / CHM 批次导出 |
| REQ-DER-005 | `scripts/audit_export_readiness.py` |
| REQ-DER-006 | `scripts/export_sample_docs.py` 批次模式 + CHM 真编译 |

## 1. Master Baseline

- [x] 1.1 新增 master change 图纸与状态文件；allowed_files: `openspec/changes/export-ready-docs-master/**`；forbidden_files: `originFab/**`, `assets/**`

## 2. Batch-3 ~ Batch-8

- [x] 2.1 清理 `核心规则` 高密度规则表；allowed_files: `docs/核心规则/**`, `docs/acceptance/**`；forbidden_files: `originFab/**`, `assets/**`
- [x] 2.2 清理 `创作指南` 目录结构与表格页；allowed_files: `docs/创作指南/**`, `docs/acceptance/**`；forbidden_files: `originFab/**`, `assets/**`
- [x] 2.3 清理 `资源目录` 下课程、装备、消耗品、改造、种族、工坊、出身、强化等目录；allowed_files: `docs/资源目录/**`, `docs/acceptance/**`；forbidden_files: `originFab/**`, `assets/**`

## 3. Batch-9 Overview

- [x] 3.1 收口顶层入口与 `Need Overview` 页；allowed_files: `docs/*.md`, `docs/核心规则*.md`, `docs/acceptance/**`；forbidden_files: `originFab/**`

## 4. Batch-10 Final Verification

- [x] 4.1 清理剩余 B 桶并形成整书候选验证记录；allowed_files: `docs/**/*.md`, `docs/acceptance/**`, `scripts/**`；forbidden_files: `originFab/**`, `assets/**`
- [x] 4.2 更新 master `longflow-state.json`；allowed_files: `openspec/changes/export-ready-docs-master/longflow-state.json`；forbidden_files: `originFab/**`
