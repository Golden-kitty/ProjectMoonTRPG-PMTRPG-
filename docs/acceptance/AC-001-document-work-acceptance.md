# AC-001: Document Work Acceptance Baseline

## Capability Under Review
PMTRPG 文档清洗、结构重建和治理型改动的最小验收标准。

## Preconditions
- 对应 `Task Brief` 已明确 `Goal`、`InScope`、`OutOfScope` 和 `Provides`
- 待处理文件、脚本或清单项已被列出
- 可访问相关参考源：原始 PDF / CHM、`docs/PDF章节页码映射.md`、审计输出或缩略图索引

## Happy Paths
- [ ] 目标文件完成所述改动，且与 `Task Brief` 一致
- [ ] 相关章节仍可通过 `docs/PDF章节页码映射.md` 或源页定位进行对照
- [ ] 若任务涉及表格清洗，目标文件不再残留未处理的 `<table>`，或已明确记录无法自动转换的原因
- [ ] 若任务涉及清单型批处理，`docs/表格重建清单.md` 已同步状态与说明

## Edge Cases
- [ ] 改动后没有新增 `�`、异常占位字符或仅标题无正文的空壳文件
- [ ] 相对图片路径和文档链接在仓库内仍可解析
- [ ] 同名章节、多候选映射或占位文档没有因本次改动变得更难判断

## CounterExamples / Must Not Happen
- [ ] 只因为脚本执行成功就判定内容通过，而未核对源页或目标行为
- [ ] 顺手修改未列入 `EditableAreas` 的章节、脚本或资源
- [ ] 为了让审计输出变绿而破坏原始语义或删掉必要内容
- [ ] 把 `originFab/` 或 `output/` 中的临时 / 派生产物误当长期真相回写

## Regression Points
- [ ] 标题层级、章节路径和资源引用未被无意破坏
- [ ] 现有导入约束（编码、图片复制、GitHub 渲染目标）未被文档变更误导
- [ ] 审计脚本仍能对既有材料给出可解释的输出

## Required Evidence
- 相关文件 diff
- 必要时的源页对照：PDF 页面缩略图、CHM 导出页面或章节映射引用
- 相关审计输出：`audit_html.txt`、`output_title_only_dupes.txt` 或任务新增的检查结果
- 人工核对结论，说明检查了哪些边界和反例

## Pass Rule
所有关键核对点完成，且证据能说明内容正确、边界未越界、回归点已被检查时，方可通过。

## Fail Rule
任何越界修改、源语义明显漂移、关键证据缺失或回归点未检查，均应退回。
