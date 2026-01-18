# WinCHM 导出 → Markdown（管理员工作流）

本文用于把 WinCHM 导出的 HTML Tree（保留目录结构）批量转换为本仓库的 Markdown 文档。

## 1. 前置条件（Windows）
- 已安装 Python（命令行可用 `python`）
- 已准备 Pandoc（推荐放到仓库根目录）：`tools/Pandoc/pandoc.exe`
- WinCHM 已导出 “HTML Tree” 到一个目录，例如：
  - `D:\Database\Project\workrepo\PMTRPG\CHM`

## 2. 执行导入

在仓库根目录运行（PowerShell）：

```powershell
.\scripts\import_winchm_export.ps1 -Src "D:\Database\Project\workrepo\PMTRPG\CHM" -Clean
```

输出：
- `docs/`：转换后的 `.md`（保留原目录结构）
- `assets/chm/`：从导出目录中复制出来的图片资源（并自动重写 md 内图片路径）

## 3. 注意事项
- 源 HTML 多为 `gb2312` 编码，但实际常包含 GBK 扩展字符；脚本会按 `gbk` 解码后转为 UTF-8 再喂给 Pandoc，避免出现 `�`。
- 本仓库以 **GitHub Markdown 渲染**为准：导入脚本默认开启 `--target github`，会将 `<img>` 转为 `![]()`，并尽量移除无用的 `<div>`/`colgroup`/`col`/`table` 属性，提升 GitHub 预览稳定性。
- 复杂表格在 Pandoc 下仍可能以 HTML table 形式输出（GitHub 可正常渲染）。如你要求全部转为管道表，需要再做针对性重建。

