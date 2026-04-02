## Context

当前仓库是文档型项目，不适合直接照搬面向游戏运行时代码的 OpenSpec 规范。

因此本次接入采用“最小可运行基线”：

- 保留 `dispatch` / `longflow` 的核心执行契约
- 移除与 PMTRPG 当前仓库无关的运行时代码约束
- 让这次接入本身成为一个可 `DryRun` 的示例 change

## Goals

- 在仓库中落地 `openspec/project.md` 作为执行入口
- 提供 dispatch / longflow 启动脚本
- 让当前仓库能够通过示例 change 验证两套 launcher 的基本可用性

## EditableAreas

- `openspec/**`
- `docs/engineering/OPENSPEC_WORKFLOW.md`
- `README.md`
- `WORKFLOW_GUIDE.md`

## ForbiddenAreas

- `originFab/**`
- `assets/**`
- `output/**`
- `docs/**/*.md` 的大规模正文重写

## Decisions

### Decision 1: 保留现有 PMTRPG 治理为上层真相

`README.md`、`docs/project-memory.md`、`docs/project-brief.md` 与现有 `docs/tasks/` / `docs/acceptance/` 继续作为长期背景与任务输入；`openspec/project.md` 只补充跨会话协议。

### Decision 2: 使用当前接入工作作为示例 change

不另造一个空壳示例，而是让本次 change 自己包含 `proposal.md`、`design.md`、`tasks.md`、`longflow.md`、`longflow-state.json` 和一个示例 dispatch 文件。

### Decision 3: 模型路由只保留“文件首行推荐模型”

为了避免把参考项目的大型矩阵照搬进来，本仓库先只要求 dispatch 文件首行写出推荐模型；具体分组策略由主会话结合当前任务决定。

## Acceptance

- `openspec/` 目录存在且结构清晰
- `.\openspec\dispatch-launcher.ps1 -ChangeId "enable-pmtrpg-dispatch-longflow" -DryRun` 成功
- `.\openspec\longflow-launcher.ps1 -ChangeId "enable-pmtrpg-dispatch-longflow" -DryRun` 成功
- `README.md` 与 `WORKFLOW_GUIDE.md` 可定位到新的 OpenSpec 入口

## Open Questions

当前无阻断性 Open Questions。
