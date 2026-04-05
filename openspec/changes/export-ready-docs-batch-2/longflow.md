# 长任务流会话指令 - export-ready-docs-batch-2

> 本文件用于 PMTRPG 仓库的导出就绪第二批 longflow。
> 恢复会话时，必须先读取 `openspec/project.md` 与同目录下的 `longflow-state.json`。

## 公共上下文

- **Change ID**：`export-ready-docs-batch-2`
- **执行模式**：`longflow`
- **相关文件**：
  - `openspec/project.md`
  - `openspec/specs/document-export-readiness/spec.md`
  - `openspec/changes/export-ready-docs/proposal.md`
  - `openspec/changes/export-ready-docs/design.md`
  - `openspec/changes/export-ready-docs/longflow-state.json`
  - `docs/acceptance/export-readiness-audit.md`
  - `docs/acceptance/export-sample-verification.md`
  - `openspec/changes/export-ready-docs-batch-2/proposal.md`
  - `openspec/changes/export-ready-docs-batch-2/design.md`
  - `openspec/changes/export-ready-docs-batch-2/tasks.md`

## 执行规则

1. 先读 baseline change，再读 batch-2 change
2. 只处理当前 batch-2 任务，禁止顺手开启第三个 change
3. `技能列表.md` 与 `奇门.md` 优先级高于 A 桶批处理
4. 若 `hhc` 缺失或安装失败，必须记录真实证据
5. 每次阶段切换、编译验证或批次修复完成后刷新 `longflow-state.json`

## 当前任务分解

1. 落地 batch-2 change 图纸
2. 进一步收敛 `技能列表.md` 与 `奇门.md`
3. 安装并验证真实 CHM 编译链
4. 清理第一批 `核心规则` A 桶文件
5. 建立空壳页导出策略
6. 扩展批次导出脚本
7. 重跑审计、导出与站点回归，更新状态

## 恢复清单

1. 阅读 `openspec/project.md`
2. 阅读 baseline change 的 `proposal.md` / `design.md` / `tasks.md` / `longflow-state.json`
3. 阅读当前 batch-2 change 的 `proposal.md` / `design.md` / `tasks.md`
4. 阅读 `docs/acceptance/export-readiness-audit.md`
5. 阅读 `docs/acceptance/export-sample-verification.md`
6. 阅读 `longflow.md`
7. 阅读 `longflow-state.json`
8. 运行 `git status --short`
9. 按 `next_action` 继续

## 完成后汇总

完成后至少汇总：

- batch-2 已新增或更新的文件
- `技能列表.md` 与 `奇门.md` 的导出改进点
- CHM 真编译或环境阻塞结论
- A 桶第一批清理结果
- 批次导出能力和空壳页策略
- 剩余风险与下一批建议
