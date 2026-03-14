from __future__ import annotations

import re
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = REPO_ROOT / "site"
ASSETS_SRC = REPO_ROOT / "assets"
ASSETS_DST = SITE_DIR / "assets"
HOME_PAGE = SITE_DIR / "PM_TRPG.html"
INDEX_PAGE = SITE_DIR / "index.html"
ASSET_PATH_RE = re.compile(r"(?P<path>(?:\.\./)+assets/)")


def _rewrite_asset_links(text: str) -> str:
    # Markdown files are one level deeper than their rendered HTML because the
    # `docs/` root disappears from the output tree, so asset links need one
    # fewer `../` segment when published.
    return ASSET_PATH_RE.sub(lambda m: m.group("path")[3:], text)


def on_page_markdown(markdown, *args, **kwargs):  # type: ignore[no-untyped-def]
    return _rewrite_asset_links(markdown)


def on_post_build(*args, **kwargs):  # type: ignore[no-untyped-def]
    if ASSETS_DST.exists():
        shutil.rmtree(ASSETS_DST)

    # Keep the site self-contained without mutating the repository assets.
    shutil.copytree(ASSETS_SRC, ASSETS_DST)
    print(f"[mkdocs_hooks] copied assets -> {ASSETS_DST}")

    # GitHub Pages root URLs require an index.html entry point.
    if HOME_PAGE.exists():
        shutil.copy2(HOME_PAGE, INDEX_PAGE)
        print(f"[mkdocs_hooks] created homepage alias -> {INDEX_PAGE}")

    return None
