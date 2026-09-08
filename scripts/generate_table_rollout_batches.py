"""Generate deterministic Stage 7 table-level rollout and review manifests.

The source documents are kept atomic: every table from one Markdown document is
assigned to the same batch. Accepted and source-verified sets are hash/evidence
pinned so later source edits cannot silently inherit an earlier review result.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TIER_NAMES = ("simple", "span", "image", "special")
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def table_tier(item: dict[str, Any]) -> int:
    if int(item.get("nested_depth", 0)) > 0:
        return 3
    if item.get("images"):
        return 2
    if item.get("risk") == "high":
        return 3
    spans = item.get("span_signature", [])
    if any(int(span.get("colspan", 1)) > 1 or int(span.get("rowspan", 1)) > 1 for span in spans):
        return 1
    return 0


def build_documents(items: list[dict[str, Any]], repo_root: Path) -> list[dict[str, Any]]:
    by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        by_path[item["path"]].append(item)

    documents: list[dict[str, Any]] = []
    for path, tables in by_path.items():
        tables.sort(key=lambda item: (int(item.get("line", 0)), item["id"]))
        tiers = [table_tier(item) for item in tables]
        risks = [RISK_ORDER.get(str(item.get("risk")), 99) for item in tables]
        source_path = repo_root / path
        if not source_path.is_file():
            raise ValueError(f"source document missing: {path}")
        documents.append(
            {
                "path": path,
                "sha256": sha256_file(source_path),
                "table_count": len(tables),
                "tier": max(tiers),
                "risk": max(risks),
                "tables": tables,
            }
        )
    documents.sort(key=lambda item: (item["tier"], item["risk"], item["path"]))
    return documents


def partition_documents(
    documents: list[dict[str, Any]], minimum: int, maximum: int, target: int
) -> list[list[dict[str, Any]]]:
    """Partition an ordered document list without splitting documents."""

    if not (0 < minimum <= target <= maximum):
        raise ValueError("expected 0 < minimum <= target <= maximum")
    if any(int(document["table_count"]) > maximum for document in documents):
        oversized = [document["path"] for document in documents if document["table_count"] > maximum]
        raise ValueError(f"documents exceed maximum batch size: {oversized}")

    size = len(documents)
    costs = [float("inf")] * (size + 1)
    previous: list[int | None] = [None] * (size + 1)
    costs[0] = 0.0
    for end in range(1, size + 1):
        table_count = 0
        tiers: set[int] = set()
        for start in range(end - 1, -1, -1):
            document = documents[start]
            table_count += int(document["table_count"])
            tiers.add(int(document["tier"]))
            if table_count > maximum:
                break
            if table_count < minimum or costs[start] == float("inf"):
                continue
            tier_penalty = max(0, len(tiers) - 1) * 9
            cost = costs[start] + (table_count - target) ** 2 + tier_penalty
            if cost < costs[end]:
                costs[end] = cost
                previous[end] = start

    if previous[size] is None:
        raise ValueError(
            f"cannot partition {sum(document['table_count'] for document in documents)} tables "
            f"into document-atomic batches of {minimum}-{maximum}"
        )

    result: list[list[dict[str, Any]]] = []
    end = size
    while end:
        start = previous[end]
        if start is None:
            raise AssertionError("broken batch partition")
        result.append(documents[start:end])
        end = start
    result.reverse()
    return result


def load_acceptances(
    registry_path: Path,
    source_items: dict[str, dict[str, Any]],
    repo_root: Path,
) -> dict[str, str]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    accepted: dict[str, str] = {}
    for accepted_set in registry.get("accepted_sets", []):
        set_id = accepted_set["id"]
        document_paths = {document["path"] for document in accepted_set.get("documents", [])}
        for document in accepted_set.get("documents", []):
            actual = sha256_file(repo_root / document["path"])
            if actual != document["sha256"]:
                raise ValueError(
                    f"accepted document changed since {set_id}: {document['path']} "
                    f"expected {document['sha256']}, got {actual}"
                )
        registered_ids = set(accepted_set.get("table_ids", []))
        current_ids = {item_id for item_id, item in source_items.items() if item["path"] in document_paths}
        if registered_ids != current_ids:
            missing = sorted(registered_ids - current_ids)
            added = sorted(current_ids - registered_ids)
            raise ValueError(f"accepted table set drifted for {set_id}: missing={missing}, added={added}")
        for item_id in sorted(registered_ids):
            if item_id in accepted:
                raise ValueError(f"table accepted by multiple sets: {item_id}")
            accepted[item_id] = set_id
    return accepted


def load_review_policy(
    policy_path: Path,
    source_items: dict[str, dict[str, Any]],
    repo_root: Path,
) -> tuple[dict[str, Any], dict[str, str]]:
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    if policy.get("mode") != "high-risk-source-only":
        raise ValueError(f"unsupported review policy mode: {policy.get('mode')}")

    verified: dict[str, str] = {}
    for evidence_set in policy.get("source_verified_sets", []):
        set_id = evidence_set["id"]
        record_path = repo_root / evidence_set["evidence_record"]
        if not record_path.is_file():
            raise ValueError(f"source verification evidence missing for {set_id}: {record_path}")
        for item_id in evidence_set.get("table_ids", []):
            if item_id not in source_items:
                raise ValueError(f"source-verified table missing from inventory: {item_id}")
            if item_id in verified:
                raise ValueError(f"table source-verified by multiple sets: {item_id}")
            verified[item_id] = set_id
    return policy, verified


def load_high_risk_reviews(
    registry_path: Path,
    source_items: dict[str, dict[str, Any]],
    repo_root: Path,
) -> dict[str, str]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    reviewed: dict[str, str] = {}
    for reviewed_set in registry.get("reviewed_sets", []):
        set_id = reviewed_set["id"]
        document_paths = {document["path"] for document in reviewed_set.get("documents", [])}
        for document in reviewed_set.get("documents", []):
            actual = sha256_file(repo_root / document["path"])
            if actual != document["sha256"]:
                raise ValueError(
                    f"high-risk reviewed document changed since {set_id}: {document['path']} "
                    f"expected {document['sha256']}, got {actual}"
                )
        for item_id in reviewed_set.get("table_ids", []):
            if item_id not in source_items:
                raise ValueError(f"high-risk reviewed table missing from inventory: {item_id}")
            if source_items[item_id]["path"] not in document_paths:
                raise ValueError(f"high-risk reviewed table is outside hash-pinned documents: {item_id}")
            if item_id in reviewed:
                raise ValueError(f"table appears in multiple high-risk review sets: {item_id}")
            reviewed[item_id] = set_id
    return reviewed


def high_risk_reasons(item: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    """Return deterministic source-review triggers for one canonical table."""

    criteria = policy["high_risk_criteria"]
    reasons: list[str] = []
    nested_depth = int(item.get("nested_depth", 0))
    if nested_depth > int(criteria["nested_depth_greater_than"]):
        reasons.append(f"nested_depth={nested_depth}")

    max_rowspan = max(
        (int(span.get("rowspan", 1)) for span in item.get("span_signature", [])),
        default=1,
    )
    if max_rowspan > int(criteria["rowspan_greater_than"]):
        reasons.append(f"rowspan={max_rowspan}")

    columns = int(item.get("columns") or 0)
    if columns >= int(criteria["columns_at_least"]):
        reasons.append(f"columns={columns}")

    candidates = item.get("source_page_candidates", [])
    area = int(item.get("rows") or 0) * columns
    if (
        len(candidates) > int(criteria["page_candidate_count_greater_than"])
        and area >= int(criteria["ambiguous_mapping_area_at_least"])
    ):
        reasons.append(f"ambiguous_page_candidates={len(candidates)},area={area}")
    return reasons


def classify_review_status(
    item: dict[str, Any],
    accepted: dict[str, str],
    source_verified: dict[str, str],
    high_risk_reviewed: dict[str, str],
    policy: dict[str, Any],
) -> tuple[str, list[str], str | None]:
    item_id = item["id"]
    if item_id in accepted:
        return "accepted_by_user", [], accepted[item_id]
    if item_id in source_verified:
        return "source_verified_by_pdf_evidence", [], source_verified[item_id]
    reasons = high_risk_reasons(item, policy)
    if item_id in high_risk_reviewed:
        if not reasons:
            raise ValueError(f"review registry contains a table outside the high-risk policy: {item_id}")
        return "source_verified_by_high_risk_review", reasons, high_risk_reviewed[item_id]
    if reasons:
        return "high_risk_source_review_required", reasons, None
    return "closed_by_user_review_policy", [], None


def git_head(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def summarize_features(tables: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(TIER_NAMES[table_tier(item)] for item in tables)
    return {name: counts.get(name, 0) for name in TIER_NAMES}


def write_review_queue(path: Path, manifests: list[dict[str, Any]]) -> None:
    fields = [
        "batch_id",
        "table_id",
        "path",
        "line",
        "risk",
        "feature_tier",
        "source_page_candidates",
        "review_status",
        "high_risk_reasons",
        "acceptance_set",
        "evidence_set",
        "review_owner",
        "review_notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for manifest in manifests:
            for table in manifest["tables"]:
                writer.writerow(
                    {
                        "batch_id": manifest["batch_id"],
                        "table_id": table["id"],
                        "path": table["path"],
                        "line": table["line"],
                        "risk": table["risk"],
                        "feature_tier": table["feature_tier"],
                        "source_page_candidates": ";".join(
                            str(page) for page in table["source_page_candidates"]
                        ),
                        "review_status": table["review_status"],
                        "high_risk_reasons": ";".join(table.get("high_risk_reasons", [])),
                        "acceptance_set": table.get("acceptance_set", ""),
                        "evidence_set": table.get("evidence_set", ""),
                        "review_owner": {
                            "accepted_by_user": "user",
                            "source_verified_by_pdf_evidence": "implementer",
                            "source_verified_by_high_risk_review": "Codex",
                            "high_risk_source_review_required": "Codex",
                            "closed_by_user_review_policy": "policy",
                        }[table["review_status"]],
                        "review_notes": "",
                    }
                )


def write_high_risk_review(path: Path, policy: dict[str, Any], manifests: list[dict[str, Any]]) -> None:
    tables = [
        table
        for manifest in manifests
        for table in manifest["tables"]
        if table["review_status"]
        in {"source_verified_by_high_risk_review", "high_risk_source_review_required"}
    ]
    reviewed_count = sum(
        table["review_status"] == "source_verified_by_high_risk_review" for table in tables
    )
    pending_count = sum(
        table["review_status"] == "high_risk_source_review_required" for table in tables
    )
    payload = {
        "schema_version": 1,
        "status": "IN_PROGRESS" if pending_count else "PASS",
        "review_mode": policy["mode"],
        "review_owner": "Codex",
        "user_review_required_only_for": "unresolved_semantic_ambiguity",
        "high_risk_criteria": policy["high_risk_criteria"],
        "table_count": len(tables),
        "document_count": len({table["path"] for table in tables}),
        "reviewed_table_count": reviewed_count,
        "pending_table_count": pending_count,
        "tables": tables,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_summary_markdown(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Canonical HTML 表格阶段 7 分批记录",
        "",
        "## 任务边界",
        "",
        "- **TaskType**：全量表格迁移的批次化证据与高风险源表复核队列。",
        "- **Goal**：把 369 张 canonical HTML 正文表按每批 20–40 张分组，保持同一文档原子性，并依据用户确认的高风险复核策略记录状态、内容哈希和回滚门禁。",
        "- **OutOfScope**：重复要求用户验收每批 CHM/DOCX/PDF、修改规则正文、拆分混合工作树提交、删除同步 stash、把机器检查冒充原文语义核对。",
        "- **Provides**：独立 JSON manifest、UTF-8 CSV 复核队列、高风险源表 JSON、表级覆盖检查和接受记录哈希校验。",
        "- **AcceptanceChecks**：369 张表恰好覆盖一次；无文档跨批；每批 20–40 张；已接受集合的源文档哈希未漂移；仅高风险源表保持人工核对状态。",
        "",
        "## 当前结果",
        "",
        f"- 阶段状态：`{summary['stage7_status']}`。",
        f"- 批次数：{summary['batch_count']}。",
        f"- 正文表覆盖：{summary['unique_table_count']}/{summary['expected_table_count']}。",
        f"- 文档覆盖：{summary['document_count']}，跨批重复文档：{summary['duplicate_document_count']}。",
        f"- 用户已接受：{summary['accepted_table_count']}；既有 PDF 证据已闭合：{summary['source_verified_table_count']}；高风险原文复核已闭合：{summary['high_risk_reviewed_table_count']}；按策略关闭：{summary['policy_closed_table_count']}；高风险源表待核：{summary['high_risk_review_table_count']}。",
        f"- 批次大小范围：{summary['minimum_batch_size']}–{summary['maximum_batch_size']} 张表。",
        "- 当前工作树混有既有转换与用户改动，因此 manifest 的哈希检查点用于检测漂移；在形成独立提交前，不宣称已经具备可直接 `git revert` 的批次回滚点。",
        "",
        "## 批次",
        "",
    ]
    for batch in summary["batches"]:
        features = ", ".join(f"{name}={count}" for name, count in batch["feature_counts"].items() if count)
        lines.append(
            f"- `{batch['batch_id']}`：{batch['table_count']} 张表，{batch['document_count']} 个文档，"
            f"已接受 {batch['accepted_table_count']}，PDF 证据闭合 {batch['source_verified_table_count']}，"
            f"高风险复核闭合 {batch['high_risk_reviewed_table_count']}，策略关闭 {batch['policy_closed_table_count']}，"
            f"高风险待核 {batch['high_risk_review_table_count']}；{features}。"
        )
    lines.extend(
        [
            "",
            "## 门禁解释",
            "",
            "用户已确认代表性四格式产物样例通过后不再逐批审核分发产物。普通表在全量 canonical、结构回归、站点 DOM 机器 `PASS` 和代表性产物试点基础上按策略关闭；PDF 已直接对照修正的表另列为来源证据闭合。只有嵌套、纵向合并、超宽或大表且页码映射歧义的源表进入高风险队列，由 Codex 对照原 PDF；仅当证据仍无法消除语义歧义时才请用户裁决。独立提交门仍未关闭，因为现有工作树不是按这些批次形成的干净提交。",
            "",
            "全量状态队列位于 `output/spreadsheet/canonical-table-stage7-review-queue.csv`；高风险源表位于 `docs/engineering/canonical-table-high-risk-review.json`；批次 JSON 与可直接传给导出器的文件清单位于 `docs/engineering/table-rollout-batches/`。",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def generate(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = args.repo_root.resolve()
    inventory_path = (repo_root / args.inventory).resolve()
    registry_path = (repo_root / args.acceptance_registry).resolve()
    policy_path = (repo_root / args.review_policy).resolve()
    high_risk_registry_path = (repo_root / args.high_risk_review_registry).resolve()
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    source_tables = [item for item in inventory["tables"] if item.get("scope") == "source-content"]
    if any(item.get("representation") != "html" or item.get("target_state") != "canonical-html" for item in source_tables):
        raise ValueError("all source-content tables must already be canonical HTML candidates")
    source_by_id = {item["id"]: item for item in source_tables}
    if len(source_by_id) != len(source_tables):
        raise ValueError("duplicate source-content table IDs")
    accepted = load_acceptances(registry_path, source_by_id, repo_root)
    policy, source_verified = load_review_policy(policy_path, source_by_id, repo_root)
    high_risk_reviewed = load_high_risk_reviews(
        high_risk_registry_path, source_by_id, repo_root
    )
    documents = build_documents(source_tables, repo_root)
    batches = partition_documents(documents, args.minimum, args.maximum, args.target)
    baseline_commit = git_head(repo_root)
    inventory_sha256 = sha256_file(inventory_path)

    output_dir = (repo_root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    for pattern in ("stage7-batch-*.json", "stage7-batch-*.txt"):
        for old_manifest in output_dir.glob(pattern):
            old_manifest.unlink()

    manifests: list[dict[str, Any]] = []
    seen_tables: set[str] = set()
    seen_documents: set[str] = set()
    duplicate_documents = 0
    for index, batch_documents in enumerate(batches, start=1):
        batch_id = f"stage7-batch-{index:02d}"
        tables: list[dict[str, Any]] = []
        document_records = []
        for document in batch_documents:
            if document["path"] in seen_documents:
                duplicate_documents += 1
            seen_documents.add(document["path"])
            document_records.append(
                {
                    "path": document["path"],
                    "sha256": document["sha256"],
                    "table_count": document["table_count"],
                }
            )
            for item in document["tables"]:
                item_id = item["id"]
                if item_id in seen_tables:
                    raise ValueError(f"table assigned more than once: {item_id}")
                seen_tables.add(item_id)
                review_status, high_risk, review_set = classify_review_status(
                    item, accepted, source_verified, high_risk_reviewed, policy
                )
                table = {
                    "id": item_id,
                    "path": item["path"],
                    "line": item.get("line"),
                    "rows": item.get("rows"),
                    "columns": item.get("columns"),
                    "risk": item.get("risk"),
                    "feature_tier": TIER_NAMES[table_tier(item)],
                    "span_signature": item.get("span_signature", []),
                    "nested_depth": item.get("nested_depth", 0),
                    "images": item.get("images", []),
                    "source_page_candidates": item.get("source_page_candidates", []),
                    "review_status": review_status,
                    "high_risk_reasons": high_risk,
                }
                if review_status == "accepted_by_user":
                    table["acceptance_set"] = review_set
                elif review_status in {
                    "source_verified_by_pdf_evidence",
                    "source_verified_by_high_risk_review",
                }:
                    table["evidence_set"] = review_set
                tables.append(table)

        accepted_count = sum(table["review_status"] == "accepted_by_user" for table in tables)
        source_verified_count = sum(
            table["review_status"] == "source_verified_by_pdf_evidence" for table in tables
        )
        high_risk_reviewed_count = sum(
            table["review_status"] == "source_verified_by_high_risk_review" for table in tables
        )
        policy_closed_count = sum(
            table["review_status"] == "closed_by_user_review_policy" for table in tables
        )
        high_risk_count = sum(
            table["review_status"] == "high_risk_source_review_required" for table in tables
        )
        source_snapshot = hashlib.sha256(
            "".join(f"{document['path']}\0{document['sha256']}\n" for document in document_records).encode("utf-8")
        ).hexdigest()
        manifest = {
            "schema_version": 1,
            "batch_id": batch_id,
            "baseline_commit": baseline_commit,
            "inventory_sha256": inventory_sha256,
            "source_snapshot_sha256": source_snapshot,
            "table_count": len(tables),
            "document_count": len(document_records),
            "accepted_table_count": accepted_count,
            "source_verified_table_count": source_verified_count,
            "high_risk_reviewed_table_count": high_risk_reviewed_count,
            "policy_closed_table_count": policy_closed_count,
            "high_risk_review_table_count": high_risk_count,
            "pending_table_count": high_risk_count,
            "feature_counts": summarize_features(tables),
            "risk_counts": dict(sorted(Counter(table["risk"] for table in tables).items())),
            "machine_gates": {
                "canonical": "PASS",
                "structure_regression": "PASS",
                "rendered_dom": "PASS",
                "distribution_pilot": "ACCEPTED_BY_USER",
            },
            "semantic_review_status": "pending_high_risk_source_review" if high_risk_count else "closed_by_policy_or_evidence",
            "independent_commit_status": "pending_clean_batch_boundary",
            "rollback_checkpoint": {
                "kind": "baseline_commit_plus_content_hashes",
                "recoverability": "drift_detection_only_until_independent_commit",
                "source_changed_by_generator": False,
            },
            "documents": document_records,
            "tables": tables,
        }
        manifests.append(manifest)
        (output_dir / f"{batch_id}.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (output_dir / f"{batch_id}.txt").write_text(
            "\n".join(document["path"] for document in document_records) + "\n",
            encoding="utf-8",
        )

    expected_ids = set(source_by_id)
    if seen_tables != expected_ids:
        raise ValueError(
            f"batch coverage mismatch: missing={sorted(expected_ids - seen_tables)}, extra={sorted(seen_tables - expected_ids)}"
        )

    batch_summaries = [
        {
            key: manifest[key]
            for key in (
                "batch_id",
                "table_count",
                "document_count",
                "accepted_table_count",
                "source_verified_table_count",
                "high_risk_reviewed_table_count",
                "policy_closed_table_count",
                "high_risk_review_table_count",
                "pending_table_count",
                "feature_counts",
                "risk_counts",
                "semantic_review_status",
                "independent_commit_status",
            )
        }
        for manifest in manifests
    ]
    summary = {
        "schema_version": 1,
        "generated_by": "scripts/generate_table_rollout_batches.py",
        "stage7_status": "IN_PROGRESS",
        "baseline_commit": baseline_commit,
        "inventory_sha256": inventory_sha256,
        "expected_table_count": len(source_tables),
        "unique_table_count": len(seen_tables),
        "document_count": len(seen_documents),
        "duplicate_document_count": duplicate_documents,
        "accepted_table_count": sum(
            table["review_status"] == "accepted_by_user"
            for manifest in manifests
            for table in manifest["tables"]
        ),
        "source_verified_table_count": sum(
            table["review_status"] == "source_verified_by_pdf_evidence"
            for manifest in manifests
            for table in manifest["tables"]
        ),
        "high_risk_reviewed_table_count": sum(
            table["review_status"] == "source_verified_by_high_risk_review"
            for manifest in manifests
            for table in manifest["tables"]
        ),
        "policy_closed_table_count": sum(
            table["review_status"] == "closed_by_user_review_policy"
            for manifest in manifests
            for table in manifest["tables"]
        ),
        "high_risk_review_table_count": sum(
            table["review_status"] == "high_risk_source_review_required"
            for manifest in manifests
            for table in manifest["tables"]
        ),
        "pending_table_count": sum(
            table["review_status"] == "high_risk_source_review_required"
            for manifest in manifests
            for table in manifest["tables"]
        ),
        "batch_count": len(manifests),
        "minimum_batch_size": min(manifest["table_count"] for manifest in manifests),
        "maximum_batch_size": max(manifest["table_count"] for manifest in manifests),
        "batch_size_policy": {"minimum": args.minimum, "maximum": args.maximum, "target": args.target},
        "batches": batch_summaries,
    }
    summary_path = (repo_root / args.summary).resolve()
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_review_queue((repo_root / args.queue).resolve(), manifests)
    write_high_risk_review((repo_root / args.high_risk_review).resolve(), policy, manifests)
    write_summary_markdown((repo_root / args.markdown_summary).resolve(), summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--inventory", type=Path, default=Path("docs/engineering/table-inventory.json"))
    parser.add_argument(
        "--acceptance-registry",
        type=Path,
        default=Path("docs/engineering/canonical-table-acceptance-registry.json"),
    )
    parser.add_argument(
        "--review-policy",
        type=Path,
        default=Path("docs/engineering/canonical-table-review-policy.json"),
    )
    parser.add_argument(
        "--high-risk-review-registry",
        type=Path,
        default=Path("docs/engineering/canonical-table-high-risk-review-registry.json"),
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("docs/engineering/table-rollout-batches")
    )
    parser.add_argument(
        "--summary", type=Path, default=Path("docs/engineering/canonical-table-stage7-batches.json")
    )
    parser.add_argument(
        "--markdown-summary", type=Path, default=Path("docs/engineering/canonical-table-stage7.md")
    )
    parser.add_argument(
        "--queue", type=Path, default=Path("output/spreadsheet/canonical-table-stage7-review-queue.csv")
    )
    parser.add_argument(
        "--high-risk-review",
        type=Path,
        default=Path("docs/engineering/canonical-table-high-risk-review.json"),
    )
    parser.add_argument("--minimum", type=int, default=20)
    parser.add_argument("--maximum", type=int, default=40)
    parser.add_argument("--target", type=int, default=30)
    args = parser.parse_args()
    summary = generate(args)
    print(
        json.dumps(
            {
                "stage7_status": summary["stage7_status"],
                "batch_count": summary["batch_count"],
                "tables": summary["unique_table_count"],
                "accepted": summary["accepted_table_count"],
                "source_verified": summary["source_verified_table_count"],
                "high_risk_reviewed": summary["high_risk_reviewed_table_count"],
                "policy_closed": summary["policy_closed_table_count"],
                "high_risk_review": summary["high_risk_review_table_count"],
                "pending": summary["pending_table_count"],
                "batch_size_range": [summary["minimum_batch_size"], summary["maximum_batch_size"]],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
