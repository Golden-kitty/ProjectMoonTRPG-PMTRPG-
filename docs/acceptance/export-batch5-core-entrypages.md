# Export Batch 5 Core Entrypages

## Scope

补齐 `核心规则`、`创建角色`、`势力`、`可选规则` 入口页结构，并为导出准备概览正文。

- manifest：`openspec/changes/export-ready-docs-master/batch5-core-entrypages.txt`
- 文件数：`21`
- `核心规则.md`
- `核心规则/创建角色.md`
- `核心规则/创建角色/出身.md`
- `核心规则/创建角色/创建流程.md`
- `核心规则/创建角色/战斗配置.md`
- `核心规则/创建角色/战斗配置/战技与战技栏.md`
- `核心规则/创建角色/战斗配置/物品与物品栏.md`
- `核心规则/创建角色/战斗配置/特质与特质栏.md`
- `核心规则/创建角色/技能.md`
- `核心规则/创建角色/特质.md`
- `核心规则/创建角色/种族.md`
- `核心规则/创建角色/经历.md`
- `核心规则/创建角色/美德属性.md`
- `核心规则/创建角色/背景.md`
- `核心规则/势力.md`
- `核心规则/势力/空白 - 副本.md`
- `核心规则/可选规则.md`
- `核心规则/可选规则/人人如龙.md`
- `核心规则/可选规则/先攻变体.md`
- `核心规则/可选规则/等级晋升变体.md`
- `核心规则/可选规则/通用效果.md`

## Commands Run

```powershell
python scripts/audit_export_readiness.py
python scripts/export_sample_docs.py --format all --compile-chm --batch-name batch5-core-entrypages --file-list openspec/changes/export-ready-docs-master/batch5-core-entrypages.txt --stub-policy docs/acceptance/export-stub-page-policy.md
```

## Export Results

- PDF 批次导出成功：`output/export_samples/batch5-core-entrypages/pdf/batch5-core-entrypages.pdf`
- HTML 中间预览成功：`output/export_samples/batch5-core-entrypages/pdf/batch5-core-entrypages.html`
- CHM 项目文件成功生成：`output/export_samples/batch5-core-entrypages/chm/batch5-core-entrypages.hhp`
- CHM 目录文件成功生成：`output/export_samples/batch5-core-entrypages/chm/batch5-core-entrypages.hhc`
- CHM 真编译成功：`output/export_samples/batch5-core-entrypages/chm/batch5-core-entrypages.chm`
- 批次验证记录成功生成：`output/export_samples/batch5-core-entrypages/verification.md`

## Artifact Sizes

- `output/export_samples/batch5-core-entrypages/pdf/batch5-core-entrypages.pdf`：`24699` bytes
- `output/export_samples/batch5-core-entrypages/pdf/batch5-core-entrypages.html`：`19758` bytes
- `output/export_samples/batch5-core-entrypages/chm/batch5-core-entrypages.chm`：`31772` bytes

## Final Audit Snapshot

- 含 HTML table 的文件：`0`
- 无任何标题的文件：`0`
- 有标题但无 H1 的文件：`0`
- 含编码工件的文件：`0`
- 站点空壳页：`42`

## Notes

- 本批次验证记录见：`output/export_samples/batch5-core-entrypages/verification.md`
- A 桶与 B 桶已在 master pass 后全部清零；剩余空壳页已转入 `Export Filter` 策略管理。
