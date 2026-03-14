# Project Brief

## One Sentence Summary
将 `originFab/` 中的 PMTRPG 原始 PDF / CHM 内容整理为可版本控制、可审计、可持续清洗和后续构建的 Markdown 文档仓库。

## Intended Users
- 内容维护者：编辑、修订和补完规则书内容
- 管理员 / 工程维护者：执行导入、清洗、批量修复和审计脚本
- Agent / LLM 协作者：在明确边界内执行局部任务并回写结果

## Desired Outcomes
- `docs/**/*.md` 保持可读、可追踪、可逐步修订
- 章节、页码、图片和路径能够稳定对照原始 PDF / CHM
- 批量清洗和人工重建任务具备明确输入、边界、验收和证据
- 先落地站点优先工作流与 GitHub Pages 部署，再复用同一顺序来源接入 CHM / Word 构建链

## Non-Goals
- 当前阶段不直接引入 CHM 或 Word 自动构建链
- 当前阶段不一次性重写所有章节结构或所有脚本
- 当前阶段不把 `originFab/` 中的二进制源文件作为日常编辑对象

## Constraints
- 内容应尽量对齐 `originFab/Project Moon Trpg Rule Book V1.8.4.pdf` 与 WinCHM 导出结果
- 仓库当前以 GitHub Markdown 渲染为准
- 历史导入内容包含复杂表格、编码和路径问题，仍需人工复核
- 站点工作流需要兼容现有根目录 `assets/` 资源布局，并为后续 CHM / Word 复用导航顺序

## Current Milestone
- 建立站点优先工作流基线，并将现有文档清洗阶段推进到可部署、可复用的在线站点阶段

## Unknowns Needing Research
- 何时将站点导航顺序进一步固化为 CHM / `reference.docx` 的统一书籍顺序
- 哪些章节映射、术语和结构约束值得提升为长期决策
- 哪些审计项需要固化为更正式的自动检查

## Existing Material Mapping
- `README.md`：仓库入口，指向正文、原始 PDF 与索引材料
- `docs/PM_TRPG.md`：规则书正文总入口
- `IMPORT_GUIDE.md`：WinCHM 导出到 Markdown 的管理员操作约束；应视为导入契约和运行说明
- `docs/PDF图片索引.md`：按页人工查阅原始 PDF 的视觉参考
- `docs/PDF章节页码映射.md`：PDF 目录章节、页码与 Markdown 文件之间的核对索引；适合作为验证输入
- `docs/表格重建清单.md`：当前最明确的批处理施工队列；适合作为任务输入和进度记录
- `audit_html.txt`、`audit_no_heading.txt`、`audit_weird.txt`、`audit_word.txt`：结构与残留问题的审计输出；适合作为验收与回归证据
- `output_title_only_dupes.txt`：标题空壳 / 同名候选审计输出；适合作为回归证据
- `scripts/import_winchm_export.py`：WinCHM HTML Tree 到 Markdown 的导入实现
- `scripts/rebuild_tables_from_checklist.py`、`scripts/rebuild_html_tables_to_pipe.py`：表格重建执行器
- `scripts/find_title_only_duplicates.py`：标题空壳 / 重名文档审计器
- `scripts/build_pdf_chapter_map.py`、`scripts/render_pdf_pages_small.py`：章节映射与 PDF 参考图生成器
- `scripts/generate_mkdocs_config.py`：基于 `docs/PDF章节页码映射.md` 生成 `MkDocs` 配置
- `scripts/build_site.py`、`scripts/mkdocs_hooks.py`：站点构建包装器与资源复制 hook
- `.github/workflows/deploy-site.yml`：GitHub Pages 部署工作流
- `assets/chm/`：导入后的图片资源目标
- `assets/pdf_pages_small/`：PDF 页面对照缩略图目录
- `originFab/Project Moon Trpg Rule Book V1.8.4.pdf`、`originFab/Project Moon Trpg Rule Book V1.8.4.chm`：关键参考源，不作为日常施工输出目录
