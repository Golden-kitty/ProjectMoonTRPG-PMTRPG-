# 长任务流会话指令 - enable-pmtrpg-dispatch-longflow

> 本文件用于 PMTRPG 仓库的 longflow 示例。
> 恢复会话时，必须先读取 `openspec/project.md` 与同目录下的 `longflow-state.json`。

## 公共上下文

- **Change ID**：`enable-pmtrpg-dispatch-longflow`
- **执行模式**：`longflow`
- **相关文件**：
  - `openspec/project.md`
  - `openspec/specs/llm-task-dispatch/spec.md`
  - `openspec/specs/llm-long-task-flow/spec.md`
  - `openspec/changes/enable-pmtrpg-dispatch-longflow/proposal.md`
  - `openspec/changes/enable-pmtrpg-dispatch-longflow/design.md`
  - `openspec/changes/enable-pmtrpg-dispatch-longflow/tasks.md`
- **实施目标文件**：
  - `openspec/**`
  - `docs/engineering/OPENSPEC_WORKFLOW.md`
  - `README.md`
  - `WORKFLOW_GUIDE.md`

## 执行规则

1. 先读 `openspec/project.md`
2. 只处理当前 change，禁止顺手开启第二个 change
3. 超出当前 change 边界时，停止并报告
4. 每次阶段切换或验证完成后刷新 `longflow-state.json`

## 当前任务分解

1. 落地 OpenSpec 基线文件
2. 补齐两份工作流 spec
3. 新增 dispatch / longflow launcher
4. 为本次接入生成示例 change 和 dispatch 文件
5. 更新仓库入口文档并执行 `DryRun`

## 恢复清单

1. 阅读 `openspec/project.md`
2. 阅读当前 change 的 `proposal.md` / `design.md` / `tasks.md`
3. 阅读 `longflow.md`
4. 阅读 `longflow-state.json`
5. 运行 `git status --short`
6. 按 `next_action` 继续

## 完成后汇总

完成后至少汇总：

- 已生成或更新的文件
- `dispatch-launcher` 验证结果
- `longflow-launcher` 验证结果
- 剩余风险或后续建议
