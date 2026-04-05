# T-003: Export-Ready Docs Longflow

## TaskType
Implementation

## Goal
将 PMTRPG 仓库中的 `docs/` 从“站点可构建”提升到“可稳定支持 PDF / CHM 样本导出”，并以单会话 `longflow` 模式持续记录审计、修复和验证状态。

## WhyNow
当前 Site-First 工作流已经证明站点链路可运行，但实际验收也证明站点质量不能代表 PDF / CHM 打包质量。若不先补齐导出就绪门槛，后续整书导出只会把结构债务集中暴露。

## InScope
- 新增导出就绪能力 spec 和 export-ready change 文档
- 新增面向导出的任务与验收文档
- 新增导出审计脚本与审计产物
- 修复导出样本集中的图片路径、标题层级、HTML table 和编码工件
- 为站点空壳页定义导出策略
- 新增最小 PDF / CHM 样本导出脚本并记录证据

## OutOfScope
- 本次不直接完成整本书 PDF / CHM 最终打包
- 不统一所有章节的视觉排版样式
- 不修改 `originFab/`、`assets/` 原始素材本体
- 不顺手重写与样本导出无关的大批量正文

## Provides
- 一套可恢复的 export-ready longflow change
- 导出阻塞项清单和审计脚本
- 一组经过修复的 PDF / CHM 样本页面
- 面向 PDF / CHM 的独立验证证据

## EditableAreas
- `openspec/specs/**`
- `openspec/changes/**`
- `docs/tasks/`
- `docs/acceptance/`
- `docs/**/*.md` 中被明确纳入样本和阻塞修复范围的文件
- `scripts/`
- `WORKFLOW_GUIDE.md`

## ForbiddenAreas
- `originFab/`
- `assets/` 原始素材本体
- `output/`
- 未纳入本次样本与阻塞清单的正文批量重写

## Contracts
- `docs/PDF章节页码映射.md` 继续作为章节顺序主来源
- 导出验证不得依赖 `MkDocs` hook 作为唯一成立条件
- 站点分组占位页不得直接被当作 PDF / CHM 正文章节
- 每次阶段切换后都要更新 `longflow-state.json`

## AcceptanceChecks
- [ ] 仓库内存在 export-ready 的 spec、change 文档、任务文档和验收文档
- [ ] 导出审计能产出阻塞项分桶结果
- [ ] 最小样本集中的关键图片路径不再依赖 `MkDocs` hook 才能解析
- [ ] 最小样本集中的关键正文文件具备可导出的标题结构
- [ ] 最小样本集中的关键表格和编码问题已修复或明确记录限制
- [ ] 至少一次 PDF 样本导出成功并完成人工抽查
- [ ] 至少一次 CHM 样本导出链完成项目文件生成，并在工具可用时完成编译验证
- [ ] `longflow-state.json` 已写入最近验证结果和下一步动作

## SuggestedTests
- 运行导出审计脚本，检查阻塞项统计是否可解释
- 运行 PDF 样本导出，抽查复杂表格页、图片页和普通叙述页
- 运行 CHM 样本导出，检查目录、项目文件和资源可达性
- 对比导出样本与站点页面，确认无关键结构性退化

## ReturnFormat
- Changed
- NotChanged
- TestsRun
- Evidence
- OpenRisks
- Questions
- SuggestedDocUpdates
