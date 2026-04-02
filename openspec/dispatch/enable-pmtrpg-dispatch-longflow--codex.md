# 会话指令 - enable-pmtrpg-dispatch-longflow / GPT-5 Codex

> 本文件由主会话自动生成。子会话收到后请切换到 Agent 模式，严格按序执行以下所有子任务。

## 公共上下文

- **Change ID**：`enable-pmtrpg-dispatch-longflow`
- **推荐模型**：`GPT-5 Codex`
- **项目规范**：`openspec/project.md`
- **相关 Design**：`openspec/changes/enable-pmtrpg-dispatch-longflow/design.md`
- **全局禁止修改**：`originFab/**`, `assets/**`, `output/**`

## 执行规则

1. 先阅读 `openspec/project.md`
2. 严格限制在允许修改文件范围内
3. 超范围即停止并报告，不要顺手扩改
4. 完成后按末尾格式汇总

---

## 子任务 1/2 - Tooling

- **目标**：检查 `dispatch-launcher.ps1` 与 `longflow-launcher.ps1` 文本和参数设计是否自洽
- **允许修改文件**：`openspec/dispatch-launcher.ps1`, `openspec/longflow-launcher.ps1`
- **完成标准**：
  - 参数说明与实际逻辑一致
  - 默认路径指向当前仓库 `openspec/`

---

## 子任务 2/2 - Docs

- **目标**：检查 OpenSpec 说明文档与仓库入口文档的链接关系
- **允许修改文件**：`docs/engineering/OPENSPEC_WORKFLOW.md`, `README.md`, `WORKFLOW_GUIDE.md`
- **完成标准**：
  - 能从仓库入口定位到 OpenSpec 工作流
  - 不引入与现有 PMTRPG 治理相冲突的表述

---

## 完成后汇总

- **已完成 Task ID**：`Tooling`, `Docs`
- **受影响文件**：路径列表
- **验证结果**：命令与结果
- **风险或超范围问题**：如无则填 `无`
