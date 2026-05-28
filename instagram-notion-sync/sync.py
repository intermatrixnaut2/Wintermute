#!/usr/bin/env python3
"""
Instagram Saves → Notion sync.

Reads config.json from the same directory, fetches saved posts from the
Instagram web API, and writes new ones to a Notion database.
state.json tracks already-synced media IDs to prevent duplicates.
"""

import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from notion_client import Client

# ---------------------------------------------------------------------------
# Paths & logging
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
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
# Config
# ---------------------------------------------------------------------------


def _load_config() -> dict:
    if not CONFIG_FILE.exists():
        log.error(f"config.json not found at {CONFIG_FILE}")
        sys.exit(1)
    return json.loads(CONFIG_FILE.read_text())


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


def _load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"synced_ids": []}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ---------------------------------------------------------------------------
# Instagram HTTP helpers
# ---------------------------------------------------------------------------


def _make_session(cfg: dict) -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "user-agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "x-ig-app-id": "936619743392459",
            "x-csrftoken": cfg["ig_csrftoken"],
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "referer": "https://www.instagram.com/",
            "x-requested-with": "XMLHttpRequest",
        }
    )
    s.cookies.update(
        {
            "sessionid": cfg["ig_session_id"],
            "csrftoken": cfg["ig_csrftoken"],
            "ds_user_id": cfg["ig_user_id"],
        }
    )
    return s


def _validate_session(session: requests.Session) -> None:
    try:
        resp = session.get(
            "https://www.instagram.com/api/v1/accounts/edit/web_form_data/",
            timeout=30,
        )
        if resp.status_code in (401, 403):
            log.error(
                "Instagram session is invalid or expired. "
                "Refresh your cookies (sessionid, csrftoken, ds_user_id) and update config.json."
            )
            sys.exit(1)
        resp.raise_for_status()
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code in (401, 403):
            log.error(
                "Instagram session is invalid or expired. "
                "Refresh your cookies (sessionid, csrftoken, ds_user_id) and update config.json."
            )
            sys.exit(1)
        raise


# ---------------------------------------------------------------------------
# Type detection
# ---------------------------------------------------------------------------

# media_type → base label (product_type can override for video)
_MEDIA_TYPE_BASE = {1: "Post", 2: "Reel", 8: "Carousel"}


def _detect_type(media: dict) -> str:
    media_type = media.get("media_type", 1)
    product_type = (media.get("product_type") or "").lower()
    if media_type == 2:
        if product_type == "igtv":
            return "IGTV"
        return "Reel"
    return _MEDIA_TYPE_BASE.get(media_type, "Post")


# ---------------------------------------------------------------------------
# Instagram fetchers
# ---------------------------------------------------------------------------


