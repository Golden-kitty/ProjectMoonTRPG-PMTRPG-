# ProjectMoonTRPG-PMTRPG-
以月亮计划的游戏（脑叶公司、废墟图书馆等）的世界观为背景的TRPG桌面规则。

## 文档入口

- `docs/PM_TRPG.md`：规则书正文（Markdown）
- `originFab/Project Moon Trpg Rule Book V1.8.4.pdf`：原始 PDF
- `docs/PDF图片索引.md`：PDF 全页缩略图索引（便于逐页查阅/引用）
- `docs/PDF章节页码映射.md`：PDF 目录章节 ↔ 页码 ↔ 对应 Markdown 文件的映射索引
- `docs/project-brief.md`：当前阶段目标、约束与现有材料映射
- `docs/project-memory.md`：当前施工共识、风险与开放问题

## 当前工作流

- 内容源仍以 `docs/` 为准，图片素材仍以仓库根目录 `assets/` 为准
- WinCHM 导入继续遵循 `IMPORT_GUIDE.md`
- 当前构建策略转为“在线站点优先”，先落地 `MkDocs + GitHub Pages`，后续再复用同一导航顺序接入 `CHM + Word`

## 站点构建

1. 安装依赖：
   `python -m pip install -r requirements-site.txt`
2. 本地构建：
   `python scripts/build_site.py build`
3. 本地预览：
   `python scripts/build_site.py serve`

说明：

- `scripts/generate_mkdocs_config.py` 会基于 `docs/PDF章节页码映射.md` 生成 `mkdocs.yml`
- `scripts/mkdocs_hooks.py` 会在渲染前修正指向仓库根目录 `assets/` 的相对路径，并在构建后把 `assets/` 复制到 `site/assets/`
- 公开站点默认不包含治理 / 审计文档
- GitHub Actions 会在 `main` 或 `hotFix` 分支推送后自动部署到 GitHub Pages

## GitHub Pages 发布

### 首次启用

1. 先把站点相关文件提交到仓库：
   - `.github/workflows/deploy-site.yml`
   - `requirements-site.txt`
   - `scripts/build_site.py`
   - `scripts/generate_mkdocs_config.py`
   - `scripts/mkdocs_hooks.py`
   - `mkdocs.yml`
2. 打开 GitHub 仓库的 `Settings -> Pages`
3. 在 `Build and deployment` 中将 `Source` 设为 `GitHub Actions`
4. 确认仓库 / 组织没有禁用 GitHub Actions 或 Pages 部署权限

### 触发方式

- 自动触发：当前工作流监听 `main` 与 `hotFix` 分支的 `push`
- 手动触发：可在 GitHub 的 `Actions` 页面手动运行 `deploy-site`
- 如果仓库长期不使用 `main` 作为发布分支，需要同步修改 `.github/workflows/deploy-site.yml` 中的 `on.push.branches`

### 发布前自检

1. 本地安装依赖：
   `python -m pip install -r requirements-site.txt`
2. 本地构建：
   `python scripts/build_site.py build`
3. 如需人工预览：
   `python scripts/build_site.py serve`
4. 确认 `site/` 已生成，且抽查关键页面图片是否可见

### 首次发布流程

1. 将站点相关改动合并到 `main`，或在 `Actions` 中手动选择目标分支运行 `deploy-site`
2. 进入 GitHub 的 `Actions` 页面，等待 `deploy-site` 的 `build` 与 `deploy` 两个 job 完成
3. 首次成功后，到 `Settings -> Pages` 或工作流日志中的 `github-pages` 环境查看站点 URL
4. 若页面刚发布时仍返回 404，等待 1-3 分钟后刷新再试

### 常见问题

- `push` 后没有自动发布：
  通常是因为当前提交不在 `main` 分支，或工作流文件尚未存在于 GitHub 上的目标分支
- Actions 中出现权限错误：
  检查仓库或组织是否限制了 GitHub Actions / Pages，必要时确认 `Settings -> Pages` 已启用 `GitHub Actions`
- 本地能构建，线上失败：
  先重新执行 `python scripts/build_site.py build`，再对照 `Actions` 日志检查依赖安装或路径问题
- 页面图片缺失：
  优先确认构建日志中是否出现 `[mkdocs_hooks] copied assets`，以及正文页面中的图片是否仍引用 `assets/`
- 修改了 `docs/PDF章节页码映射.md` 后导航未更新：
  重新运行 `python scripts/build_site.py build`，该脚本会先生成新的 `mkdocs.yml`
- 根 URL 打开后出现 `The site configured at this address does not contain the requested file.`：
  旧构建产物里缺少 `index.html`。重新构建并重新部署当前版本后，`scripts/mkdocs_hooks.py` 会自动从 `PM_TRPG.html` 生成 `index.html`