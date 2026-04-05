# Requirement -> Verification Matrix

| Requirement ID | Test / Check |
|----------------|--------------|
| REQ-DER-001 | `技能列表.md` / `奇门.md` 导出前后对比 + 批次导出资源抽查 |
| REQ-DER-003 | 关键复杂表格转化结果 + PDF / CHM 批次导出 |
| REQ-DER-005 | `scripts/audit_export_readiness.py` |
| REQ-DER-006 | `scripts/export_sample_docs.py` 批次模式 + CHM 真编译尝试 |

## 1. Batch-2 Baseline

- [x] 1.1 新增 `proposal.md`、`design.md`、`tasks.md`、`longflow.md`、`longflow-state.json`；allowed_files: `openspec/changes/export-ready-docs-batch-2/**`；forbidden_files: `originFab/**`, `assets/**`

## 2. Critical Samples

- [x] 2.1 收敛 `docs/核心规则/速查图表/技能列表.md` 的复杂 HTML table；allowed_files: `docs/核心规则/速查图表/技能列表.md`；forbidden_files: `originFab/**`, `assets/**`
- [x] 2.2 收敛 `docs/资源目录/装备/武器/奇门.md` 的重复列与导出结构；allowed_files: `docs/资源目录/装备/武器/奇门.md`；forbidden_files: `originFab/**`, `assets/**`

## 3. CHM Verification

- [x] 3.1 检查并尝试安装真实 CHM 编译工具；allowed_files: `docs/acceptance/export-sample-verification.md`, `openspec/changes/export-ready-docs-batch-2/longflow-state.json`；forbidden_files: `originFab/**`
- [x] 3.2 运行 `scripts/export_sample_docs.py --format chm --compile-chm` 并记录结果；allowed_files: `docs/acceptance/export-sample-verification.md`, `output/**`；forbidden_files: `originFab/**`

## 4. First A-Bucket Batch

- [x] 4.1 挑选 `核心规则` 第一批 10-20 个 A 桶文件；allowed_files: `docs/acceptance/export-readiness-audit.md`, `openspec/changes/export-ready-docs-batch-2/longflow-state.json`；forbidden_files: `originFab/**`
- [x] 4.2 修复第一批文件并记录审计前后差异；allowed_files: `docs/核心规则/**`, `docs/acceptance/export-readiness-audit.md`, `docs/acceptance/export-sample-verification.md`；forbidden_files: `originFab/**`, `assets/**`

## 5. Export Scaling

- [x] 5.1 新增空壳页导出策略说明；allowed_files: `docs/acceptance/export-stub-page-policy.md`, `WORKFLOW_GUIDE.md`；forbidden_files: `originFab/**`
- [x] 5.2 扩展批次导出脚本；allowed_files: `scripts/export_sample_docs.py`；forbidden_files: `originFab/**`, `assets/**`

## 6. Verification

- [x] 6.1 重跑导出审计、批次导出与站点回归；allowed_files: `scripts/**`, `docs/**/*.md`, `output/**`；forbidden_files: `originFab/**`
- [x] 6.2 更新 batch-2 `longflow-state.json`；allowed_files: `openspec/changes/export-ready-docs-batch-2/longflow-state.json`；forbidden_files: `originFab/**`
