# AC-002: Site-First Workflow Acceptance

## Capability Under Review
PMTRPG 仓库的“在线站点优先”工作流基线，包括导航生成、资源复制、本地构建与 GitHub Pages 部署。

## Preconditions
- `T-002: Site-First Workflow Baseline` 已明确目标、边界和验收条件
- `docs/PDF章节页码映射.md` 仍可作为章节顺序主来源
- 构建机可访问 `docs/`、`assets/`、`scripts/` 与新增站点依赖

## Happy Paths
- [ ] 站点配置可由仓库内脚本稳定生成，而不是完全依赖手工维护
- [ ] `mkdocs build` 成功并产出公开站点
- [ ] 站点导航主顺序与 `docs/PDF章节页码映射.md` 对齐
- [ ] 依赖 `assets/chm/` 的正文图片在构建产物中可访问
- [ ] GitHub Actions / Pages 工作流可从仓库默认分支部署站点

## Edge Cases
- [ ] 多候选映射不会被静默选错；若无法可靠判定，应保守降级为分组节点而非错误页面
- [ ] 治理 / 审计材料不应默认进入公开导航
- [ ] 站点构建不应要求移动或改写现有 `assets/` 原素材
- [ ] 站点顺序调整应能复用于后续 CHM / Word，而不是只对 MkDocs 有效

## CounterExamples / Must Not Happen
- [ ] 只因为 `mkdocs build` 跑通就判定完成，而未检查导航与资源可达性
- [ ] 为了构建通过而顺手大批量改写正文文件
- [ ] 新增第二套与 `docs/PDF章节页码映射.md` 冲突的长期章节顺序
- [ ] 把 `originFab/`、`output/` 或治理型材料误公开为站点正文

## Regression Points
- [ ] 现有导入约束（编码、图片复制、GitHub 渲染目标）未被错误覆盖
- [ ] `README.md`、项目简述和项目记忆中的阶段描述保持一致
- [ ] 站点构建链的新增文件不会破坏现有脚本或清洗工作流

## Required Evidence
- 相关新增 / 修改文件 diff
- 一次本地构建结果
- 关键页面的图片 / 导航抽查结果
- 如有保守降级的分组节点，需说明原因与影响范围

## Pass Rule
站点工作流文件齐备，构建成功，导航与资源抽查通过，且没有越界修改或顺手重写正文时，可判通过。

## Fail Rule
若导航顺序明显偏离、关键图片不可访问、越界修改正文或缺少构建 / 抽查证据，则退回。
