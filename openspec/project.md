# Project Overview

> **AI 必读：本文件是 PMTRPG 仓库内 OpenSpec 工作流的权威入口。**
> 在生成 spec、proposal、design、tasks、dispatch 或 longflow 产物之前，必须先阅读本文件。
> 本文件用于补充现有 `README.md`、`docs/project-memory.md`、`docs/project-brief.md` 与 `WORKFLOW_GUIDE.md`，不会替代它们。

## 项目定位

本项目是一个以 Markdown 文档为核心的 PMTRPG 规则仓库。

当前目标不是开发游戏运行时代码，而是稳定维护以下能力：

- `docs/` 正文与索引的持续清洗
- 基于 `docs/PDF章节页码映射.md` 的站点优先构建链
- 面向多会话协作的可追踪文档工作流

## 权威材料顺序

进入任何 OpenSpec 会话前，至少按以下顺序读取最小上下文：

1. `README.md`
2. `docs/project-memory.md`
3. `docs/project-brief.md`
4. 与当前任务直接相关的 `docs/tasks/T-*.md`、`docs/acceptance/AC-*.md`
5. 如涉及工程实施，再补读 `WORKFLOW_GUIDE.md`、`IMPORT_GUIDE.md`

## 核心约束

### A. 材料与真相来源

1. `docs/` 是当前可编辑正文与索引主来源。
2. `originFab/` 中的 PDF / CHM / Word 等材料是参考源，不是日常编辑输出目录。
3. `docs/PDF章节页码映射.md` 是章节顺序与映射核对主来源，不能随意另造一套长期真相。
4. `docs/project-memory.md` 只记录已确认且仍有效的长期信息；聊天结论不能直接替代长期文档。

### B. 编辑边界

1. 默认只修改当前任务声明的 `EditableAreas`，不得顺手修相邻章节、脚本或资源。
2. 任何会改变目录落点、章节映射、表格重建策略、验收方式的未知项，必须先澄清再规划。
3. `originFab/`、构建产物和无关正文默认视为禁止修改区域，除非当前 change 明确放行。

### C. 证据与验收

1. 不得在没有证据时宣称完成；证据可以是 diff、脚本输出、人工核对记录或验收清单。
2. 对文档型 change，应优先提供可复查的路径、命令和抽查结果，而不是只给口头结论。
3. 如果任务依赖人工判断，必须在 change 文档里写清楚核对方法与剩余风险。

### D. 当前工程方向

1. 当前仓库以“在线站点优先”为主工作流，后续再复用导航顺序接入 `CHM + Word`。
2. OpenSpec 在本仓库中服务于文档治理、脚本边界和多会话协作，不应强行套用游戏运行时架构约束。

## OpenSpec 五步（本仓库适配版）

### 第一步：能力 spec

- 长期能力定义写入 `openspec/specs/<capability>/spec.md`
- spec 必须包含：
  - `Purpose`
  - `Requirements`
  - `Scenarios`
  - `Invariants`
  - `Non-goals`
- spec 只定义契约，不写具体实现细节

### 第二步：change 图纸

- 每个活跃 change 放在 `openspec/changes/<change-id>/`
- 最小文件集：
  - `proposal.md`
  - `design.md`
  - `tasks.md`
- change 应聚焦一个清晰目标，例如：
  - 一个工作流基线
  - 一组相关治理文档
  - 一段边界明确的脚本适配

### 第三步：设计基线提交

- 在进入实施前，应先把 change 文档落盘并形成可追溯基线
- 若用户明确要求提交，再执行 Git 提交；否则至少应保证设计文档已成型且可审阅

### 第四步：实施

- 按 `tasks.md` 顺序执行
- 每条任务都应声明：
  - `allowed_files`
  - `forbidden_files`
  - 绑定的 requirement / acceptance
- 对文档型任务，实施可以是：
  - 新增或修改治理文档
  - 新增 launcher / 校验脚本
  - 调整工作流说明与仓库入口文档

### 第五步：归档

- 完成的 change 应移入 `openspec/changes/archive/`
- 未归档的活跃 change 才应作为当前上下文继续引用

## Dispatch 工作流（强制）

### Dispatch 触发条件

以下意图触发 dispatch：

- “分发任务”
- “给我 Group N”
- “把 tasks 拆给子会话”
- 任何明确要求由多个子会话并行或分组执行当前 change 的请求

### Dispatch 核心机制

dispatch 采用“文件落盘 + deeplink 启动”模式：

1. 主会话把子任务写入 `openspec/dispatch/<change-id>--<model-tag>.md`
2. 每个 dispatch 文件对应一个模型组、一个子会话
3. 子会话通过 Cursor deeplink 打开，并读取对应 dispatch 文件执行

### 不变量

- 同一 dispatch 文件中的任务必须能由一个子会话顺序完成
- 同一 change 的 dispatch 与 longflow 不得并行写状态
- 禁止在聊天里只给裸提示词而不落盘 dispatch 文件
- dispatch 文件必须显式列出允许修改文件与禁止修改行为

### Dispatch 启动方式

- 手工 deeplink：由主会话输出 `Start-Process "cursor://..."` 命令
- 批量辅助：`.\openspec\dispatch-launcher.ps1 -ChangeId "<change-id>"`

## Longflow 工作流（强制）

### Longflow 触发条件

以下意图触发 longflow：

- “单会话直接做完整个 change”
- “不要分发，直接连续做完”
- “如果断线就继续当前 change”
- 任何明确要求由一个会话串行完成 spec -> design -> apply -> verify 的请求

### Longflow 核心机制

longflow 采用 `longflow.md + longflow-state.json + launcher` 模式：

1. `longflow.md` 面向人和 LLM，说明上下文、规则、任务分解、恢复清单和汇总格式
2. `longflow-state.json` 面向脚本，记录 phase、task、验证结果、心跳和下一步动作
3. `openspec/longflow-launcher.ps1` 基于状态文件构造恢复 deeplink

### 最小状态字段

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

### 终止状态

- `blocked`
- `awaiting_user`
- `completed`

当状态进入上述任一值时，launcher 必须停止自动重试。

### 恢复顺序

恢复会话必须按以下顺序读取：

1. `openspec/project.md`
2. 当前 change 的 `proposal.md` / `design.md` / `tasks.md`
3. `longflow.md`
4. `longflow-state.json`
5. 当前 Git 工作树状态

### Longflow 启动方式

- 手工 deeplink：由主会话输出恢复命令
- 本地 launcher：
  - `.\openspec\longflow-launcher.ps1 -ChangeId "<change-id>"`
  - `.\openspec\longflow-launcher.ps1 -ChangeId "<change-id>" -AutoRetry`

## 与现有 PMTRPG 治理的关系

- `docs/tasks/` 与 `docs/acceptance/` 仍然是 PMTRPG 当前阶段的重要任务输入和验收来源
- `.cursor/rules/` 中的最小治理、Discovery 与 Verifier 规则继续有效
- OpenSpec 在本仓库中主要承担“跨会话协作协议”和“change 级落盘上下文”角色

## 推荐参考

- `README.md`
- `WORKFLOW_GUIDE.md`
- `IMPORT_GUIDE.md`
- `docs/tasks/T-001-workflow-baseline.md`
- `docs/tasks/T-002-site-first-workflow.md`
- `docs/acceptance/AC-002-site-first-workflow-acceptance.md`
