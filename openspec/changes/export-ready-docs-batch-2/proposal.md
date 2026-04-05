# export-ready-docs-batch-2

## Why

`export-ready-docs` baseline 已经证明：

- 站点质量不能代表 PDF / CHM 质量
- 仓库已经具备导出审计、样本 PDF 导出和 CHM 项目生成能力
- 后续工作不再是“补基线”，而是“按批次收敛剩余高风险页和阻塞桶”

当前仍然存在三类高优先级问题：

- `技能列表.md` 仍保留复杂 HTML 大表
- `奇门.md` 虽不再包含 HTML table，但导出表格结构仍较粗糙
- 当前环境尚未完成真实 CHM 编译验证

## What Changes

- 新建 batch-2 的 longflow change 图纸与状态文件
- 继续收敛 `技能列表.md` 与 `奇门.md`
- 尝试安装 / 验证真实 CHM 编译链
- 新增第一批 A 桶清理任务与证据
- 增强批次导出能力与空壳页导出策略

## OutOfScope

- 不直接完成整书 PDF / CHM 最终成品
- 不重跑 Site-First 基线建设
- 不修改 `originFab/`
- 不顺手批量重写所有剩余正文文件

## Provides

- 一条新的 batch-2 longflow
- 更稳定的关键样本页导出质量
- CHM 编译环境证据
- 第一批 A 桶清理结果与批次导出能力
