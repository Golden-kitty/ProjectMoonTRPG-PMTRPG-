from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, cwd=REPO_ROOT, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "build"
    if mode not in {"build", "serve"}:
        raise SystemExit("Usage: python scripts/build_site.py [build|serve]")

    run([sys.executable, "scripts/generate_mkdocs_config.py"])
    if mode == "build":
        run([sys.executable, "-m", "mkdocs", "build", "--strict"])
    else:
        run([sys.executable, "-m", "mkdocs", "serve"])


if __name__ == "__main__":
    main()
