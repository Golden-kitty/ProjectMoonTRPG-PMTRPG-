# export-ready-docs

## Why

PMTRPG 仓库已经完成 Site-First 基线，并验证了站点可以构建、部署和访问。

但实际抽查表明：

- 站点通过并不代表 PDF / CHM 导出质量通过
- `MkDocs` 的 hook、导航和链接容错掩盖了源文档中的结构问题
- 若直接进入整书打包，问题会在标题层级、图片路径、HTML table 和空壳页上集中爆发

## What Changes

- 新增 `document-export-readiness` 能力 spec
- 新增 export-ready 的 `Task Brief`、`Acceptance` 和 OpenSpec change 图纸
- 新增导出审计脚本和导出样本脚本
- 修复最小样本集中的关键阻塞项
- 记录 PDF / CHM 样本导出证据与剩余风险

## OutOfScope

- 不在本次 change 中完成整书 PDF / CHM 最终成品
- 不一次性统一所有正文章节的视觉样式
- 不修改 `originFab/`
- 不顺手大规模改写与样本无关的正文文件

## Provides

- 一条可恢复的 export-ready longflow
- 一份导出阻塞项清单
- 一组已过样本验证的正文页面
- 面向 PDF / CHM 的独立验收证据
