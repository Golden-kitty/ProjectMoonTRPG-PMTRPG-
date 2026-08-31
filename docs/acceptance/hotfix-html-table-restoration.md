# hotFix HTML 表格恢复验收记录

## 任务边界

- **TaskType**：紧急内容恢复
- **Goal**：撤销最近一次 HTML 表格转 Markdown 管道表造成的结构损坏，同时保留 hotFix 后续规则修订。
- **OutOfScope**：全库统一 HTML、重写 PDF / Word 导出器、重构图片资源分发、修改 `originFab/`。
- **EditableAreas**：受影响的 `docs/**/*.md` 表格；造成隐式转换的脚本入口；本验收记录。
- **ForbiddenAreas**：原始二进制资料、无关正文、站点主题、正式分发工作流。

## 基线与恢复结果

- 损坏进入历史的合入点：`8a5359f`。
- 表格结构恢复参照：`ce3c991`。
- hotFix 施工前基线：`0534270`。
- 受影响文件中，参照版本共有 `343` 个 HTML `table`（包含嵌套表格）。恢复后逐文件总数仍为 `343`。
- `82/82` 个含目标表格的文件，其行、单元格、`rowspan`、`colspan` 结构签名与参照版本一致。
- 参照版本使用的表格图片引用全部保留，缺失数为 `0`。
- `0ca326d` 引入的规则修改共抽取 `108` 个新增文本片段，恢复后保留 `108/108`。
- 全库仍有 `28` 个 Markdown 管道表分隔行；它们不属于本次被破坏的 HTML 表格集合，未被扩大处理。

## 防复发措施

- `scripts/master_export_batches.py` 不再隐式调用 HTML 到 Markdown 的表格转换。
- `scripts/rebuild_html_tables_to_pipe.py` 默认拒绝原地执行有损转换；只有显式使用 `--allow-lossy` 才会继续。
- `scripts/rebuild_tables_from_checklist.py` 同样要求显式使用 `--allow-lossy`。
- 拒绝路径已验证：命令返回非零，目标文件 SHA-256 保持不变。

## 验证证据

### 站点

- `python scripts/build_site.py build`：通过。
- MkDocs 生成 `212` 个导航项并完成站点构建。

### CHM

- 代表性样本包含：等级、技能列表、检定一览表、奇门。
- HTML Help Compiler 编译完成：`4` 个主题，输出 CHM 为 `34,759` 字节。
- 四个主题 HTML 分别保留 `1`、`1`、`5`、`4` 个表格；后三个样本仍含合并单元格属性。
- **已知限制**：当前样本工程未把技能图标加入 CHM 文件清单，编译报告为 `0 Graphics`。这是导出器资源收集问题，不能视为 CHM 图片分发通过。

### DOCX 兼容性样本

- Pandoc 成功生成 DOCX。
- OOXML 检测到 `11` 个表格、`53` 个 `gridSpan`、`9` 个 `vMerge`，证明基础横向与纵向合并可进入 DOCX。
- **Needs More Evidence**：项目尚未接入正式 Word 自动构建链；当前环境也没有可用的 Word / LibreOffice 渲染器，未完成逐页视觉验收。
- **已知限制**：图片文件 URI 在当前预览链中被百分号编码后未正确解析，样本内绘图对象数为 `0`。

### PDF

- ReportLab 样本成功生成 `14` 页 PDF，正文和代表性规则文本均可提取。
- 已将全部页面渲染为 PNG 并进行视觉检查。
- **Needs More Evidence / 当前不通过版式验收**：现有 PDF 导出器没有应用 HTML 的 `rowspan`、`colspan` 和嵌套表格布局。复杂表格出现过窄列和纵向挤压，不能作为最终分发质量。

## 验收结论

- **Hotfix 源内容恢复：Passed**。
- **站点构建：Passed**。
- **CHM 表格结构：Passed；图片打包：Needs More Evidence**。
- **DOCX 结构兼容性：初步通过；正式构建与视觉验收：Needs More Evidence**。
- **PDF 生成：Passed；复杂表格版式：Failed / 需要后续导出器改造**。

本次提交只恢复表格并阻止相同的隐式有损转换再次发生。全量 HTML 统一和多格式渲染器改造应另立任务，并以 CHM、DOCX、PDF 的独立视觉验收作为完成条件。
