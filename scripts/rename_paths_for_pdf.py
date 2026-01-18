from __future__ import annotations

from pathlib import Path


RENAMES: list[tuple[Path, Path]] = [
    (
        Path("docs/资源目录/课程/古武术总纲.md"),
        Path("docs/资源目录/课程/古武术.md"),
    ),
    (
        Path("docs/资源目录/能力列表/出身经历类.md"),
        Path("docs/资源目录/能力列表/出身类.md"),
    ),
]


def safe_rename(src: Path, dst: Path) -> str:
    if not src.exists():
        return f"missing: {src.as_posix()}"
    if dst.exists():
        return f"exists: {dst.as_posix()}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    return f"renamed: {src.as_posix()} -> {dst.as_posix()}"


def replace_in_file(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    if old not in text:
        return
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> None:
    logs: list[str] = []
    for src, dst in RENAMES:
        logs.append(safe_rename(src, dst))

    # Update known checklist references (best-effort)
    checklist = Path("docs/表格重建清单.md")
    if checklist.exists():
        replace_in_file(
            checklist,
            "`docs/资源目录/能力列表/出身经历类.md`",
            "`docs/资源目录/能力列表/出身类.md`",
        )
        replace_in_file(
            checklist,
            "`docs/资源目录/课程/古武术总纲.md`",
            "`docs/资源目录/课程/古武术.md`",
        )

    Path("output_rename_log.txt").write_text("\n".join(logs) + "\n", encoding="utf-8")
    print("wrote output_rename_log.txt")


if __name__ == "__main__":
    main()

