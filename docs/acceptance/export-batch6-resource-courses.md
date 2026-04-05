# Export Batch 6 Resource Courses

## Scope

统一 `资源目录/课程` 下课程、基础战技与流派战技的表格和标题结构。

- manifest：`openspec/changes/export-ready-docs-master/batch6-resource-courses.txt`
- 文件数：`20`
- `资源目录/课程/其他课程.md`
- `资源目录/课程/其他课程/烹饪.md`
- `资源目录/课程/古武术.md`
- `资源目录/课程/基础战技.md`
- `资源目录/课程/基础战技/收尾人操典.md`
- `资源目录/课程/基础战技/暗巷格斗术.md`
- `资源目录/课程/基础战技/标准战术.md`
- `资源目录/课程/基础战技/标准格斗术.md`
- `资源目录/课程/基础战技/街头搏击术.md`
- `资源目录/课程/基础战技/通用镇暴术.md`
- `资源目录/课程/流派战技.md`
- `资源目录/课程/流派战技/丧家犬.md`
- `资源目录/课程/流派战技/八相枪.md`
- `资源目录/课程/流派战技/古武术/咏春.md`
- `资源目录/课程/流派战技/屠夫.md`
- `资源目录/课程/流派战技/暴徒.md`
- `资源目录/课程/流派战技/臼齿事务所.md`
- `资源目录/课程/流派战技/街灯事务所.md`
- `资源目录/课程/流派战技/锈链格斗技.md`
- `资源目录/课程/能力课程.md`

## Commands Run

```powershell
python scripts/audit_export_readiness.py
python scripts/export_sample_docs.py --format all --compile-chm --batch-name batch6-resource-courses --file-list openspec/changes/export-ready-docs-master/batch6-resource-courses.txt --stub-policy docs/acceptance/export-stub-page-policy.md
```

## Export Results

- PDF 批次导出成功：`output/export_samples/batch6-resource-courses/pdf/batch6-resource-courses.pdf`
- HTML 中间预览成功：`output/export_samples/batch6-resource-courses/pdf/batch6-resource-courses.html`
- CHM 项目文件成功生成：`output/export_samples/batch6-resource-courses/chm/batch6-resource-courses.hhp`
- CHM 目录文件成功生成：`output/export_samples/batch6-resource-courses/chm/batch6-resource-courses.hhc`
- CHM 真编译成功：`output/export_samples/batch6-resource-courses/chm/batch6-resource-courses.chm`
- 批次验证记录成功生成：`output/export_samples/batch6-resource-courses/verification.md`

## Artifact Sizes

- `output/export_samples/batch6-resource-courses/pdf/batch6-resource-courses.pdf`：`28937` bytes
- `output/export_samples/batch6-resource-courses/pdf/batch6-resource-courses.html`：`114876` bytes
- `output/export_samples/batch6-resource-courses/chm/batch6-resource-courses.chm`：`59297` bytes

## Final Audit Snapshot

- 含 HTML table 的文件：`0`
- 无任何标题的文件：`0`
- 有标题但无 H1 的文件：`0`
- 含编码工件的文件：`0`
- 站点空壳页：`42`

## Notes

- 本批次验证记录见：`output/export_samples/batch6-resource-courses/verification.md`
- A 桶与 B 桶已在 master pass 后全部清零；剩余空壳页已转入 `Export Filter` 策略管理。
