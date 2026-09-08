# Export Readiness Audit

## Summary

- 扫描文件数：`203`
- 含 HTML table 的文件：`92`
- HTML table 块数：`369`
- canonical HTML table 块数：`369`
- 非 canonical HTML table 块数：`0`
- 无任何标题的文件：`0`
- 有标题但无 H1 的文件：`0`
- 站点空壳页：`42`
- 含编码工件的文件：`0`
- 由分发适配器解析的相对图片引用：`47`
- 缺失图片引用：`0`

## Bucket Policy

- `A-阻塞导出`：非 canonical HTML table、缺失图片资源或无标题正文页。
- `B-高风险退化`：无 H1、编码工件、其他会显著影响导出结构但不必然阻塞的项。
- `C-导航空壳`：主要用于站点分组、在 PDF / CHM 中会退化为空白章节的页面。
- canonical HTML table 是当前统一源表示，由站点、CHM、DOCX、PDF 适配器消费，不再因为使用 HTML 而自动进入阻塞桶。
- 指向仓库 `assets/` 且文件存在的相对图片由分发适配器解析和复制，不再视为站点 hook 专属依赖。
- 纯站点分组页默认不进入导出书籍正文；若需要进入导出，则必须补最小概览正文。

## Sample Docs

- `核心规则/基本规则/等级.md`: tables=1, canonical_tables=1, noncanonical_tables=0, no_heading=False, no_h1=False, adapter_resolved_image_refs=0, missing_image_refs=0, nbspace=0
- `核心规则/战斗/战斗流程.md`: tables=0, canonical_tables=0, noncanonical_tables=0, no_heading=False, no_h1=False, adapter_resolved_image_refs=0, missing_image_refs=0, nbspace=0
- `核心规则/速查图表/技能列表.md`: tables=1, canonical_tables=1, noncanonical_tables=0, no_heading=False, no_h1=False, adapter_resolved_image_refs=42, missing_image_refs=0, nbspace=0
- `资源目录/装备/武器/奇门.md`: tables=4, canonical_tables=4, noncanonical_tables=0, no_heading=False, no_h1=False, adapter_resolved_image_refs=0, missing_image_refs=0, nbspace=0

## Global HTML Tag Distribution

| Tag | Count |
| --- | ---: |
| `td` | 16020 |
| `b` | 6353 |
| `tr` | 4966 |
| `table` | 738 |
| `strong` | 338 |
| `th` | 180 |
| `thead` | 52 |
| `tbody` | 52 |

## A-阻塞导出

- 文件数：`0`

## B-高风险退化

- 文件数：`0`

## C-导航空壳

- 文件数：`42`
- `创作指南/武器设计.md`
- `创作指南/防具设计.md`
- `核心规则/创建角色/经历.md`
- `核心规则/势力/空白 - 副本.md`
- `核心规则/可选规则/通用效果.md`
- `核心规则/基本规则/称呼.md`
- `核心规则/基本规则.md`
- `核心规则/战斗.md`
- `核心规则/购买项/改造类/系统.md`
- `核心规则/购买项/精神成瘾品.md`
- `核心规则/速查图表.md`
- `玩家手册.md`
- `资源目录/工坊/任意.md`
- `资源目录/工坊/后巷.md`
- `资源目录/工坊/巢内.md`
- `资源目录/工坊/郊区.md`
- `资源目录/工坊/限定.md`
- `资源目录/工坊.md`
- `资源目录/强化/义体.md`
- `资源目录/强化/植入物.md`
- `资源目录/强化/纹身/传说.md`
- `资源目录/强化/纹身.md`
- `资源目录/强化/药物.md`
- `资源目录/改造/部件/巨型.md`
- `资源目录/改造/部件/系统.md`
- `资源目录/消耗品/医疗品.md`
- `资源目录/消耗品/工具.md`
- `资源目录/消耗品/弹药/大口径.md`
- `资源目录/消耗品/弹药.md`
- `资源目录/消耗品/成瘾品/精神成瘾品.md`
- 其余 `12` 个文件已省略，后续按批次处理。

## Export Stub Strategy

- 对仅作为站点目录占位的概览页，导出阶段应过滤，不生成 PDF / CHM 正文章节。
- 对需要在书籍中保留的概览页，应在后续批次补最小正文，而不是继续保留单行标题。
- 样本集中的文件必须具备真实章节内容，不允许以占位页替代。
