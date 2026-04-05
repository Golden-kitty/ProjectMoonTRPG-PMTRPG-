# Export Batch 10 Final Bucket

## Scope

清理剩余 B 桶文件，完成整书候选前的标题、编码与结构噪音收口。

- manifest：`openspec/changes/export-ready-docs-master/batch10-final-bucket.txt`
- 文件数：`32`
- `核心规则/基本规则.md`
- `核心规则/基本规则/晋升.md`
- `核心规则/基本规则/检定.md`
- `核心规则/基本规则/称呼.md`
- `核心规则/基本规则/稀有度.md`
- `核心规则/基本规则/自动成败和取整计算.md`
- `核心规则/基本规则/评级.md`
- `核心规则/战斗.md`
- `核心规则/战斗/伤害类型.md`
- `核心规则/战斗/伤害计算.md`
- `核心规则/战斗/战后.md`
- `核心规则/战斗/战技.md`
- `核心规则/战斗/拼点.md`
- `核心规则/战斗/行动类动作.md`
- `核心规则/战斗/重创与疯狂.md`
- `核心规则/战斗/防御类动作.md`
- `核心规则/战斗/首发类动作.md`
- `核心规则/效果/效果表.md`
- `核心规则/速查图表.md`
- `玩家手册.md`
- `资源目录/工坊.md`
- `资源目录/能力列表.md`
- `都市箴言/将资源用在刀刃上.md`
- `都市箴言/平衡参考.md`
- `都市箴言/平衡参考/属性_技能参考.md`
- `都市箴言/术语标准化的重要性.md`
- `都市箴言/森语系列说明.md`
- `都市箴言/森语系列说明/战斗说明.md`
- `都市箴言/森语系列说明/车卡说明.md`
- `都市箴言/森语系列说明/非战斗说明.md`
- `都市箴言/设计战技平衡.md`
- `都市箴言/避免成为‘空想家’.md`

## Commands Run

```powershell
python scripts/audit_export_readiness.py
python scripts/export_sample_docs.py --format all --compile-chm --batch-name batch10-final-bucket --file-list openspec/changes/export-ready-docs-master/batch10-final-bucket.txt --stub-policy docs/acceptance/export-stub-page-policy.md
```

## Export Results

- PDF 批次导出成功：`output/export_samples/batch10-final-bucket/pdf/batch10-final-bucket.pdf`
- HTML 中间预览成功：`output/export_samples/batch10-final-bucket/pdf/batch10-final-bucket.html`
- CHM 项目文件成功生成：`output/export_samples/batch10-final-bucket/chm/batch10-final-bucket.hhp`
- CHM 目录文件成功生成：`output/export_samples/batch10-final-bucket/chm/batch10-final-bucket.hhc`
- CHM 真编译成功：`output/export_samples/batch10-final-bucket/chm/batch10-final-bucket.chm`
- 批次验证记录成功生成：`output/export_samples/batch10-final-bucket/verification.md`

## Artifact Sizes

- `output/export_samples/batch10-final-bucket/pdf/batch10-final-bucket.pdf`：`51785` bytes
- `output/export_samples/batch10-final-bucket/pdf/batch10-final-bucket.html`：`52549` bytes
- `output/export_samples/batch10-final-bucket/chm/batch10-final-bucket.chm`：`62706` bytes

## Final Audit Snapshot

- 含 HTML table 的文件：`0`
- 无任何标题的文件：`0`
- 有标题但无 H1 的文件：`0`
- 含编码工件的文件：`0`
- 站点空壳页：`42`

## Notes

- 本批次验证记录见：`output/export_samples/batch10-final-bucket/verification.md`
- A 桶与 B 桶已在 master pass 后全部清零；剩余空壳页已转入 `Export Filter` 策略管理。
