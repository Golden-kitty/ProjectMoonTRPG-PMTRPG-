# Workflow Guide

本文汇总 PMTRPG 仓库当前的工程化工作流，包括本地环境、站点构建与 GitHub Pages 发布。

## 当前工作流

- 内容源以 `docs/` 为准
- 图片素材以仓库根目录 `assets/` 为准
- WinCHM 导入继续遵循 `IMPORT_GUIDE.md`
- 当前构建策略为“在线站点优先”，后续再复用同一导航顺序接入 `CHM + Word`

## 本地环境

如需在 `Cursor / VS Code` 中使用统一环境，可在仓库根目录创建并复用 `.venv`。

1. Windows 示例：`py -3 -m venv .venv`
2. 安装完整本地环境：`.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt`
3. 在编辑器中选择解释器：`${workspaceFolder}/.venv/Scripts/python.exe`

依赖说明：

- `requirements-site.txt`：仅站点构建依赖
- `requirements-viz.txt`：仅可视化依赖
- `requirements-dev.txt`：同时安装站点构建与可视化依赖

## 站点构建

1. 安装依赖：
   `python -m pip install -r requirements-site.txt`
2. 本地构建：
   `python scripts/build_site.py build`
3. 本地预览：
   `python scripts/build_site.py serve`

补充说明：

- `scripts/generate_mkdocs_config.py` 会基于 `docs/PDF章节页码映射.md` 生成 `mkdocs.yml`
- `scripts/mkdocs_hooks.py` 会在渲染前修正指向仓库根目录 `assets/` 的相对路径，并在构建后将 `assets/` 复制到 `site/assets/`
- 构建完成后会自动从 `PM_TRPG.html` 生成 `site/index.html`，用于 GitHub Pages 根路径访问
- 公开站点默认不包含治理 / 审计文档

## GitHub Pages 发布

### 首次启用

1. 确认以下文件已提交到目标分支：
   - `.github/workflows/deploy-site.yml`
   - `requirements-site.txt`
   - `mkdocs.yml`
   - `scripts/build_site.py`
   - `scripts/generate_mkdocs_config.py`
   - `scripts/mkdocs_hooks.py`
2. 打开 GitHub 仓库 `Settings -> Pages`
3. 在 `Build and deployment` 中将 `Source` 设为 `GitHub Actions`
4. 确认仓库 / 组织没有禁用 GitHub Actions 或 Pages 权限

### 触发方式

- 自动触发：当前工作流监听 `main` 与 `hotFix` 分支的 `push`
- 手动触发：可在 GitHub 的 `Actions` 页面手动运行 `deploy-site`
- 如果未来调整发布分支，需要同步修改 `.github/workflows/deploy-site.yml` 中的 `on.push.branches`

### 发布前自检

1. 执行 `python -m pip install -r requirements-site.txt`
2. 执行 `python scripts/build_site.py build`
3. 如需人工预览，执行 `python scripts/build_site.py serve`
4. 确认 `site/` 已生成，并抽查关键页面图片是否可见

### 首次发布流程

1. 将站点相关改动合并到 `main` 或 `hotFix`
2. 打开 GitHub 的 `Actions` 页面，确认 `deploy-site` 已运行
3. 首次成功后，到 `Settings -> Pages` 或工作流日志中的 `github-pages` 环境查看站点 URL
4. 如果刚发布时仍返回 404，等待 1-3 分钟后刷新

## 常见问题

- `push` 后没有自动发布：
  通常是因为当前提交不在 `main` / `hotFix`，或 `Settings -> Pages` 的 `Source` 仍不是 `GitHub Actions`
- Actions 中出现权限错误：
  检查仓库或组织是否限制了 GitHub Actions / Pages
- 本地能构建，线上失败：
  先重新执行 `python scripts/build_site.py build`，再对照 `Actions` 日志检查依赖安装和路径问题
- 页面图片缺失：
  优先确认构建日志中是否出现 `[mkdocs_hooks] copied assets`
- 修改了 `docs/PDF章节页码映射.md` 后导航未更新：
  重新运行 `python scripts/build_site.py build`，该脚本会先生成新的 `mkdocs.yml`
- 根 URL 出现 `The site configured at this address does not contain the requested file.`：
  说明线上还是旧构建产物，重新部署当前版本即可
