# enable-pmtrpg-dispatch-longflow

## Why

PMTRPG 仓库已经有最小治理文档、任务文档和站点优先工作流，但还没有把多会话协作协议显式落盘到仓库内。

结果是：

- 需要分发任务时，没有统一的 dispatch 文件目录、格式和 launcher
- 需要单会话串行推进并支持断线恢复时，没有 longflow 状态文件和恢复入口
- 新会话很难快速分辨哪些规则来自现有 PMTRPG 治理，哪些属于本次 change 的执行边界

## What Changes

- 新增 `openspec/` 基线目录与项目入口文档
- 新增 `dispatch` / `longflow` 两套 launcher
- 新增 `llm-task-dispatch` 与 `llm-long-task-flow` 两份能力 spec
- 新增一份 PMTRPG 适配说明文档
- 为当前 change 自身补一份 longflow 状态与一个示例 dispatch 文件

## OutOfScope

- 不大规模重写 `docs/**/*.md` 正文
- 不修改 `originFab/`
- 不引入后台服务或自动确认执行机制
- 不复制参考项目的整套模型路由矩阵

## Provides

- 仓库内可引用的 OpenSpec 入口与能力 spec
- 可 `DryRun` 的 dispatch / longflow launcher
- 一份可供后续 change 复用的示例 change 骨架
