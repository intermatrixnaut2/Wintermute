#!/usr/bin/env python3
"""
Instagram Saves → Notion sync script.

Reads saved posts (and collections) from Instagram's private web API using
browser session cookies, then syncs new ones into a Notion database.
A state.json file tracks already-synced post IDs to prevent duplicates.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from notion_client import Client

# ---------------------------------------------------------------------------
# Paths & logging
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
STATE_FILE = SCRIPT_DIR / "state.json"
LOG_FILE = SCRIPT_DIR / "sync.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config — all values come from environment variables
# ---------------------------------------------------------------------------

IG_SESSION_ID = os.environ["IG_SESSION_ID"]
IG_CSRF_TOKEN = os.environ["IG_CSRF_TOKEN"]
IG_DS_USER_ID = os.environ["IG_DS_USER_ID"]
NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_SAVES_DB_ID = os.environ["NOTION_SAVES_DB_ID"]

# ---------------------------------------------------------------------------
# Instagram HTTP helpers
# ---------------------------------------------------------------------------

_IG_HEADERS = {
    "x-csrftoken": IG_CSRF_TOKEN,
    "x-ig-app-id": "936619743392459",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "referer": "https://www.instagram.com/",
    "x-requested-with": "XMLHttpRequest",
}

_IG_COOKIES = {
    "sessionid": IG_SESSION_ID,
    "csrftoken": IG_CSRF_TOKEN,
    "ds_user_id": IG_DS_USER_ID,
}

MEDIA_TYPE_MAP = {1: "Post", 2: "Reel", 8: "Carousel"}


def _ig_get(url: str, params: dict | None = None) -> dict:
    resp = requests.get(
        url,
        headers=_IG_HEADERS,
        cookies=_IG_COOKIES,
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------


def _load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"synced_ids": [], "last_sync": None}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ---------------------------------------------------------------------------
# Instagram fetchers
# ---------------------------------------------------------------------------


def _fetch_collections() -> list[dict]:
    """Return the user's named Instagram collections."""
    data = _ig_get(
        "https://www.instagram.com/api/v1/collections/list/",
        params={"collection_types": '["ALL"]'},
    )
    return data.get("items", [])


def _fetch_collection_media(collection_id: str) -> list[dict]:
    """Paginate through all media in a collection."""
    items: list[dict] = []
    next_max_id: str | None = None

    while True:
        params: dict = {"count": 50}
        if next_max_id:
            params["max_id"] = next_max_id

        data = _ig_get(
            f"https://www.instagram.com/api/v1/feed/collection/{collection_id}/",
            params=params,
        )
        items.extend(data.get("items", []))
        next_max_id = data.get("next_max_id")
        if not next_max_id:
            break
        time.sleep(1.0)

    return items


def fetch_all_saves() -> list[tuple[dict, str]]:
    """
    Returns a deduplicated list of (media_item, collection_name) tuples.
    Collection media is fetched first; then the general "All Posts" feed
    catches anything not in a named collection.
    """
    result: list[tuple[dict, str]] = []
    seen_ids: set[str] = set()

    def _add(media: dict, collection_name: str) -> None:
        mid = str(media.get("pk") or media.get("id", ""))
        if mid and mid not in seen_ids:
            seen_ids.add(mid)
            result.append((media, collection_name))

    # Named collections
    log.info("Fetching collections...")
    try:
        collections = _fetch_collections()
        log.info(f"Found {len(collections)} collections")
    except Exception as exc:
        log.warning(f"Could not fetch collections: {exc}")
        collections = []

    for col in collections:
        col_id = col.get("collection_id", "")
        col_name = col.get("collection_name") or "All Posts"
        log.info(f"  Fetching collection '{col_name}' ({col_id})")
        try:
            for item in _fetch_collection_media(col_id):
                media = item.get("media", item)
                _add(media, col_name)
        except Exception as exc:
            log.warning(f"  Failed to fetch collection '{col_name}': {exc}")
        time.sleep(0.5)

    # General saved posts feed — catches items not in named collections
    log.info("Fetching general saved posts feed...")
    next_max_id: str | None = None
    while True:
        params: dict = {"count": 50}
        if next_max_id:
            params["max_id"] = next_max_id
        try:
            data = _ig_get(
                "https://www.instagram.com/api/v1/feed/saved/posts/",
                params=params,
            )
            for item in data.get("items", []):
                media = item.get("media", item)
                _add(media, "All Posts")
            next_max_id = data.get("next_max_id")
            if not next_max_id:
                break
            time.sleep(1.0)
        except Exception as exc:
            log.warning(f"Stopped paginating saved feed: {exc}")
            break

    log.info(f"Total unique saves found: {len(result)}")
    return result


# ---------------------------------------------------------------------------
# Notion helpers
# ---------------------------------------------------------------------------


def _truncate(text: str, limit: int = 2000) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _media_to_notion_props(media: dict, collection_name: str) -> dict:
    media_type_id = media.get("media_type", 1)
    content_type = MEDIA_TYPE_MAP.get(media_type_id, "Post")
    shortcode = media.get("code", "")

    if content_type == "Reel":
        url = f"https://www.instagram.com/reel/{shortcode}/"
    else:
        url = f"https://www.instagram.com/p/{shortcode}/"

    username = media.get("user", {}).get("username", "unknown")
    caption = _truncate((media.get("caption") or {}).get("text", ""))
    post_id = str(media.get("pk") or media.get("id", ""))
    title = _truncate(f"@{username} — {content_type}", 255)
    now = datetime.now(timezone.utc).isoformat()

    return {
        "Name": {"title": [{"text": {"content": title}}]},
        "Author": {"rich_text": [{"text": {"content": f"@{username}"}}]},
        "Caption": {"rich_text": [{"text": {"content": caption}}]},
        "URL": {"url": url or None},
        "Content Type": {"select": {"name": content_type}},
        "Collection": {"select": {"name": collection_name}},
        "Post ID": {"rich_text": [{"text": {"content": post_id}}]},
        "Processed": {"checkbox": False},
        "Synced At": {"date": {"start": now}},
    }


# ---------------------------------------------------------------------------
# Main sync
# ---------------------------------------------------------------------------


def sync() -> None:
    state = _load_state()
    synced_ids: set[str] = set(state["synced_ids"])

    notion = Client(auth=NOTION_TOKEN)

    saves = fetch_all_saves()
    new_count = 0
    error_count = 0

    for media, collection_name in saves:
        post_id = str(media.get("pk") or media.get("id", ""))
        if not post_id or post_id in synced_ids:
            continue

        try:
            props = _media_to_notion_props(media, collection_name)
            notion.pages.create(
                parent={"database_id": NOTION_SAVES_DB_ID},
                properties=props,
            )
            synced_ids.add(post_id)
            new_count += 1
            log.info(f"  + Synced: {props['Name']['title'][0]['text']['content']}")
            time.sleep(0.35)  # stay well within Notion's 3 req/s limit
        except Exception as exc:
            error_count += 1
            log.error(f"  ! Failed to sync post {post_id}: {exc}")

    state["synced_ids"] = list(synced_ids)
    state["last_sync"] = datetime.now(timezone.utc).isoformat()
    _save_state(state)

    log.info(f"Sync complete — new: {new_count}, errors: {error_count}")


if __name__ == "__main__":
    sync()
