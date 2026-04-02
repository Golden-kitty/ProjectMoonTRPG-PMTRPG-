# llm-long-task-flow Specification

## Purpose

`llm-long-task-flow` 定义“单个 LLM 会话在一个 change 内连续完成 spec / design / apply / verify，并在断线后可恢复”的执行契约。

它用于补充 `dispatch`，适合以下场景：

- 当前 change 更适合串行推进而不是拆给多个子会话
- 用户希望由一个会话直接完成完整链路
- 需要依靠落盘状态文件在中断后继续，而不是重新口头恢复上下文

## Requirements

### Requirement: Single-Change Scope

**Requirement ID:** `REQ-LTF-001`

每个 longflow 会话 MUST 绑定到且仅绑定到一个 change。

#### Acceptance Criteria

1. WHEN 用户启动某个 change 的 longflow THEN 系统 SHALL 仅允许该 change 作为当前上下文
2. IF 同一 change 已在 dispatch 模式下执行 THEN 系统 SHALL 拒绝并行进入 longflow

### Requirement: Persistent State File

**Requirement ID:** `REQ-LTF-002`

longflow MUST 将当前 phase、当前 task、最近验证结果、下一步动作和心跳时间写入机器可解析状态文件。

#### Acceptance Criteria

1. WHEN 会话跨越阶段边界 THEN 系统 SHALL 更新 `longflow-state.json`
2. IF Task 完成或验证完成 THEN 系统 SHALL 记录最近验证结果与 `next_action`

### Requirement: Human-Readable Session Contract

**Requirement ID:** `REQ-LTF-003`

每个 longflow change MUST 提供一个人类和 LLM 都能直接阅读的 `longflow.md`。

#### Acceptance Criteria

1. WHEN 新会话被拉起 THEN 系统 SHALL 提供 `longflow.md`
2. IF 会话需要恢复 THEN `longflow.md` SHALL 包含恢复清单和完成后汇总格式

### Requirement: Deterministic Resume Procedure

**Requirement ID:** `REQ-LTF-004`

恢复会话 MUST 先读取 `openspec/project.md`、change 文档、`longflow.md` 和 `longflow-state.json`，再根据 `next_action` 继续执行。

#### Acceptance Criteria

1. WHEN 会话从中断状态恢复 THEN 系统 SHALL 先读取权威规范与状态文件
2. IF `next_action` 已存在 THEN 恢复会话 SHALL 从该动作继续，而不是重新自由规划整条链路

### Requirement: Local Resume Launcher

**Requirement ID:** `REQ-LTF-005`

系统 MUST 提供本地 launcher，用于根据 longflow 状态拉起或重拉起 Cursor 会话。

#### Acceptance Criteria

1. WHEN 操作者执行 launcher THEN 系统 SHALL 读取 `longflow-state.json`
2. IF 状态文件存在 `resume_prompt` THEN launcher SHALL 使用该提示生成 deeplink

### Requirement: Terminal Statuses

**Requirement ID:** `REQ-LTF-006`

longflow 状态文件 MUST 至少支持 `in_progress`、`blocked`、`awaiting_user`、`completed` 四种状态；launcher 在终止状态下 MUST 停止自动重试。

#### Acceptance Criteria

1. WHEN `status` 进入 `blocked`、`awaiting_user` 或 `completed` THEN launcher SHALL 停止自动重试
2. IF 状态仍为 `in_progress` 且心跳过期 THEN launcher SHALL 允许按策略重拉起

### Requirement: Guardrail Preservation

**Requirement ID:** `REQ-LTF-007`

longflow MUST 保留 OpenSpec 五步、任务边界、`allowed_files` / `forbidden_files` 和验证门禁。

#### Acceptance Criteria

1. WHEN longflow 进入实施 THEN 系统 SHALL 要求设计层已成型
2. IF 当前任务越过 `allowed_files` THEN 会话 SHALL 停止并报告超范围

## State Schema

### Artifact: `longflow-state.json`

最小字段集合如下：

- `change_id`
- `mode`
- `status`
- `current_phase`
- `current_task`
- `last_commit`
- `last_validation`
- `heartbeat_at`
- `next_action`
- `resume_prompt`

### Artifact: `longflow.md`

最小章节集合如下：

- `公共上下文`
- `执行规则`
- `当前任务分解`
- `恢复清单`
- `完成后汇总`

## Scenarios

### Scenario: Fresh longflow execution

1. 用户为某个 change 选择 longflow 模式
2. 会话读取 `openspec/project.md`、change 文档和 `longflow.md`
3. 会话在阶段切换时持续刷新 `longflow-state.json`
4. 完成验证后，状态进入终止状态

### Scenario: Resume after interruption

1. 原会话中断
2. 操作者通过 launcher 或手工 deeplink 拉起新会话
3. 新会话读取 `longflow-state.json` 中的 `next_action`
4. 新会话从指定动作继续，而不是重新猜测上下文

## Invariants

- 一个 longflow 会话只能服务一个 change
- `dispatch` 与 `longflow` 不得对同一 change 并行写状态
- 新会话在开始修改文件前，必须先读取 `longflow-state.json`
- 进入终止状态后，不得在没有显式恢复动作的前提下自动继续推进

## Non-goals

- 本规范不保证系统层面绝对只有一个活跃 Cursor 会话
- 本规范不替代 group dispatch 的并行工作流
- 本规范不定义 PMTRPG 业务正文本身的内容结论
