# Export Batch 8 Resource Systems

## Scope

收口 `资源目录` 下改造、种族、工坊、出身、强化、能力列表等系统性目录。

- manifest：`openspec/changes/export-ready-docs-master/batch8-resource-systems.txt`
- 文件数：`37`
- `资源目录/出身/传统武人.md`
- `资源目录/出身/基础出身.md`
- `资源目录/工坊/任意.md`
- `资源目录/工坊/任意/奥特兰卡酒吧.md`
- `资源目录/工坊/后巷.md`
- `资源目录/工坊/后巷/好棒棒快餐连锁.md`
- `资源目录/工坊/后巷/炎魔窟.md`
- `资源目录/工坊/巢内.md`
- `资源目录/工坊/巢内/宛冯煅冶所.md`
- `资源目录/工坊/郊区.md`
- `资源目录/工坊/郊区/公平代价.md`
- `资源目录/工坊/限定.md`
- `资源目录/强化/义体.md`
- `资源目录/强化/植入物.md`
- `资源目录/强化/纹身.md`
- `资源目录/强化/纹身/传说.md`
- `资源目录/强化/纹身/传说/墨染云影.md`
- `资源目录/强化/纹身/传说/山海异兽.md`
- `资源目录/强化/药物.md`
- `资源目录/改造/机体/传闻/侦查型.md`
- `资源目录/改造/机体/传闻/堡垒型.md`
- `资源目录/改造/机体/传闻/强攻型.md`
- `资源目录/改造/机体/传闻/火力型.md`
- `资源目录/改造/机体/传闻/通用型.md`
- `资源目录/改造/机体/怪谈/侦查型.md`
- `资源目录/改造/机体/怪谈/堡垒型.md`
- `资源目录/改造/机体/怪谈/强攻型.md`
- `资源目录/改造/部件/中型.md`
- `资源目录/改造/部件/大型.md`
- `资源目录/改造/部件/小型.md`
- `资源目录/改造/部件/巨型.md`
- `资源目录/改造/部件/怪谈/中型.md`
- `资源目录/改造/部件/怪谈/小型.md`
- `资源目录/改造/部件/系统.md`
- `资源目录/种族/基本种族.md`
- `资源目录/能力列表/出身类.md`
- `资源目录/能力列表/课程类.md`

## Commands Run

```powershell
python scripts/audit_export_readiness.py
python scripts/export_sample_docs.py --format all --compile-chm --batch-name batch8-resource-systems --file-list openspec/changes/export-ready-docs-master/batch8-resource-systems.txt --stub-policy docs/acceptance/export-stub-page-policy.md
```

## Export Results

- PDF 批次导出成功：`output/export_samples/batch8-resource-systems/pdf/batch8-resource-systems.pdf`
- HTML 中间预览成功：`output/export_samples/batch8-resource-systems/pdf/batch8-resource-systems.html`
- CHM 项目文件成功生成：`output/export_samples/batch8-resource-systems/chm/batch8-resource-systems.hhp`
- CHM 目录文件成功生成：`output/export_samples/batch8-resource-systems/chm/batch8-resource-systems.hhc`
- CHM 真编译成功：`output/export_samples/batch8-resource-systems/chm/batch8-resource-systems.chm`
- 批次验证记录成功生成：`output/export_samples/batch8-resource-systems/verification.md`

## Artifact Sizes

- `output/export_samples/batch8-resource-systems/pdf/batch8-resource-systems.pdf`：`22417` bytes
- `output/export_samples/batch8-resource-systems/pdf/batch8-resource-systems.html`：`120979` bytes
- `output/export_samples/batch8-resource-systems/chm/batch8-resource-systems.chm`：`64503` bytes

## Final Audit Snapshot

- 含 HTML table 的文件：`0`
- 无任何标题的文件：`0`
- 有标题但无 H1 的文件：`0`
- 含编码工件的文件：`0`
- 站点空壳页：`42`

## Notes

- 本批次验证记录见：`output/export_samples/batch8-resource-systems/verification.md`
- A 桶与 B 桶已在 master pass 后全部清零；剩余空壳页已转入 `Export Filter` 策略管理。
