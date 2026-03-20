# T-001: Workflow Baseline And Material Mapping

## TaskType
Implementation

## Goal
为 PMTRPG 仓库建立最小治理文档与材料映射，使后续 Agent 施工能够基于稳定上下文工作。

## WhyNow
当前仓库已经有导入说明、清单、映射和审计脚本，但缺少统一的任务边界、验收口径和跨会话记忆。

## InScope
- 新增 `docs/project-brief.md` 和 `docs/project-memory.md`
- 新增一份当前改动的正式 `Task Brief`
- 新增一份可复用的文档施工 `Acceptance` 基线
- 新增 `.cursor/rules/` 最小规则文件
- 将现有入口文档、导入说明、清单、映射、审计输出和关键脚本映射到新工作流角色

## OutOfScope
- 不引入 MkDocs / Word / CHM 构建配置
- 不修改 `originFab/` 源材料
- 不重写现有导入 / 审计脚本逻辑
- 不对大批量文档正文做内容修订

## Provides
- 当前阶段可复用的项目简述、项目记忆和文档施工验收基线
- 一组可在 Cursor 中启用的最小规则
- 一份明确说明现有材料在工作流中各司何职的长期文档

## EditableAreas
- `README.md`
- `docs/project-brief.md`
- `docs/project-memory.md`
- `docs/tasks/`
- `docs/acceptance/`
- `.cursor/rules/`

## ForbiddenAreas
- `originFab/`
- `assets/`
- `tools/`
- `scripts/`
- `output/`

## Contracts
- 新增文档中的路径引用必须对应仓库现有材料
- 新增治理文件不得改变现有导入 / 清洗脚本的运行行为
- 映射必须区分长期记忆、任务输入、验收证据和执行器四类角色，避免材料职责混淆

## AcceptanceChecks
- [ ] `docs/project-brief.md` 概括项目目标、限制和现有材料映射
- [ ] `docs/project-memory.md` 只记录当前阶段仍有效的已确认信息
- [ ] 至少一份 `Task Brief` 和一份 `Acceptance` 能直接用于当前文档施工任务
- [ ] `.cursor/rules/` 中存在最小治理、`Discovery` 和 `Verifier` 规则
- [ ] 新增文档不要求修改现有脚本或原始素材即可生效

## SuggestedTests
- 人工检查新文档中的路径是否都存在
- 人工确认工作流角色划分与当前仓库材料一致
- 后续任务命中触发条件时，优先复用这套 `Task Brief / Acceptance` 结构

## ReturnFormat
- Changed
- NotChanged
- TestsRun
- Evidence
- OpenRisks
- Questions
- SuggestedDocUpdates
