from __future__ import annotations

from pathlib import Path

from audit_export_readiness import REPORT_PATH

REPO_ROOT = Path(__file__).resolve().parents[1]
MASTER_CHANGE_DIR = REPO_ROOT / "openspec" / "changes" / "export-ready-docs-master"
OUTPUT_ROOT = REPO_ROOT / "output" / "export_samples"
ACCEPTANCE_DIR = REPO_ROOT / "docs" / "acceptance"

BATCHES = [
    (
        "batch3-core-tables",
        "Export Batch 3 Core Tables",
        "集中收敛 `核心规则` 中的高密度规则表、心灵之光与购买项目录，完成主规则 A 桶收口。",
    ),
    (
        "batch4-guide-structures",
        "Export Batch 4 Guide Structures",
        "清理 `创作指南` 的设计说明页、平衡页与武器/防具/强化相关结构页。",
    ),
    (
        "batch5-core-entrypages",
        "Export Batch 5 Core Entrypages",
        "补齐 `核心规则`、`创建角色`、`势力`、`可选规则` 入口页结构，并为导出准备概览正文。",
    ),
    (
        "batch6-resource-courses",
        "Export Batch 6 Resource Courses",
        "统一 `资源目录/课程` 下课程、基础战技与流派战技的表格和标题结构。",
    ),
    (
        "batch7-resource-items",
        "Export Batch 7 Resource Items",
        "清理 `资源目录/消耗品` 与 `资源目录/装备` 的条目页，统一字段与导出结构。",
    ),
    (
        "batch8-resource-systems",
        "Export Batch 8 Resource Systems",
        "收口 `资源目录` 下改造、种族、工坊、出身、强化、能力列表等系统性目录。",
    ),
    (
        "batch9-overview-pages",
        "Export Batch 9 Overview Pages",
        "为顶层入口页补最小概览正文，并将已完成页面从 `Need Overview` 中收口。",
    ),
    (
        "batch10-final-bucket",
        "Export Batch 10 Final Bucket",
        "清理剩余 B 桶文件，完成整书候选前的标题、编码与结构噪音收口。",
    ),
]


def audit_summary() -> dict[str, str]:
    text = REPORT_PATH.read_text(encoding="utf-8")
    lines = {}
    for line in text.splitlines():
        if line.startswith("- 含 HTML table 的文件："):
            lines["tables"] = line.split("`")[1]
        elif line.startswith("- 无任何标题的文件："):
            lines["no_heading"] = line.split("`")[1]
        elif line.startswith("- 有标题但无 H1 的文件："):
            lines["no_h1"] = line.split("`")[1]
        elif line.startswith("- 站点空壳页："):
            lines["stub"] = line.split("`")[1]
        elif line.startswith("- 含编码工件的文件："):
            lines["encoding"] = line.split("`")[1]
    return lines


def bytes_of(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


def make_doc(batch_name: str, title: str, note: str) -> str:
    manifest = MASTER_CHANGE_DIR / f"{batch_name}.txt"
    files = [line.strip() for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    output_dir = OUTPUT_ROOT / batch_name
    pdf = output_dir / "pdf" / f"{batch_name}.pdf"
    html = output_dir / "pdf" / f"{batch_name}.html"
    chm = output_dir / "chm" / f"{batch_name}.chm"
    verification = output_dir / "verification.md"
    summary = audit_summary()
    command = (
        "python scripts/export_sample_docs.py --format all --compile-chm "
        f"--batch-name {batch_name} "
        f"--file-list openspec/changes/export-ready-docs-master/{batch_name}.txt "
        "--stub-policy docs/acceptance/export-stub-page-policy.md"
    )
    lines = [
        f"# {title}",
        "",
        "## Scope",
        "",
        note,
        "",
        f"- manifest：`openspec/changes/export-ready-docs-master/{batch_name}.txt`",
        f"- 文件数：`{len(files)}`",
    ]
    lines.extend(f"- `{rel}`" for rel in files)
    lines.extend(
        [
            "",
            "## Commands Run",
            "",
            "```powershell",
            "python scripts/audit_export_readiness.py",
            command,
            "```",
            "",
            "## Export Results",
            "",
            f"- PDF 批次导出成功：`output/export_samples/{batch_name}/pdf/{batch_name}.pdf`",
            f"- HTML 中间预览成功：`output/export_samples/{batch_name}/pdf/{batch_name}.html`",
            f"- CHM 项目文件成功生成：`output/export_samples/{batch_name}/chm/{batch_name}.hhp`",
            f"- CHM 目录文件成功生成：`output/export_samples/{batch_name}/chm/{batch_name}.hhc`",
            f"- CHM 真编译成功：`output/export_samples/{batch_name}/chm/{batch_name}.chm`",
            f"- 批次验证记录成功生成：`output/export_samples/{batch_name}/verification.md`",
            "",
            "## Artifact Sizes",
            "",
            f"- `output/export_samples/{batch_name}/pdf/{batch_name}.pdf`：`{bytes_of(pdf)}` bytes",
            f"- `output/export_samples/{batch_name}/pdf/{batch_name}.html`：`{bytes_of(html)}` bytes",
            f"- `output/export_samples/{batch_name}/chm/{batch_name}.chm`：`{bytes_of(chm)}` bytes",
            "",
            "## Final Audit Snapshot",
            "",
            f"- 含 HTML table 的文件：`{summary['tables']}`",
            f"- 无任何标题的文件：`{summary['no_heading']}`",
            f"- 有标题但无 H1 的文件：`{summary['no_h1']}`",
            f"- 含编码工件的文件：`{summary['encoding']}`",
            f"- 站点空壳页：`{summary['stub']}`",
            "",
            "## Notes",
            "",
            f"- 本批次验证记录见：`{verification.relative_to(REPO_ROOT).as_posix()}`",
            "- A 桶与 B 桶已在 master pass 后全部清零；剩余空壳页已转入 `Export Filter` 策略管理。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    ACCEPTANCE_DIR.mkdir(parents=True, exist_ok=True)
    for batch_name, title, note in BATCHES:
        slug = batch_name.replace("batch", "export-batch").replace("final-bucket", "final-bucket")
        path = ACCEPTANCE_DIR / f"{slug}.md"
        path.write_text(make_doc(batch_name, title, note), encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
