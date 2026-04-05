# 长任务流会话指令 - export-ready-docs-master

> 本文件用于 PMTRPG 仓库的导出就绪总 longflow。
> 恢复会话时，必须先读取 `openspec/project.md` 与同目录下的 `longflow-state.json`。

## 公共上下文

- **Change ID**：`export-ready-docs-master`
- **执行模式**：`longflow`
- **相关文件**：
  - `openspec/project.md`
  - `openspec/specs/document-export-readiness/spec.md`
  - `openspec/changes/export-ready-docs/longflow-state.json`
  - `openspec/changes/export-ready-docs-batch-2/longflow-state.json`
  - `openspec/changes/export-ready-docs-master/proposal.md`
  - `openspec/changes/export-ready-docs-master/design.md`
  - `openspec/changes/export-ready-docs-master/tasks.md`
  - `docs/acceptance/export-readiness-audit.md`
  - `docs/acceptance/export-stub-page-policy.md`
  - `scripts/audit_export_readiness.py`
  - `scripts/export_sample_docs.py`

## 执行规则

1. 先读 baseline 和 batch-2，再读 master change
2. 每次只推进当前 batch，不跨 batch 顺手做无关目录
3. 每个 batch 必须具备 manifest、acceptance 记录和导出证据
4. 站点回归、审计回归、PDF/CHM 批次导出是每批必做动作
5. 概览页补正文不得新增规则真相，只写最小导览信息

## 当前任务分解

1. 落地 master change 图纸
2. 完成 Batch-3 到 Batch-8 的 A 桶持续清理
3. 完成 Batch-9 的概览页收口
4. 完成 Batch-10 的 B 桶最终收口与整书候选验证
5. 更新 master state 并留下下一阶段建议
