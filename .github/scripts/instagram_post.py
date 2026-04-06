#!/usr/bin/env python3
"""Post a blog entry to Instagram via the official Graph API.

Feed post  — screenshot (1080×1080) + title / URL / hashtags caption.
Story      — screenshot (1080×1920) + link sticker pointing to the post URL.

Required environment variables:
    INSTAGRAM_USER_ID       Numeric IG user ID.
    INSTAGRAM_ACCESS_TOKEN  Long-lived OAuth access token (expires in 60 days).
    CLOUDINARY_URL          cloudinary://API_KEY:API_SECRET@CLOUD_NAME
                            Used to host screenshots so the Graph API can fetch them.
"""

import os
import sys
import time
from pathlib import Path

import cloudinary
import cloudinary.uploader
import frontmatter
import requests
from playwright.sync_api import sync_playwright

BASE_URL = "https://mehul.pt"
CONTENT_DIR = Path("content")
GRAPH_URL = "https://graph.instagram.com/v21.0"

FEED_IMG = Path("/tmp/ig_feed.jpg")
STORY_IMG = Path("/tmp/ig_story.jpg")


# ---------------------------------------------------------------------------
# Blog helpers
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
    return post.get("title", ""), post.get("tags", [])


def build_caption(title: str, url: str, tags: list[str]) -> str:
    lines = [title, "", url]
    if tags:
        hashtags = " ".join(
            f"#{t.replace(' ', '').replace('-', '')}" for t in tags
        )
        lines += ["", hashtags]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Screenshots
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Cloudinary — host screenshots so the Graph API can fetch them
# ---------------------------------------------------------------------------

def upload_to_cloudinary(path: Path) -> str:
    """Upload an image and return its public HTTPS URL."""
    # CLOUDINARY_URL env var is picked up automatically by the SDK
    result = cloudinary.uploader.upload(
        str(path),
        resource_type="image",
        overwrite=True,
        public_id=f"blog-ig/{path.stem}",
    )
    return result["secure_url"]


# ---------------------------------------------------------------------------
# Instagram Graph API
# ---------------------------------------------------------------------------

def _post(endpoint: str, **data) -> dict:
    token = os.environ["INSTAGRAM_ACCESS_TOKEN"]
    resp = requests.post(
        f"{GRAPH_URL}/{endpoint}",
        data={**data, "access_token": token},
        timeout=30,
    )
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise RuntimeError(f"Graph API error: {resp.text}") from None
    return resp.json()


def create_feed_container(user_id: str, image_url: str, caption: str) -> str:
    data = _post(f"{user_id}/media", image_url=image_url, caption=caption)
    return data["id"]


def create_story_container(user_id: str, image_url: str, link_url: str) -> str:
    data = _post(
        f"{user_id}/media",
        media_type="STORIES",
        image_url=image_url,
        link_sticker=f'{{"link_url":"{link_url}"}}',
    )
    return data["id"]


def publish_container(user_id: str, container_id: str) -> str:
    # Instagram requires a short delay between container creation and publishing
    time.sleep(5)
    data = _post(f"{user_id}/media_publish", creation_id=container_id)
    return data["id"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: instagram_post.py <post_path>", file=sys.stderr)
        sys.exit(1)

    user_id = os.environ["INSTAGRAM_USER_ID"]
    post_path = sys.argv[1]
    md_path, post_url = resolve_post(post_path)
    title, tags = read_post_meta(md_path)

    print(f"Title : {title}")
    print(f"URL   : {post_url}")
    print(f"Tags  : {tags}")

    # Screenshots
    print("\nTaking screenshots…")
    take_screenshot(post_url, FEED_IMG, width=1080, height=1080)
    take_screenshot(post_url, STORY_IMG, width=1080, height=1920)

    # Upload to Cloudinary to get public URLs for the Graph API
    print("\nUploading to Cloudinary…")
    feed_url = upload_to_cloudinary(FEED_IMG)
    story_url = upload_to_cloudinary(STORY_IMG)
    print(f"  Feed  : {feed_url}")
    print(f"  Story : {story_url}")

    caption = build_caption(title, post_url, tags)
    print(f"\nCaption:\n{caption}\n")

    # Post via Graph API
    print("Creating feed media container…")
    feed_container = create_feed_container(user_id, feed_url, caption)

    print("Creating story media container…")
    story_container = create_story_container(user_id, story_url, post_url)

    print("Publishing feed post…")
    feed_id = publish_container(user_id, feed_container)
    print(f"  Published feed post: {feed_id}")

    print("Publishing story…")
    story_id = publish_container(user_id, story_container)
    print(f"  Published story: {story_id}")

    print("\nDone!")


if __name__ == "__main__":
    main()
