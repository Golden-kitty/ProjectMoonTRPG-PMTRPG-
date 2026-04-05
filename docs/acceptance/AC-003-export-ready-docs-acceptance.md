# AC-003: Export-Ready Docs Acceptance

## Capability Under Review
PMTRPG 文档从站点可用提升到 PDF / CHM 样本可导出的最小能力，包括结构收敛、资源可达性、样本导出和 longflow 恢复状态。

## Preconditions
- `T-003: Export-Ready Docs Longflow` 已明确目标、边界和验收条件
- `docs/PDF章节页码映射.md` 仍可作为章节顺序主来源
- 样本导出所需工具链已明确可用性或缺失情况

## Happy Paths
- [ ] export-ready spec 与 change 文档存在且边界清晰
- [ ] 导出审计已产出阻塞项分桶结果
- [ ] 样本集中关键图片在不依赖 MkDocs hook 的情况下仍可解析
- [ ] 样本集中关键正文页面具有稳定 H1 和章节结构
- [ ] 样本 PDF 导出成功，且抽查内容与站点无关键结构性偏差
- [ ] 样本 CHM 导出链完成目录/项目文件生成；若编译器可用，则编译成功
- [ ] `longflow-state.json` 正确记录当前 phase、task、验证结果和下一步动作

## Edge Cases
- [ ] 站点空壳页没有被误当成 PDF / CHM 正文空白页
- [ ] 无法可靠转换的表格被明确记录限制，而非静默忽略
- [ ] 若 CHM 编译工具不可用，状态应转为有证据的受限通过或待外部验证，而不是伪造通过
- [ ] 导出验证不应因为站点仍能构建就跳过结构抽查

## CounterExamples / Must Not Happen
- [ ] 只因为 `mkdocs build` 通过就宣称 PDF / CHM 就绪
- [ ] 为了让导出脚本跑通而顺手重写无关正文
- [ ] 保留会在 PDF / CHM 中失效的站点专用路径技巧，却不记录风险
- [ ] 把 `originFab/` 或临时导出产物回写成长期正文真相

## Regression Points
- [ ] Site-First 工作流未被破坏，`build_site.py build` 仍可运行
- [ ] `docs/PDF章节页码映射.md` 与现有导航顺序未被另造长期真相替代
- [ ] 样本修复未破坏现有图片资源或章节路径
- [ ] 导出脚本与审计脚本对缺失外部工具的处理是可解释的

## Required Evidence
- export-ready spec / change / task / acceptance 文档 diff
- 导出审计结果
- PDF 样本导出结果与抽查记录
- CHM 样本项目文件、可选的编译日志、以及工具可用性说明
- `longflow-state.json` 的阶段状态与最近验证结果

## Pass Rule
当导出审计已收敛到可解释范围、样本 PDF 导出成功、CHM 样本链路已形成可复查证据、且 `longflow-state.json` 状态与剩余风险一致时，可判通过。

## Fail Rule
若关键图片仍依赖站点 hook、样本页缺少可导出标题结构、重要表格仍未处理、缺少独立导出证据或状态文件未更新，则退回。
