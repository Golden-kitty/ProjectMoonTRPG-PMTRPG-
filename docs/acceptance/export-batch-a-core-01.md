# Export Batch A Core 01

## Scope

本批次处理 `核心规则` 下的 11 个 A 桶阻塞文件：

- `核心规则/创建角色/战斗配置/战技与战技栏.md`
- `核心规则/创建角色/战斗配置/物品与物品栏.md`
- `核心规则/创建角色/战斗配置/特质与特质栏.md`
- `核心规则/创建角色/技能.md`
- `核心规则/可选规则/等级晋升变体.md`
- `核心规则/基本规则/晋升.md`
- `核心规则/效果/如何使用.md`
- `核心规则/效果/强度表.md`
- `核心规则/效果/效果表.md`
- `核心规则/生活日常/休整.md`
- `核心规则/生活日常/食物与营养.md`

## Commands Run

```powershell
python scripts/audit_export_readiness.py
$env:Path = "d:\Database\Project\workrepo\PMTRPG\ProjectMoonTRPG\tools\htmlhelp-workshop;" + $env:Path
python scripts/export_sample_docs.py --format all --compile-chm --batch-name batch-a-core-01 --file-list "openspec/changes/export-ready-docs-batch-2/batch-a-core-01.txt"
```

## Audit Delta

批次开始前，基于上一轮样本收敛后的审计结果：

- 含 HTML table 的文件：`79`
- HTML table 块数：`334`
- 无任何标题的文件：`24`
- 依赖站点 hook 重写图片路径的文件：`1`

本批次完成后：

- 含 HTML table 的文件：`72`
- HTML table 块数：`324`
- 无任何标题的文件：`16`
- 依赖站点 hook 重写图片路径的文件：`0`
- A 桶文件数：`84`

本批次 11 个目标文件已不再出现在 `docs/acceptance/export-readiness-audit.md` 的 A 桶列表中。

## Export Results

- PDF 批次导出成功：`output/export_samples/batch-a-core-01/pdf/batch-a-core-01.pdf`
- HTML 中间预览成功：`output/export_samples/batch-a-core-01/pdf/batch-a-core-01.html`
- CHM 项目文件成功生成：`output/export_samples/batch-a-core-01/chm/batch-a-core-01.hhp`
- CHM 目录文件成功生成：`output/export_samples/batch-a-core-01/chm/batch-a-core-01.hhc`
- CHM 真编译成功：`output/export_samples/batch-a-core-01/chm/batch-a-core-01.chm`
- 批次验证记录成功生成：`output/export_samples/batch-a-core-01/verification.md`

## Artifact Sizes

- `output/export_samples/batch-a-core-01/pdf/batch-a-core-01.pdf`：`20888` bytes
- `output/export_samples/batch-a-core-01/pdf/batch-a-core-01.html`：`24656` bytes
- `output/export_samples/batch-a-core-01/chm/batch-a-core-01.chm`：`34005` bytes

## Manual Review Notes

- 本批次的主要修复模式是补 H1、将简单 HTML 表替换为 Markdown 表，以及把图片图例改写为文本图例。
- `技能.md` 已不再依赖图标图片引用来表达技能标记含义，降低了导出链对站点资源路径的依赖。
- `休整.md` 的模板区块已经从 HTML 表占位改为键值表，更适合作为后续规范模板。
- `特质与特质栏.md` 和 `物品与物品栏.md` 的结构已经简化为直接可读的栏位表，不再依赖站点容错渲染。
- CHM 编译结果显示 `11 Topics / 6 Local links / 0 Graphics`，说明本批次文件可被真实 CHM 编译器接受。

## Remaining Risks

- `核心规则` 中仍剩余大量复杂 HTML 表页面，尤其是 `心灵之光`、`购买项`、`速查图表` 等目录下的高密度结构页。
- 本批次主要收敛了“简单表格 + 无 H1”类型，尚未触碰嵌套表、复杂 rowspan / colspan、术语图例混排等更高难度页面。
- 顶层与分组页的空壳策略已经独立成文，但其中标记为 `Need Overview` 的页面仍需后续补最小正文。
