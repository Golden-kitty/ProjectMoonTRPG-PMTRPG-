# Export Batch 3 Core Tables

## Scope

集中收敛 `核心规则` 中的高密度规则表、心灵之光与购买项目录，完成主规则 A 桶收口。

- manifest：`openspec/changes/export-ready-docs-master/batch3-core-tables.txt`
- 文件数：`28`
- `核心规则/心灵之光/压迫.md`
- `核心规则/心灵之光/变格之路.md`
- `核心规则/心灵之光/同调.md`
- `核心规则/心灵之光/异想体.md`
- `核心规则/心灵之光/心灵侵蚀.md`
- `核心规则/心灵之光/情感.md`
- `核心规则/心灵之光/神备和扭曲.md`
- `核心规则/效果/升华与恶化.md`
- `核心规则/购买项/强化.md`
- `核心规则/购买项/强化类/义体与植入物类.md`
- `核心规则/购买项/强化类/纹身类.md`
- `核心规则/购买项/强化类/药物类.md`
- `核心规则/购买项/改造.md`
- `核心规则/购买项/改造类/机体.md`
- `核心规则/购买项/改造类/系统.md`
- `核心规则/购买项/改造类/部件.md`
- `核心规则/购买项/消耗品.md`
- `核心规则/购买项/精神成瘾品.md`
- `核心规则/购买项/装备.md`
- `核心规则/购买项/装备类/武器类与武器属性.md`
- `核心规则/购买项/装备类/衣物类和饰品类.md`
- `核心规则/购买项/装备类/防具类与防具属性.md`
- `核心规则/购买项/课程.md`
- `核心规则/速查图表/战斗速查.md`
- `核心规则/速查图表/技能列表.md`
- `核心规则/速查图表/检定一览表.md`
- `核心规则/速查图表/状态一览.md`
- `核心规则/速查图表/经历与晋升一览表.md`

## Commands Run

```powershell
python scripts/audit_export_readiness.py
python scripts/export_sample_docs.py --format all --compile-chm --batch-name batch3-core-tables --file-list openspec/changes/export-ready-docs-master/batch3-core-tables.txt --stub-policy docs/acceptance/export-stub-page-policy.md
```

## Export Results

- PDF 批次导出成功：`output/export_samples/batch3-core-tables/pdf/batch3-core-tables.pdf`
- HTML 中间预览成功：`output/export_samples/batch3-core-tables/pdf/batch3-core-tables.html`
- CHM 项目文件成功生成：`output/export_samples/batch3-core-tables/chm/batch3-core-tables.hhp`
- CHM 目录文件成功生成：`output/export_samples/batch3-core-tables/chm/batch3-core-tables.hhc`
- CHM 真编译成功：`output/export_samples/batch3-core-tables/chm/batch3-core-tables.chm`
- 批次验证记录成功生成：`output/export_samples/batch3-core-tables/verification.md`

## Artifact Sizes

- `output/export_samples/batch3-core-tables/pdf/batch3-core-tables.pdf`：`49600` bytes
- `output/export_samples/batch3-core-tables/pdf/batch3-core-tables.html`：`77678` bytes
- `output/export_samples/batch3-core-tables/chm/batch3-core-tables.chm`：`79872` bytes

## Final Audit Snapshot

- 含 HTML table 的文件：`0`
- 无任何标题的文件：`0`
- 有标题但无 H1 的文件：`0`
- 含编码工件的文件：`0`
- 站点空壳页：`42`

## Notes

- 本批次验证记录见：`output/export_samples/batch3-core-tables/verification.md`
- A 桶与 B 桶已在 master pass 后全部清零；剩余空壳页已转入 `Export Filter` 策略管理。
