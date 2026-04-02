# llm-task-dispatch Specification

## Purpose

`llm-task-dispatch` 定义 PMTRPG 仓库中“一个主会话把当前 change 的子任务分发给多个 Cursor 子会话”的执行契约。

它的目标是让文档治理、脚本边界清晰的子任务可以按模型或分组拆开执行，同时保留可追踪的文件边界与汇总格式。

## Requirements

### Requirement: Change-Scoped Dispatch Files

**Requirement ID:** `REQ-LTD-001`

每个 dispatch 文件 MUST 绑定到且仅绑定到一个 change。

#### Acceptance Criteria

1. WHEN 主会话生成 dispatch 文件 THEN 文件路径 SHALL 位于 `openspec/dispatch/<change-id>--<model-tag>.md`
2. IF 子会话开始执行 THEN 子会话 SHALL 只读取并执行该文件内列出的子任务

### Requirement: One File Per Model Group

**Requirement ID:** `REQ-LTD-002`

同一模型组的子任务 MUST 合并到一个 dispatch 文件中，避免同一模型重复开启多个会话。

#### Acceptance Criteria

1. WHEN 主会话按模型分组 THEN 同组任务 SHALL 合并到同一个 dispatch 文件
2. IF 子任务属于不同模型组 THEN 系统 SHALL 使用不同 dispatch 文件

### Requirement: Explicit File Boundaries

**Requirement ID:** `REQ-LTD-003`

每个 dispatch 文件 MUST 显式写出公共上下文、允许修改文件、禁止修改行为和完成后汇总格式。

#### Acceptance Criteria

1. WHEN dispatch 文件被创建 THEN 文件 SHALL 包含 `公共上下文`、`执行规则` 与 `完成后汇总` 章节
2. IF 某个子任务可能越界 THEN 文件 SHALL 提前写出 `allowed_files` 或等价文件边界

### Requirement: Launcher Availability

**Requirement ID:** `REQ-LTD-004`

仓库 MUST 提供本地 launcher，用于根据 `change-id` 扫描 dispatch 文件并拉起 Cursor 子会话。

#### Acceptance Criteria

1. WHEN 操作者运行 `dispatch-launcher.ps1` THEN 系统 SHALL 扫描 `openspec/dispatch/` 下匹配文件
2. IF 找到匹配文件 THEN launcher SHALL 为每个文件构造 deeplink

### Requirement: No Prompt-Only Distribution

**Requirement ID:** `REQ-LTD-005`

主会话 MUST NOT 只在聊天中输出裸提示词而不落盘 dispatch 文件。

#### Acceptance Criteria

1. WHEN 用户请求分发 THEN 主会话 SHALL 先生成 dispatch 文件
2. IF 只存在聊天中的临时提示而没有仓库内文件 THEN 当前分发 SHALL NOT 视为完成

### Requirement: Longflow Mutual Exclusion

**Requirement ID:** `REQ-LTD-006`

dispatch 与 longflow MUST NOT 同时作用于同一个 change。

#### Acceptance Criteria

1. WHEN 某个 change 已进入 longflow THEN 系统 SHALL 拒绝并行生成面向同一 change 的 dispatch 执行链
2. IF 当前 change 已由 dispatch 模式拆分执行 THEN 系统 SHALL 不再把它声明为正在 longflow 中

## Scenarios

### Scenario: 主会话分发文档任务

1. 主会话读取当前 change 的 `tasks.md`
2. 按模型或任务边界生成一个或多个 dispatch 文件
3. 用户通过 launcher 或手工 deeplink 拉起子会话
4. 子会话在允许文件范围内执行并输出汇总

### Scenario: 子会话遇到越界需求

1. 子会话执行某个 dispatch 文件中的任务
2. 发现需要修改未授权文件
3. 子会话停止继续推进并回报阻断，而不是顺手扩改

## Invariants

- 一个 dispatch 文件只能服务一个 change
- 同一模型组不应被拆成多个并行 dispatch 文件
- 子会话开始前必须能在仓库中定位到 dispatch 文件
- dispatch 不得绕过任务边界与文件边界

## Non-goals

- 本规范不定义具体模型路由矩阵
- 本规范不保证 Cursor 会话自动确认执行
- 本规范不替代 longflow 模式
