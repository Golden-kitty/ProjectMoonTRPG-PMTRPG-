from __future__ import annotations

import re
import shutil
from pathlib import Path

from scripts.site_content import adapt_site_content

REPO_ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = REPO_ROOT / "site"
ASSETS_SRC = REPO_ROOT / "assets"
ASSET_PATH_RE = re.compile(r"(?P<path>(?:\.\./)+assets/)")


def _rewrite_asset_links(text: str) -> str:
    # Markdown files are one level deeper than their rendered HTML because the
    # `docs/` root disappears from the output tree, so asset links need one
    # fewer `../` segment when published.
    return ASSET_PATH_RE.sub(lambda m: m.group("path")[3:], text)


def on_page_markdown(markdown, *args, **kwargs):  # type: ignore[no-untyped-def]
    return _rewrite_asset_links(markdown)


def on_page_content(html, page, **kwargs):  # type: ignore[no-untyped-def]
    # Apply presentation only after Markdown has generated its stable links and IDs.
    return adapt_site_content(html, page.file.src_uri)


def on_post_build(*args, **kwargs):  # type: ignore[no-untyped-def]
    config = kwargs.get("config")
    site_dir = Path(config["site_dir"]) if config is not None else SITE_DIR
    assets_dst = site_dir / "assets"
    # Merge repository assets into the theme output. Material also writes its
    # stylesheets, scripts, and icons under site/assets, so replacing the whole
    # directory would silently remove the theme and leave the HTML unstyled.
    # These manifests are build-time evidence, not assets requested by readers.
    shutil.copytree(
        ASSETS_SRC, assets_dst, dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("presentation-v184.json", "semantic-presentation.json"),
    )
    print(f"[mkdocs_hooks] copied assets -> {assets_dst}")

    # GitHub Pages root URLs require an index.html entry point.
    home_page = site_dir / "PM_TRPG.html"
    index_page = site_dir / "index.html"
    if home_page.exists():
        shutil.copy2(home_page, index_page)
        print(f"[mkdocs_hooks] created homepage alias -> {index_page}")

    return None
