# 长任务流会话指令 - export-ready-docs

> 本文件用于 PMTRPG 仓库的导出就绪 longflow。
> 恢复会话时，必须先读取 `openspec/project.md` 与同目录下的 `longflow-state.json`。

## 公共上下文

- **Change ID**：`export-ready-docs`
- **执行模式**：`longflow`
- **相关文件**：
  - `openspec/project.md`
  - `openspec/specs/document-export-readiness/spec.md`
  - `docs/tasks/T-003-export-ready-docs.md`
  - `docs/acceptance/AC-003-export-ready-docs-acceptance.md`
  - `openspec/changes/export-ready-docs/proposal.md`
  - `openspec/changes/export-ready-docs/design.md`
  - `openspec/changes/export-ready-docs/tasks.md`
- **实施目标文件**：
  - `openspec/specs/document-export-readiness/spec.md`
  - `openspec/changes/export-ready-docs/**`
  - `docs/tasks/T-003-export-ready-docs.md`
  - `docs/acceptance/AC-003-export-ready-docs-acceptance.md`
  - `docs/acceptance/export-readiness-audit.md`
  - `docs/acceptance/export-sample-verification.md`
  - `scripts/audit_export_readiness.py`
  - `scripts/export_sample_docs.py`
  - 样本修复文件
    - `docs/核心规则/基本规则/等级.md`
    - `docs/核心规则/速查图表/技能列表.md`
    - `docs/核心规则/战斗/战斗流程.md`
    - `docs/资源目录/装备/武器/奇门.md`
  - `WORKFLOW_GUIDE.md`

## 执行规则

1. 先读 `openspec/project.md`
2. 只处理当前 change，禁止顺手开启第二个 change
3. 样本文件之外的正文修改必须有明确阻塞理由
4. 每次阶段切换、样本导出或回归验证完成后刷新 `longflow-state.json`
5. 若外部导出工具缺失，必须记录证据与限制，不得伪造“已通过”

## 当前任务分解

1. 落地 export-ready spec、任务文档、验收文档和 change 图纸
2. 生成导出阻塞项审计结果
3. 修复样本文件中的标题、表格、图片路径和编码问题
4. 记录站点空壳页的导出策略
5. 运行 PDF / CHM 样本导出并记录证据
6. 回归站点构建并更新验证状态

## 恢复清单

1. 阅读 `openspec/project.md`
2. 阅读当前 change 的 `proposal.md` / `design.md` / `tasks.md`
3. 阅读 `docs/tasks/T-003-export-ready-docs.md`
4. 阅读 `docs/acceptance/AC-003-export-ready-docs-acceptance.md`
5. 阅读 `longflow.md`
6. 阅读 `longflow-state.json`
7. 运行 `git status --short`
8. 按 `next_action` 继续

## 完成后汇总

完成后至少汇总：

- 已生成或更新的 spec / change / task / acceptance 文件
- 导出阻塞项审计结果
- 样本 PDF / CHM 导出结果
- 站点回归构建结果
- 剩余风险和后续批次建议
