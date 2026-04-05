# Export Batch 9 Overview Pages

## Scope

为顶层入口页补最小概览正文，并将已完成页面从 `Need Overview` 中收口。

- manifest：`openspec/changes/export-ready-docs-master/batch9-overview-pages.txt`
- 文件数：`12`
- `PM_TRPG.md`
- `创作指南.md`
- `核心规则.md`
- `核心规则/创建角色.md`
- `核心规则/创建角色/战斗配置.md`
- `核心规则/势力.md`
- `核心规则/可选规则.md`
- `核心规则/心灵之光.md`
- `核心规则/生活日常.md`
- `核心规则/购买项.md`
- `资源目录.md`
- `都市箴言.md`

## Commands Run

```powershell
python scripts/audit_export_readiness.py
python scripts/export_sample_docs.py --format all --compile-chm --batch-name batch9-overview-pages --file-list openspec/changes/export-ready-docs-master/batch9-overview-pages.txt --stub-policy docs/acceptance/export-stub-page-policy.md
```

## Export Results

- PDF 批次导出成功：`output/export_samples/batch9-overview-pages/pdf/batch9-overview-pages.pdf`
- HTML 中间预览成功：`output/export_samples/batch9-overview-pages/pdf/batch9-overview-pages.html`
- CHM 项目文件成功生成：`output/export_samples/batch9-overview-pages/chm/batch9-overview-pages.hhp`
- CHM 目录文件成功生成：`output/export_samples/batch9-overview-pages/chm/batch9-overview-pages.hhc`
- CHM 真编译成功：`output/export_samples/batch9-overview-pages/chm/batch9-overview-pages.chm`
- 批次验证记录成功生成：`output/export_samples/batch9-overview-pages/verification.md`

## Artifact Sizes

- `output/export_samples/batch9-overview-pages/pdf/batch9-overview-pages.pdf`：`13531` bytes
- `output/export_samples/batch9-overview-pages/pdf/batch9-overview-pages.html`：`7690` bytes
- `output/export_samples/batch9-overview-pages/chm/batch9-overview-pages.chm`：`19943` bytes

## Final Audit Snapshot

- 含 HTML table 的文件：`0`
- 无任何标题的文件：`0`
- 有标题但无 H1 的文件：`0`
- 含编码工件的文件：`0`
- 站点空壳页：`42`

## Notes

- 本批次验证记录见：`output/export_samples/batch9-overview-pages/verification.md`
- A 桶与 B 桶已在 master pass 后全部清零；剩余空壳页已转入 `Export Filter` 策略管理。
