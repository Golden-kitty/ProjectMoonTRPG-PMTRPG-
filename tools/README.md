# tools（Windows）

本项目默认在 Windows 下优先使用项目根目录 `tools/` 内的工具：

- 7-Zip：`tools/7-Zip/7z.exe`
- Pandoc：`tools/Pandoc/pandoc.exe`

如系统已配置 `PATH`，脚本也支持从 `PATH` 查找。

# tools 目录说明（Windows）

本项目在 Windows 下默认会优先从项目根目录的 `tools/` 中查找依赖工具：

- `tools/7-Zip/7z.exe`
- `tools/Pandoc/pandoc.exe`

如本机已在 `PATH` 中配置了 7-Zip 或 Pandoc，脚本也会保留对 `PATH` 的查找/回退逻辑。

> 说明：本仓库默认忽略 `tools/` 下的二进制文件（见 `.gitignore`），但保留本说明文件。

