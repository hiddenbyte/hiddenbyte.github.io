#!/usr/bin/env python3
"""Post a blog entry to Instagram: a feed photo and a story with a link sticker."""

import base64
import json
import os
import sys
import time
from pathlib import Path

import frontmatter
from instagrapi import Client
from instagrapi.types import StoryLink
from playwright.sync_api import sync_playwright

BASE_URL = "https://mehul.pt"
CONTENT_DIR = Path("content")

FEED_IMG = Path("/tmp/ig_feed.jpg")
STORY_IMG = Path("/tmp/ig_story.jpg")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def resolve_post(post_path: str) -> tuple[Path, str]:
    """Return (markdown_path, post_url) for a path like 'posts/my-slug'."""
    post_path = post_path.strip("/")
    candidates = [
        CONTENT_DIR / f"{post_path}.md",
        CONTENT_DIR / post_path / "index.md",
    ]
    for p in candidates:
        if p.exists():
            return p, f"{BASE_URL}/{post_path}/"
    raise FileNotFoundError(
        f"No markdown file found for '{post_path}'. "
        f"Tried: {[str(c) for c in candidates]}"
    )


def read_post_meta(md_path: Path) -> tuple[str, list[str]]:
    post = frontmatter.load(str(md_path))
    title: str = post.get("title", "")
    tags: list[str] = post.get("tags", [])
    return title, tags


def take_screenshot(url: str, output: Path, width: int, height: int) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(url, wait_until="networkidle", timeout=30_000)
        time.sleep(2)  # let web fonts / lazy images settle
        page.screenshot(
            path=str(output),
            clip={"x": 0, "y": 0, "width": width, "height": height},
            type="jpeg",
        )
        browser.close()
    print(f"  Saved {output} ({width}×{height})")


def build_caption(title: str, url: str, tags: list[str]) -> str:
    lines = [title, "", url]
    if tags:
        hashtags = " ".join(
            f"#{t.replace(' ', '').replace('-', '')}" for t in tags
        )
        lines += ["", hashtags]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Instagram
# ---------------------------------------------------------------------------

def instagram_client() -> Client:
    cl = Client()

    # Restore a cached session when available (avoids login challenges)
    session_b64 = os.environ.get("INSTAGRAM_SESSION_JSON", "")
    if session_b64:
        try:
            session = json.loads(base64.b64decode(session_b64))
            cl.set_settings(session)
            cl.get_timeline_feed()  # probe — raises if session expired
            print("Session restored from INSTAGRAM_SESSION_JSON.")
            return cl
        except Exception as exc:
            print(f"Cached session invalid ({exc}), falling back to login.")

    username = os.environ["INSTAGRAM_USERNAME"]
    password = os.environ["INSTAGRAM_PASSWORD"]
    totp_secret = os.environ.get("INSTAGRAM_TOTP_SECRET", "")

    print(f"Logging in as {username}…")
    if totp_secret:
        cl.login(
            username,
            password,
            verification_code=cl.totp_generate_code(totp_secret),
        )
    else:
        cl.login(username, password)

    return cl


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: instagram_post.py <post_path>", file=sys.stderr)
        sys.exit(1)

    post_path = sys.argv[1]
    md_path, post_url = resolve_post(post_path)
    title, tags = read_post_meta(md_path)

    print(f"Title : {title}")
    print(f"URL   : {post_url}")
    print(f"Tags  : {tags}")

    # --- Screenshots -------------------------------------------------------
    print("\nTaking screenshots…")
    take_screenshot(post_url, FEED_IMG, width=1080, height=1080)   # 1:1 feed
    take_screenshot(post_url, STORY_IMG, width=1080, height=1920)  # 9:16 story

    caption = build_caption(title, post_url, tags)
    print(f"\nCaption:\n{caption}\n")

    # --- Instagram ---------------------------------------------------------
    cl = instagram_client()

    print("Uploading feed post…")
    cl.photo_upload(str(FEED_IMG), caption)

    print("Uploading story with link sticker…")
    cl.photo_upload_to_story(
        str(STORY_IMG),
        links=[StoryLink(webUri=post_url)],
    )

    print("\nDone!")


if __name__ == "__main__":
    main()
