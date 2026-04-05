# document-export-readiness Specification

## Purpose

`document-export-readiness` 定义 PMTRPG Markdown 正文从“站点可渲染”提升到“可稳定导出为 PDF / CHM”的最低契约。

它用于解决一个当前已被证实的问题：

- `MkDocs` 站点能构建成功，并不代表 PDF / CHM 打包质量可接受
- 站点 hook、导航配置和链接容错会掩盖源文件中的结构债务
- 如果没有单独的导出就绪标准，后续打包会在标题、表格、图片路径和编码问题上集中失败

## Requirements

### Requirement: Export-Independent Resource Paths

**Requirement ID:** `REQ-DER-001`

正文中的关键图片引用 MUST 不依赖 `MkDocs` 专用 hook 才能在导出链中解析。

#### Acceptance Criteria

1. WHEN 文档进入 PDF / CHM 样本导出 THEN 关键图片路径 SHALL 在不执行 `scripts/mkdocs_hooks.py` 的情况下仍可解析
2. IF 某类图片路径仍需要站点侧重写 THEN 系统 SHALL 先将其列为阻塞项，而不是直接判定导出通过

### Requirement: Export-Compatible Structure

**Requirement ID:** `REQ-DER-002`

进入导出目录树的正文文件 MUST 具备稳定的标题结构。

#### Acceptance Criteria

1. WHEN 文件作为独立章节进入导出书籍 THEN 文件 SHALL 至少具有一个明确的 H1
2. IF 文件仅作为站点分组占位 THEN 系统 SHALL 明确把它标记为导出过滤对象或补成真实概览页

### Requirement: Table Portability

**Requirement ID:** `REQ-DER-003`

导出样本中使用的正文表格 MUST 优先采用可移植格式，而不是依赖浏览器容错的 HTML table。

#### Acceptance Criteria

1. WHEN 文件被纳入导出样本集 THEN 其中的关键表格 SHALL 转为 Markdown 管道表或已验证兼容的导出格式
2. IF 某个表格暂时无法无损转换 THEN 系统 SHALL 在变更文档中记录原因、影响范围和后续策略

### Requirement: Encoding Hygiene

**Requirement ID:** `REQ-DER-004`

导出链涉及的正文文件 MUST 清理明显的编码工件和异常占位字符。

#### Acceptance Criteria

1. WHEN 文件进入导出样本集 THEN 其中 SHALL 不包含 `\xa0`、`�` 或其他已知会影响导出质量的工件
2. IF 发现新的编码异常模式 THEN 审计脚本 SHALL 能将其记录为回归证据

### Requirement: Explicit Export Audit

**Requirement ID:** `REQ-DER-005`

系统 MUST 提供面向 PDF / CHM 的独立审计，而不是复用站点构建通过作为唯一证据。

#### Acceptance Criteria

1. WHEN change 进入验证阶段 THEN 系统 SHALL 产出导出阻塞项审计结果
2. IF 审计仍存在阻塞项 THEN longflow SHALL 保持未完成状态并写明下一步动作

### Requirement: Sample Export Verification

**Requirement ID:** `REQ-DER-006`

在整书导出前，系统 MUST 先跑通覆盖关键结构的最小样本集。

#### Acceptance Criteria

1. WHEN change 进入样本导出阶段 THEN 系统 SHALL 至少包含复杂表格页、图片页、普通叙述页和资源页四类样本
2. IF 样本导出与站点内容结构明显不一致 THEN 系统 SHALL 退回阻塞项修复，而不是直接宣称整书可导出

## Scenarios

### Scenario: Site passes but export fails

1. 站点构建成功
2. 导出审计发现标题、表格或图片路径问题
3. 样本 PDF / CHM 出现空页、断图或表格错位
4. 会话回到修复阶段，继续 longflow

### Scenario: Resume export-ready longflow

1. 会话执行到部分修复或样本导出阶段后中断
2. 新会话读取 `openspec/project.md`、change 文档、`longflow.md` 和 `longflow-state.json`
3. 新会话根据 `next_action` 继续审计、修复或验证

## Invariants

- `docs/PDF章节页码映射.md` 仍是章节顺序与映射主来源
- `originFab/` 只作为参考源，不作为日常编辑输出目录
- 不得为了通过审计而删改原始语义或把站点导航技巧误当正文内容
- PDF / CHM 验证必须独立于 `MkDocs` hook 和公开站点导航

## Non-goals

- 本规范不定义最终 PDF / CHM 的视觉美学
- 本规范不要求第一次 change 就完成整书导出
- 本规范不替代 Site-First 工作流本身
