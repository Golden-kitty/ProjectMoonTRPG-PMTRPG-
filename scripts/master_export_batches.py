from __future__ import annotations

import argparse
import re
from pathlib import Path

from audit_export_readiness import DOCS_DIR, analyze_file, iter_docs
from rebuild_html_tables_to_pipe import rebuild_file

REPO_ROOT = Path(__file__).resolve().parents[1]
MASTER_CHANGE_DIR = REPO_ROOT / "openspec" / "changes" / "export-ready-docs-master"

BATCH_RULES: dict[str, dict[str, object]] = {
    "batch3-core-tables": {
        "prefixes": [
            "核心规则/心灵之光/",
            "核心规则/购买项/",
            "核心规则/速查图表/",
        ],
        "files": ["核心规则/效果/升华与恶化.md"],
    },
    "batch4-guide-structures": {
        "prefixes": ["创作指南/"],
        "files": ["创作指南.md"],
    },
    "batch5-core-entrypages": {
        "prefixes": [
            "核心规则/创建角色/",
            "核心规则/势力/",
            "核心规则/可选规则/",
        ],
        "files": [
            "核心规则.md",
            "核心规则/创建角色.md",
            "核心规则/势力.md",
            "核心规则/可选规则.md",
            "核心规则/创建角色/战斗配置.md",
        ],
    },
    "batch6-resource-courses": {
        "prefixes": ["资源目录/课程/"],
        "files": ["资源目录/课程.md"],
    },
    "batch7-resource-items": {
        "prefixes": ["资源目录/消耗品/", "资源目录/装备/"],
        "files": [],
    },
    "batch8-resource-systems": {
        "prefixes": [
            "资源目录/改造/",
            "资源目录/种族/",
            "资源目录/工坊/",
            "资源目录/出身/",
            "资源目录/强化/",
            "资源目录/能力列表/",
        ],
        "files": ["资源目录/改造.md"],
    },
    "batch9-overview-pages": {
        "prefixes": [],
        "files": [
            "PM_TRPG.md",
            "核心规则.md",
            "资源目录.md",
            "创作指南.md",
            "都市箴言.md",
            "核心规则/势力.md",
            "核心规则/购买项.md",
            "核心规则/心灵之光.md",
            "核心规则/生活日常.md",
            "核心规则/创建角色.md",
            "核心规则/创建角色/战斗配置.md",
            "核心规则/可选规则.md",
        ],
    },
    "batch10-final-bucket": {
        "prefixes": [],
        "files": [],
        "dynamic_bucket": "B-高风险退化",
    },
}

OVERVIEW_TEMPLATES = {
    "PM_TRPG.md": "# PROJECT MOON TRPG\n\n本页作为规则书总入口，用于说明全文结构与阅读顺序。\n\n- `核心规则`：角色创建、战斗、效果、购买项、生活日常等主规则内容。\n- `资源目录`：装备、课程、工坊、改造、消耗品等条目索引。\n- `创作指南`：资源与规则设计参考。\n- `都市箴言`：术语、经验与设计思路汇总。\n",
    "核心规则.md": "# 核心规则\n\n本章汇总 PMTRPG 的核心玩法规则，建议按以下顺序阅读。\n\n- `创建角色`：完成角色基础构筑与初始配置。\n- `战斗`：理解战斗流程、拼点、伤害和状态处理。\n- `效果`：查阅效果参数、强度与效果表。\n- `购买项`：查看装备、强化、改造与相关规则入口。\n- `生活日常`：查阅休整、营养与非战斗流程。\n- `心灵之光`：查阅异想体、同调、压迫与变格相关规则。\n",
    "资源目录.md": "# 资源目录\n\n本章作为条目索引页，用于汇总可供角色获取、学习或使用的资源。\n\n- `装备`：武器、防具、衣物、饰品等条目。\n- `消耗品`：医疗品、爆炸物、燃料、食物等消耗资源。\n- `课程`：基础课程、基础战技与流派战技。\n- `改造`：义体、机体与部件类资源。\n- `种族`、`出身`、`强化`、`工坊`、`能力列表`：角色构筑与扩展资源。\n",
    "创作指南.md": "# 创作指南\n\n本章用于汇总资源设计、平衡与扩展规则的参考说明。\n\n- `资源设计表格`：统一条目结构与字段参考。\n- `属性平衡`、`战技平衡`：数值与构筑平衡说明。\n- `武器设计`、`防具设计`、`强化类设计`：常见条目设计入口。\n\n建议在扩展新条目前，先查阅对应设计页，再回到正文目录核对成品结构。\n",
    "都市箴言.md": "# 都市箴言\n\n本章用于收纳 PMTRPG 的术语说明、经验总结与扩展设计思路。\n\n- 用作跨章节阅读时的概念补充，而不是替代正文规则。\n- 优先作为创作、主持与长期维护时的参考索引。\n",
    "核心规则/势力.md": "# 势力\n\n本页作为势力章节概览，用于说明本章的阅读定位。\n\n- 本章主要描述都市中的势力结构、关系与相关规则入口。\n- 具体势力内容应以下级页面为准；本页仅负责导览与范围说明。\n",
    "核心规则/购买项.md": "# 购买项\n\n本页作为购买项章节概览，用于说明装备、强化、改造与课程相关内容的入口关系。\n\n- `装备`：常规可购买装备与武器条目。\n- `强化`：纹身、药物、植入物等强化类内容。\n- `改造`：机体、系统、部件等改造条目。\n- `课程`：可学习的课程、基础战技与流派战技。\n",
    "核心规则/心灵之光.md": "# 心灵之光\n\n本页作为心灵之光章节概览，用于引导阅读异想体、同调、压迫与变格相关规则。\n\n- `异想体`：异想体背景与接触前提。\n- `同调`、`压迫`：与异想体互动的核心判定流程。\n- `变格之路`：角色在情感与具现层面的进一步发展。\n",
    "核心规则/生活日常.md": "# 生活日常\n\n本页作为生活日常章节概览，用于说明非战斗流程与长期资源管理内容。\n\n- `休整`：短休、长休与营地动作。\n- `食物与营养`：营养、恢复骰与相关非战斗效果。\n",
    "核心规则/创建角色.md": "# 创建角色\n\n本页作为创建角色章节概览，用于说明角色建立时的阅读顺序。\n\n- 先确认种族、出身、经历与背景。\n- 再进入技能、特质与美德属性等基础构筑页。\n- 最后根据战斗配置完成战技栏、物品栏与特质栏设置。\n",
    "核心规则/创建角色/战斗配置.md": "# 战斗配置\n\n本页作为战斗配置章节概览，用于说明角色进入战斗前的配置结构。\n\n- `战技与战技栏`：准备战技组与战技栏位。\n- `物品与物品栏`：随身栏位、容器与背包栏。\n- `特质与特质栏`：可生效特质数量与栏位结构。\n",
    "核心规则/可选规则.md": "# 可选规则\n\n本页作为可选规则章节概览，用于说明扩展与变体规则的使用方式。\n\n- 本章内容默认不强制启用，应由 TG 与玩家共同确认。\n- 具体变体效果与适用边界以下级页面为准。\n",
}

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.M)