def _fetch_collections(session: requests.Session) -> list[dict]:
    resp = session.get(
        "https://www.instagram.com/api/v1/collections/list/",
        params={
            "collection_types": '["ALL_MEDIA_AUTO_COLLECTION","PRODUCT_AUTO_COLLECTION","MEDIA"]'
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("items", [])


def _fetch_collection_media(session: requests.Session, collection_id: str) -> list[dict]:
    items: list[dict] = []
    next_max_id: str | None = None
    while True:
        params: dict = {"count": 50}
        if next_max_id:
            params["max_id"] = next_max_id
        resp = session.get(
            f"https://www.instagram.com/api/v1/feed/collection/{collection_id}/",
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        items.extend(data.get("items", []))
        next_max_id = data.get("next_max_id")
        if not next_max_id:
            break
        time.sleep(1.0)
    return items


def _fetch_saved_posts(session: requests.Session) -> list[dict]:
    items: list[dict] = []
    next_max_id: str | None = None
    while True:
        params: dict = {"count": 50}
        if next_max_id:
            params["next_max_id"] = next_max_id
        resp = session.get(
            "https://www.instagram.com/api/v1/feed/saved/posts/",
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        items.extend(data.get("items", []))
        next_max_id = data.get("next_max_id")
        if not next_max_id:
            break
        time.sleep(1.0)
    return items


def fetch_all_saves(
    session: requests.Session, collections_filter: list[str] | None
) -> list[tuple[dict, str | None]]:
    """
    Returns (media, collection_name_or_None) tuples, deduplicated by media pk.
    If collections_filter is set, only items from matching collections are returned.
    """
    result: list[tuple[dict, str | None]] = []
    seen_ids: set[str] = set()

    def _add(media: dict, col_name: str | None) -> None:
        mid = str(media.get("pk") or media.get("id", ""))
        if mid and mid not in seen_ids:
            seen_ids.add(mid)
            result.append((media, col_name))

    log.info("Fetching collections...")
    try:
        collections = _fetch_collections(session)
        log.info(f"  Found {len(collections)} collections")
    except Exception as exc:
        log.warning(f"  Could not fetch collections: {exc}")
        collections = []

    for col in collections:
        col_name = col.get("collection_name") or ""
        if collections_filter and col_name not in collections_filter:
            log.info(f"  Skipping collection '{col_name}' (not in filter)")
            continue
        col_id = col.get("collection_id", "")
        log.info(f"  Fetching collection '{col_name}' ({col_id})")
        try:
            for item in _fetch_collection_media(session, col_id):
                _add(item.get("media", item), col_name)
        except Exception as exc:
            log.warning(f"  Failed to fetch '{col_name}': {exc}")
        time.sleep(0.5)

    if not collections_filter:
        log.info("Fetching general saved posts feed...")
        try:
            for item in _fetch_saved_posts(session):
                _add(item.get("media", item), None)
        except Exception as exc:
            log.warning(f"  Saved feed error: {exc}")

    log.info(f"Total unique saves fetched: {len(result)}")
    return result


# ---------------------------------------------------------------------------
# Notion property builder
# ---------------------------------------------------------------------------


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _build_props(media: dict, collection_name: str | None) -> dict:
    content_type = _detect_type(media)
    shortcode = media.get("code", "")
    username = (media.get("user") or {}).get("username", "unknown")
    caption_raw = ((media.get("caption") or {}).get("text") or "")
    media_id = str(media.get("pk") or media.get("id", ""))
    now = datetime.now(timezone.utc).isoformat()

    url = (
        f"https://www.instagram.com/reel/{shortcode}/"
        if content_type == "Reel"
        else f"https://www.instagram.com/p/{shortcode}/"
    )

    props: dict = {
        "Name": {"title": [{"text": {"content": _truncate(f"@{username}/{shortcode}", 255)}}]},
        "URL": {"url": url},
        "Type": {"select": {"name": content_type}},
        "Author": {"rich_text": [{"text": {"content": f"@{username}"}}]},
        "Status": {"select": {"name": "New"}},
        "Media ID": {"rich_text": [{"text": {"content": media_id}}]},
        "Saved": {"date": {"start": now}},
        "Caption": {"rich_text": [{"text": {"content": _truncate(caption_raw, 1900)}}]},
    }

    if collection_name:
        props["Collection"] = {"select": {"name": collection_name}}

    return props


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def sync() -> None:
    cfg = _load_config()
    collections_filter: list[str] | None = cfg.get("collections_filter") or None

    session = _make_session(cfg)

    log.info("Validating Instagram session...")
    _validate_session(session)
    log.info("Session valid.")

    state = _load_state()
    synced_ids: set[str] = set(state["synced_ids"])

    notion = Client(auth=cfg["notion_token"])

    saves = fetch_all_saves(session, collections_filter)

    new_count = 0
    skipped_count = 0
    error_count = 0
    total = len(saves)

    for media, col_name in saves:
        media_id = str(media.get("pk") or media.get("id", ""))
        if not media_id:
            skipped_count += 1
            continue
        if media_id in synced_ids:
            skipped_count += 1
            continue

        try:
            props = _build_props(media, col_name)
            notion.pages.create(
                parent={"database_id": cfg["notion_database_id"]},
                properties=props,
            )
            synced_ids.add(media_id)
            state["synced_ids"] = list(synced_ids)
            _save_state(state)
            new_count += 1
            log.info(f"  + {props['Name']['title'][0]['text']['content']}")
            time.sleep(0.35)
        except Exception as exc:
            error_count += 1
            log.error(f"  ! Failed {media_id}: {exc}")

    log.info(
        f"Sync complete: {new_count} new | {skipped_count} skipped"
        f" | {total} total | {error_count} errors"
    )


if __name__ == "__main__":
    sync()
