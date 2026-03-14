# T-002: Site-First Workflow Baseline

## TaskType
Implementation

## Goal
在 PMTRPG 仓库内先落地“在线站点优先”的新工作流，使 `docs/` 可以稳定生成静态站点并接入 GitHub Pages，同时为后续 `CHM + Word` 共用导航顺序与资源策略打基础。

## WhyNow
当前仓库已经完成 WinCHM / PDF -> Markdown 的主要导入与清洗工作，但尚未落地站点、CI/CD 和可复用的导航顺序。继续只做清洗会让后续产物链条迟迟没有真实落点。

## InScope
- 新增站点优先工作流的正式 `Task Brief` 与 `Acceptance`
- 为 `docs/PDF章节页码映射.md` 建立可复用的导航生成脚本
- 新增 `MkDocs` 站点配置生成器和本地构建包装脚本
- 为站点构建增加资源复制策略，确保 `assets/chm/` 中被正文依赖的图片可见
- 新增 GitHub Actions / Pages 部署工作流
- 更新 `README.md`、`docs/project-brief.md`、`docs/project-memory.md`，记录当前阶段转向

## OutOfScope
- 本次不实现特殊背景页 / Frontmatter 样式体系
- 本次不直接产出 CHM 或 Word
- 本次不大规模重写 `docs/**/*.md` 正文内容或统一所有标题层级
- 本次不修改 `originFab/`、`assets/` 现有素材本体

## Provides
- 一套可在本仓库直接运行的站点优先工作流
- 以 `docs/PDF章节页码映射.md` 为来源的可复用导航顺序
- GitHub Pages 自动部署链路
- 为后续 `CHM + Word` 复用的资源与导航基础

## EditableAreas
- `README.md`
- `docs/project-brief.md`
- `docs/project-memory.md`
- `docs/tasks/`
- `docs/acceptance/`
- `scripts/`
- `.github/workflows/`
- `.gitignore`
- `requirements-site.txt`

## ForbiddenAreas
- `originFab/`
- `assets/` 现有素材本体
- `tools/`
- `output/`
- `docs/**/*.md` 的大规模正文重写

## Contracts
- 站点导航顺序应以 `docs/PDF章节页码映射.md` 为主来源，避免另造一套长期真相
- 构建时资源复制只能使用现有 `assets/`，不得重写原素材目录
- 内部治理 / 审计材料默认不进入公开站点导航
- 站点工作流必须为后续 `CHM + Word` 保留复用空间，而不是绑定到一次性手工配置

## AcceptanceChecks
- [ ] 仓库内存在可执行的 `MkDocs` 站点配置生成与本地构建脚本
- [ ] `mkdocs build` 可成功产出站点
- [ ] 站点导航覆盖主要正文章节，且顺序与 `docs/PDF章节页码映射.md` 一致
- [ ] 依赖 `assets/chm/` 的正文图片在站点构建产物中可访问
- [ ] `docs/project-brief.md` 与 `docs/project-memory.md` 已反映当前阶段转向
- [ ] GitHub Actions / Pages 工作流已就位，且不要求修改原始素材即可运行

## SuggestedTests
- 本地运行站点构建脚本并检查 `site/` 是否生成
- 抽查包含图片的正文页面，确认图片链接可解析
- 人工抽查站点顶层导航顺序与 `docs/PDF章节页码映射.md` 是否一致
- 检查公开导航中未包含治理 / 审计文档

## ReturnFormat
- Changed
- NotChanged
- TestsRun
- Evidence
- OpenRisks
- Questions
- SuggestedDocUpdates
