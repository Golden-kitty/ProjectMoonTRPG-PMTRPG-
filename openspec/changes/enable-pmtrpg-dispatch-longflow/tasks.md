# Requirement -> Verification Matrix

| Requirement ID | Test / Check |
|----------------|--------------|
| REQ-LTD-004 | `dispatch-launcher.ps1 -DryRun` |
| REQ-LTF-005 | `longflow-launcher.ps1 -DryRun` |
| REQ-LTF-006 | `longflow-launcher.ps1 -DryRun` 输出终止状态摘要 |

## 1. OpenSpec Baseline

- [x] 1.1 新增 `openspec/project.md` 与 `openspec/config.yaml`；allowed_files: `openspec/project.md`, `openspec/config.yaml`；forbidden_files: `originFab/**`, `docs/**/*.md`
- [x] 1.2 新增 `llm-task-dispatch` 与 `llm-long-task-flow` spec；allowed_files: `openspec/specs/**`；forbidden_files: `originFab/**`, `docs/**/*.md`

## 2. Tooling

- [x] 2.1 新增 `openspec/dispatch-launcher.ps1`；allowed_files: `openspec/dispatch-launcher.ps1`；forbidden_files: `originFab/**`, `docs/**/*.md`
- [x] 2.2 新增 `openspec/longflow-launcher.ps1`；allowed_files: `openspec/longflow-launcher.ps1`；forbidden_files: `originFab/**`, `docs/**/*.md`

## 3. Example Change

- [x] 3.1 为当前 change 新增 `proposal.md`、`design.md`、`tasks.md`、`longflow.md`、`longflow-state.json`；allowed_files: `openspec/changes/enable-pmtrpg-dispatch-longflow/**`；forbidden_files: `originFab/**`, `docs/**/*.md`
- [x] 3.2 新增一个示例 dispatch 文件；allowed_files: `openspec/dispatch/enable-pmtrpg-dispatch-longflow--codex.md`；forbidden_files: `originFab/**`, `docs/**/*.md`

## 4. Documentation & Verification

- [x] 4.1 新增 `docs/engineering/OPENSPEC_WORKFLOW.md` 并更新入口文档；allowed_files: `docs/engineering/OPENSPEC_WORKFLOW.md`, `README.md`, `WORKFLOW_GUIDE.md`；forbidden_files: `originFab/**`
- [x] 4.2 运行两个 launcher 的 `-DryRun` 做人工验证；allowed_files: `openspec/**`；forbidden_files: `originFab/**`