def normalize_spaces(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def promote_or_add_h1(text: str, rel: str) -> str:
    matches = list(HEADING_RE.finditer(text))
    stem = Path(rel).stem
    if not matches:
        return f"# {stem}\n\n{text.lstrip()}"

    h1_count = sum(1 for m in matches if len(m.group(1)) == 1)
    if h1_count:
        return text

    first = matches[0]
    heading_text = first.group(2).strip()
    replacement = f"# {heading_text}"
    if first.start() == 0:
        return text[: first.start()] + replacement + text[first.end() :]
    return f"# {stem}\n\n{text.lstrip()}"


def ensure_overview(rel: str) -> bool:
    template = OVERVIEW_TEMPLATES.get(rel)
    if not template:
        return False
    path = DOCS_DIR / rel
    current = path.read_text(encoding="utf-8")
    if current.strip() == template.strip():
        return False
    info = analyze_file(path, rel)
    non_heading_lines = [
        line.strip()
        for line in current.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if info["stub"] or len(non_heading_lines) <= 3:
        path.write_text(template, encoding="utf-8")
        return True
    return False


def fix_file(rel: str) -> bool:
    path = DOCS_DIR / rel
    if not path.exists():
        return False

    changed = False
    if "<table" in path.read_text(encoding="utf-8", errors="replace").lower():
        changed = rebuild_file(str(path)) or changed

    text = path.read_text(encoding="utf-8")
    new_text = normalize_spaces(text)
    new_text = promote_or_add_h1(new_text, rel)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8", newline="\n")
        changed = True
    return changed


def select_batch(rel_paths: list[str], batch_name: str) -> list[str]:
    rule = BATCH_RULES[batch_name]
    files = set(rule.get("files", []))
    prefixes = tuple(rule.get("prefixes", []))

    if "dynamic_bucket" in rule:
        bucket_name = str(rule["dynamic_bucket"])
        selected = []
        for rel in rel_paths:
            info = analyze_file(DOCS_DIR / rel, rel)
            bucket = (
                "A-阻塞导出"
                if info["tables"] or info["image_hook_dependent"] or info["no_heading"]
                else "B-高风险退化"
                if info["no_h1"] or info["nbspace"] or info["replacement_char"]
                else "C-导航空壳"
                if info["stub"]
                else None
            )
            if bucket == bucket_name:
                selected.append(rel)
        return sorted(selected)

    selected = []
    for rel in rel_paths:
        if rel in files or (prefixes and rel.startswith(prefixes)):
            selected.append(rel)
    return sorted(set(selected))


def write_manifests() -> None:
    rel_paths = [rel for _path, rel in iter_docs()]
    MASTER_CHANGE_DIR.mkdir(parents=True, exist_ok=True)
    for batch_name in BATCH_RULES:
        selected = select_batch(rel_paths, batch_name)
        manifest = MASTER_CHANGE_DIR / f"{batch_name}.txt"
        manifest.write_text("\n".join(selected) + ("\n" if selected else ""), encoding="utf-8")
        print(f"manifest {batch_name} {len(selected)}")


def fix_batch(batch_name: str) -> None:
    manifest = MASTER_CHANGE_DIR / f"{batch_name}.txt"
    rels = [line.strip() for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    changed = 0
    if batch_name == "batch9-overview-pages":
        for rel in rels:
            if ensure_overview(rel):
                changed += 1
    for rel in rels:
        if fix_file(rel):
            changed += 1
    print(f"fixed {batch_name} {changed}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("write-manifests")
    fix = sub.add_parser("fix-batch")
    fix.add_argument("--batch", required=True, choices=sorted(BATCH_RULES))
    args = parser.parse_args()

    if args.cmd == "write-manifests":
        write_manifests()
    else:
        fix_batch(args.batch)


if __name__ == "__main__":
    main()
