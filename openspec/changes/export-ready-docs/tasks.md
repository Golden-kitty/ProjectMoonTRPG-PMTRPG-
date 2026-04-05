# Requirement -> Verification Matrix

| Requirement ID | Test / Check |
|----------------|--------------|
| REQ-DER-001 | 导出审计中的关键图片路径检查 + PDF / CHM 样本资源抽查 |
| REQ-DER-002 | 标题结构审计 + 样本导出目录检查 |
| REQ-DER-003 | 样本文件 HTML table 清理 + PDF 抽查 |
| REQ-DER-004 | 编码工件审计 + 样本文件 diff |
| REQ-DER-005 | `scripts/audit_export_readiness.py` |
| REQ-DER-006 | `scripts/export_sample_docs.py --format pdf` / `--format chm` |

## 1. Baseline Docs

- [x] 1.1 新增 `openspec/specs/document-export-readiness/spec.md`；allowed_files: `openspec/specs/document-export-readiness/spec.md`；forbidden_files: `originFab/**`, `assets/**`
- [x] 1.2 新增 export-ready 的 `proposal.md`、`design.md`、`tasks.md`、`longflow.md`、`longflow-state.json`；allowed_files: `openspec/changes/export-ready-docs/**`；forbidden_files: `originFab/**`, `assets/**`
- [x] 1.3 新增 `docs/tasks/T-003-export-ready-docs.md` 与 `docs/acceptance/AC-003-export-ready-docs-acceptance.md`；allowed_files: `docs/tasks/T-003-export-ready-docs.md`, `docs/acceptance/AC-003-export-ready-docs-acceptance.md`；forbidden_files: `originFab/**`

## 2. Audit Tooling

- [x] 2.1 新增导出审计脚本；allowed_files: `scripts/audit_export_readiness.py`；forbidden_files: `originFab/**`, `assets/**`
- [x] 2.2 生成并提交导出阻塞项报告；allowed_files: `docs/acceptance/export-readiness-audit.md`；forbidden_files: `originFab/**`, `assets/**`

## 3. Sample Fixes

- [x] 3.1 修复 `docs/核心规则/基本规则/等级.md` 的 H1、表格与编码问题；allowed_files: `docs/核心规则/基本规则/等级.md`；forbidden_files: `originFab/**`, `assets/**`
- [x] 3.2 修复 `docs/核心规则/速查图表/技能列表.md` 的 H1、图片路径与表格兼容性问题；allowed_files: `docs/核心规则/速查图表/技能列表.md`；forbidden_files: `originFab/**`, `assets/**`
- [x] 3.3 修复 `docs/核心规则/战斗/战斗流程.md` 的导出标题结构与编码工件；allowed_files: `docs/核心规则/战斗/战斗流程.md`；forbidden_files: `originFab/**`, `assets/**`
- [x] 3.4 修复 `docs/资源目录/装备/武器/奇门.md` 的导出标题结构与编码工件；allowed_files: `docs/资源目录/装备/武器/奇门.md`；forbidden_files: `originFab/**`, `assets/**`

## 4. Stub Policy

- [x] 4.1 记录站点空壳页的导出策略；allowed_files: `docs/acceptance/export-readiness-audit.md`, `WORKFLOW_GUIDE.md`；forbidden_files: `originFab/**`

## 5. Sample Export

- [x] 5.1 新增 PDF / CHM 样本导出脚本；allowed_files: `scripts/export_sample_docs.py`；forbidden_files: `originFab/**`, `assets/**`
- [x] 5.2 运行样本 PDF 导出并记录结果；allowed_files: `docs/acceptance/export-sample-verification.md`；forbidden_files: `originFab/**`
- [x] 5.3 运行样本 CHM 项目生成与可选编译并记录结果；allowed_files: `docs/acceptance/export-sample-verification.md`；forbidden_files: `originFab/**`

## 6. Verification

- [x] 6.1 回归 `python scripts/build_site.py build`；allowed_files: `scripts/**`, `docs/**/*.md`；forbidden_files: `originFab/**`
- [x] 6.2 更新 `longflow-state.json` 的验证结果和下一步动作；allowed_files: `openspec/changes/export-ready-docs/longflow-state.json`；forbidden_files: `originFab/**`
