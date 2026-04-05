# Export Batch 4 Guide Structures

## Scope

清理 `创作指南` 的设计说明页、平衡页与武器/防具/强化相关结构页。

- manifest：`openspec/changes/export-ready-docs-master/batch4-guide-structures.txt`
- 文件数：`19`
- `创作指南.md`
- `创作指南/具现化特性设计.md`
- `创作指南/属性平衡.md`
- `创作指南/强化类设计.md`
- `创作指南/战技平衡.md`
- `创作指南/武器设计.md`
- `创作指南/武器设计/临时武器与徒手.md`
- `创作指南/武器设计/奇门.md`
- `创作指南/武器设计/巨兵.md`
- `创作指南/武器设计/弓弩.md`
- `创作指南/武器设计/热武器.md`
- `创作指南/武器设计/盾牌.md`
- `创作指南/武器设计/短兵.md`
- `创作指南/武器设计/短柄.md`
- `创作指南/武器设计/软兵.md`
- `创作指南/武器设计/长兵.md`
- `创作指南/武器设计/长柄.md`
- `创作指南/资源设计表格.md`
- `创作指南/防具设计.md`

## Commands Run

```powershell
python scripts/audit_export_readiness.py
python scripts/export_sample_docs.py --format all --compile-chm --batch-name batch4-guide-structures --file-list openspec/changes/export-ready-docs-master/batch4-guide-structures.txt --stub-policy docs/acceptance/export-stub-page-policy.md
```

## Export Results

- PDF 批次导出成功：`output/export_samples/batch4-guide-structures/pdf/batch4-guide-structures.pdf`
- HTML 中间预览成功：`output/export_samples/batch4-guide-structures/pdf/batch4-guide-structures.html`
- CHM 项目文件成功生成：`output/export_samples/batch4-guide-structures/chm/batch4-guide-structures.hhp`
- CHM 目录文件成功生成：`output/export_samples/batch4-guide-structures/chm/batch4-guide-structures.hhc`
- CHM 真编译成功：`output/export_samples/batch4-guide-structures/chm/batch4-guide-structures.chm`
- 批次验证记录成功生成：`output/export_samples/batch4-guide-structures/verification.md`

## Artifact Sizes

- `output/export_samples/batch4-guide-structures/pdf/batch4-guide-structures.pdf`：`23667` bytes
- `output/export_samples/batch4-guide-structures/pdf/batch4-guide-structures.html`：`39841` bytes
- `output/export_samples/batch4-guide-structures/chm/batch4-guide-structures.chm`：`35615` bytes

## Final Audit Snapshot

- 含 HTML table 的文件：`0`
- 无任何标题的文件：`0`
- 有标题但无 H1 的文件：`0`
- 含编码工件的文件：`0`
- 站点空壳页：`42`

## Notes

- 本批次验证记录见：`output/export_samples/batch4-guide-structures/verification.md`
- A 桶与 B 桶已在 master pass 后全部清零；剩余空壳页已转入 `Export Filter` 策略管理。
