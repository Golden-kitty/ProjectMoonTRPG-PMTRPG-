# Export Batch 7 Resource Items

## Scope

清理 `资源目录/消耗品` 与 `资源目录/装备` 的条目页，统一字段与导出结构。

- manifest：`openspec/changes/export-ready-docs-master/batch7-resource-items.txt`
- 文件数：`34`
- `资源目录/消耗品/医疗品.md`
- `资源目录/消耗品/医疗品/传闻.md`
- `资源目录/消耗品/工具.md`
- `资源目录/消耗品/工具/传闻.md`
- `资源目录/消耗品/工具/怪谈.md`
- `资源目录/消耗品/弹药.md`
- `资源目录/消耗品/弹药/其他.md`
- `资源目录/消耗品/弹药/大口径.md`
- `资源目录/消耗品/弹药/小口径.md`
- `资源目录/消耗品/成瘾品.md`
- `资源目录/消耗品/成瘾品/生理成瘾品.md`
- `资源目录/消耗品/成瘾品/精神成瘾品.md`
- `资源目录/消耗品/燃料.md`
- `资源目录/消耗品/燃料/化学能.md`
- `资源目录/消耗品/燃料/电子能.md`
- `资源目录/消耗品/食物.md`
- `资源目录/消耗品/食物/乳制品.md`
- `资源目录/消耗品/食物/包装食物.md`
- `资源目录/消耗品/食物/碳酸饮料.md`
- `资源目录/消耗品/食物/酒精饮料.md`
- `资源目录/装备/武器/奇门.md`
- `资源目录/装备/武器/巨兵.md`
- `资源目录/装备/武器/弓弩.md`
- `资源目录/装备/武器/火器.md`
- `资源目录/装备/武器/盾牌.md`
- `资源目录/装备/武器/短兵.md`
- `资源目录/装备/武器/短柄.md`
- `资源目录/装备/武器/软兵.md`
- `资源目录/装备/武器/长兵.md`
- `资源目录/装备/武器/长柄.md`
- `资源目录/装备/衣物.md`
- `资源目录/装备/衣物/外套.md`
- `资源目录/装备/防具.md`
- `资源目录/装备/饰品.md`

## Commands Run

```powershell
python scripts/audit_export_readiness.py
python scripts/export_sample_docs.py --format all --compile-chm --batch-name batch7-resource-items --file-list openspec/changes/export-ready-docs-master/batch7-resource-items.txt --stub-policy docs/acceptance/export-stub-page-policy.md
```

## Export Results

- PDF 批次导出成功：`output/export_samples/batch7-resource-items/pdf/batch7-resource-items.pdf`
- HTML 中间预览成功：`output/export_samples/batch7-resource-items/pdf/batch7-resource-items.html`
- CHM 项目文件成功生成：`output/export_samples/batch7-resource-items/chm/batch7-resource-items.hhp`
- CHM 目录文件成功生成：`output/export_samples/batch7-resource-items/chm/batch7-resource-items.hhc`
- CHM 真编译成功：`output/export_samples/batch7-resource-items/chm/batch7-resource-items.chm`
- 批次验证记录成功生成：`output/export_samples/batch7-resource-items/verification.md`

## Artifact Sizes

- `output/export_samples/batch7-resource-items/pdf/batch7-resource-items.pdf`：`18724` bytes
- `output/export_samples/batch7-resource-items/pdf/batch7-resource-items.html`：`106594` bytes
- `output/export_samples/batch7-resource-items/chm/batch7-resource-items.chm`：`51771` bytes

## Final Audit Snapshot

- 含 HTML table 的文件：`0`
- 无任何标题的文件：`0`
- 有标题但无 H1 的文件：`0`
- 含编码工件的文件：`0`
- 站点空壳页：`42`

## Notes

- 本批次验证记录见：`output/export_samples/batch7-resource-items/verification.md`
- A 桶与 B 桶已在 master pass 后全部清零；剩余空壳页已转入 `Export Filter` 策略管理。
