# Export Sample Verification

## Scope

本次样本验证覆盖以下文件：

- `docs/核心规则/基本规则/等级.md`
- `docs/核心规则/速查图表/技能列表.md`
- `docs/核心规则/战斗/战斗流程.md`
- `docs/资源目录/装备/武器/奇门.md`

## Commands Run

```powershell
python scripts/audit_export_readiness.py
python scripts/export_sample_docs.py --format pdf
python scripts/export_sample_docs.py --format chm --compile-chm
python scripts/build_site.py build
```

## Results

- PDF 样本导出成功：`output/export_samples/pdf/sample-export.pdf`
- PDF 中间预览成功生成：`output/export_samples/pdf/sample-export.html`
- CHM 项目文件成功生成：`output/export_samples/chm/sample-export.hhp`
- CHM 目录文件成功生成：`output/export_samples/chm/sample-export.hhc`
- CHM 编译未执行：当前环境缺少 `hhc`
- Site-First 回归通过：`python scripts/build_site.py build` 成功

## Artifact Sizes

- `output/export_samples/pdf/sample-export.pdf`：`21325` bytes
- `output/export_samples/pdf/sample-export.html`：`35944` bytes
- `output/export_samples/chm/sample-export.hhp`：`490` bytes
- `output/export_samples/chm/sample-export.hhc`：`783` bytes

## Audit Delta

导出审计在本批次修复后变为：

- 含 HTML table 的文件：`80`（从 `82` 降到 `80`）
- HTML table 块数：`335`（从 `340` 降到 `335`）
- 无任何标题的文件：`24`（从 `25` 降到 `24`）
- 有标题但无 H1 的文件：`174`（从 `177` 降到 `174`）
- 含编码工件的文件：`90`（从 `92` 降到 `90`）

样本文件状态：

- `等级.md`：`tables=0`，`no_h1=False`
- `战斗流程.md`：`tables=0`，`no_h1=False`
- `技能列表.md`：`tables=1`，`no_h1=False`
- `奇门.md`：`tables=0`，`no_h1=False`

## Manual Review Notes

- `sample-export.html` 中四个样本页面均已形成独立章节，目录可跳转到对应片段。
- `等级.md` 的升级表已经转为 Markdown 表格，HTML 预览显示为两个稳定表格。
- `战斗流程.md` 已具备 `H1 + H2` 结构，适合进入 PDF / CHM 目录树。
- `奇门.md` 已补 H1，并移除原始 HTML table；当前表格内容已转成可导出的 Markdown 表格，但由于原表存在大量 `colspan`，仍保留重复列信息，属于“可导出但待进一步优化”的状态。
- `技能列表.md` 仍保留 1 个复杂 HTML table，用于保留图标与大表结构；当前样本导出依赖 HTML 兼容渲染，后续若要做整书稳定导出，建议继续拆分或重建该表。
- 生成的 PDF 被识别为 `9` 页样本文件；当前文本提取结果较弱，更适合作为视觉样本而非全文检索产物。

## Open Risks

- 当前环境没有 `hhc`，因此 CHM 只验证到项目文件生成，尚未完成真实编译。
- `技能列表.md` 仍是导出阻塞项的代表样本，说明复杂 HTML table 仍是整书导出的主要风险。
- `奇门.md` 的表格虽然不再含 HTML，但仍需要后续批次进一步去重和美化列结构。

## Batch-2 Update

### Commands Run

```powershell
python scripts/audit_export_readiness.py
python scripts/export_sample_docs.py --format pdf
$env:Path = "d:\Database\Project\workrepo\PMTRPG\ProjectMoonTRPG\tools\htmlhelp-workshop;" + $env:Path
python scripts/export_sample_docs.py --format chm --compile-chm
```

### Results

- 通过解包 `tools/htmlhelp-alt.exe`，在 `tools/htmlhelp-workshop/hhc.exe` 获得可用的真实 CHM 编译器。
- `python scripts/export_sample_docs.py --format chm --compile-chm` 编译成功，生成 `output/export_samples/chm/sample-export.chm`。
- 为兼容 `hhc`，导出脚本已将 CHM 中间 HTML 文件名改为纯 ASCII 的 `sample-01.html` 到 `sample-04.html`。
- `技能列表.md` 已去除复杂 HTML table 和图片图标依赖；`奇门.md` 已改成“元信息 + 战技表”结构。

### Artifact Sizes

- `output/export_samples/chm/sample-export.chm`：`34970` bytes
- `output/export_samples/chm/sample-export.hhp`：`390` bytes
- `output/export_samples/chm/sample-export.hhc`：`699` bytes

### Audit Delta

- 含 HTML table 的文件：`79`
- HTML table 块数：`334`
- 依赖站点 hook 重写图片路径的文件：`1`
- `技能列表.md`：`tables=0`，`hook_image_refs=0`
- `奇门.md`：`tables=0`，`hook_image_refs=0`

### Manual Review Notes

- `hhc` 输出显示 `4 Topics / 3 Local links / 0 Graphics`，并成功创建 `.chm`。
- 先前导致 CHM 编译失败的直接原因是中间 HTML 文件名包含中文路径片段；改为 ASCII 文件名后已通过真实编译。
- 本轮验证证明 Batch-2 已补齐“真实 CHM 编译”这一基线缺口，后续重点转向 A 桶批次清理和批次导出能力。
