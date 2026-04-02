# PMTRPG OpenSpec Workflow

本文说明 PMTRPG 仓库中 `openspec/` 的用途，以及何时使用 `dispatch` 和 `longflow`。

## 适用范围

这套工作流主要服务于以下场景：

- 为当前仓库新增或调整治理文档
- 为脚本、站点构建链或映射流程做边界明确的改动
- 需要把一个 change 交给多个子会话并行执行
- 需要让一个会话在断线后恢复并继续当前 change

它不替代现有 PMTRPG 基础治理，而是把跨会话协作协议落盘到仓库里。

## 与现有材料的关系

- `README.md`：仓库总入口
- `docs/project-memory.md`：长期记忆
- `docs/project-brief.md`：项目简述
- `docs/tasks/`：当前阶段的任务输入
- `docs/acceptance/`：当前阶段的验收输入
- `WORKFLOW_GUIDE.md`：本地构建与发布操作
- `openspec/project.md`：OpenSpec 执行入口

## 目录结构

```text
openspec/
  project.md
  config.yaml
  dispatch-launcher.ps1
  longflow-launcher.ps1
  dispatch/
  changes/
  specs/
```

说明：

- `specs/` 放长期能力契约
- `changes/` 放活跃 change 的 proposal / design / tasks / longflow 状态
- `dispatch/` 放主会话写给子会话的指令文件

## 何时用 Dispatch

适合：

- 一个 change 可以拆成多个边界清晰的子任务
- 子任务之间可以并行，或至少值得拆给不同模型组
- 需要把“允许改哪些文件”明确写给子会话

不适合：

- 当前 change 还没有收敛边界
- 同一任务强依赖连续上下文
- 用户明确要求一个会话做完整条链路

## 何时用 Longflow

适合：

- 一个 change 更适合串行推进
- 用户要求“单会话直接做完整个 change”
- 需要通过状态文件在断线后恢复

不适合：

- 当前 change 更适合并行拆分
- 还没有 proposal / design / tasks 这些基本图纸

## 建议流程

1. 先在 `openspec/specs/` 定义或补齐长期能力 spec
2. 在 `openspec/changes/<change-id>/` 下写 `proposal.md`、`design.md`、`tasks.md`
3. 再决定当前 change 用 `dispatch` 还是 `longflow`
4. 若用 `dispatch`，生成 `openspec/dispatch/<change-id>--<model-tag>.md`
5. 若用 `longflow`，生成 `longflow.md` 和 `longflow-state.json`
6. 执行完成后归档 change

## 常用命令

```powershell
.\openspec\dispatch-launcher.ps1 -ChangeId "enable-pmtrpg-dispatch-longflow" -DryRun
.\openspec\longflow-launcher.ps1 -ChangeId "enable-pmtrpg-dispatch-longflow" -DryRun
```

## PMTRPG 适配原则

- 文档真相优先级仍以 `README.md`、`docs/project-memory.md`、`docs/project-brief.md` 和相关任务/验收文档为准
- `originFab/` 默认只读
- 不因为引入 OpenSpec 就顺手重写 `docs/**/*.md` 正文
- launcher 只是会话拉起辅助，不会自动确认执行
