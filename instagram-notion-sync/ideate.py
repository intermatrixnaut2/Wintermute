#!/usr/bin/env python3
"""
Instagram Saves → Content Ideas pipeline.

Reads unprocessed saves from the Notion Instagram Saves database,
calls Claude to generate content ideas for each one, presents them
for review, then saves approved ideas to the Content Ideas database
and marks the original saves as processed.

Usage:
    python ideate.py              # process all unprocessed saves
    python ideate.py --limit 5   # process at most 5 saves
    python ideate.py --dry-run   # print ideas without saving
"""

import argparse
import os
import textwrap
from datetime import datetime, timezone

import anthropic
from notion_client import Client

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_SAVES_DB_ID = os.environ["NOTION_SAVES_DB_ID"]
NOTION_IDEAS_DB_ID = os.environ["NOTION_IDEAS_DB_ID"]
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

CLAUDE_MODEL = "claude-sonnet-4-6"

# ---------------------------------------------------------------------------
# Notion helpers
# ---------------------------------------------------------------------------


def _fetch_unprocessed_saves(notion: Client, limit: int | None = None) -> list[dict]:
    """Return Notion page objects for unprocessed saves."""
    pages: list[dict] = []
    cursor = None

    while True:
        kwargs: dict = {
            "database_id": NOTION_SAVES_DB_ID,
            "filter": {"property": "Processed", "checkbox": {"equals": False}},
            "sorts": [{"property": "Synced At", "direction": "ascending"}],
            "page_size": 100,
        }
        if cursor:
            kwargs["start_cursor"] = cursor

        resp = notion.databases.query(**kwargs)
        pages.extend(resp.get("results", []))

        if limit and len(pages) >= limit:
            pages = pages[:limit]
            break

        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")

    return pages


def _prop_text(page: dict, prop_name: str) -> str:
    """Extract plain text from a Notion rich_text or title property."""
    prop = page.get("properties", {}).get(prop_name, {})
    kind = prop.get("type")
    if kind in ("rich_text", "title"):
        parts = prop.get(kind, [])
        return "".join(p.get("plain_text", "") for p in parts)
    if kind == "url":
        return prop.get("url") or ""
    if kind == "select":
        sel = prop.get("select")
        return sel.get("name", "") if sel else ""
    return ""


def _extract_save_data(page: dict) -> dict:
    return {
        "id": page["id"],
        "author": _prop_text(page, "Author"),
        "caption": _prop_text(page, "Caption"),
        "url": _prop_text(page, "URL"),
        "content_type": _prop_text(page, "Content Type"),
        "collection": _prop_text(page, "Collection"),
    }


def _mark_processed(notion: Client, page_id: str) -> None:
    notion.pages.update(
        page_id=page_id,
        properties={"Processed": {"checkbox": True}},
    )


def _save_idea(notion: Client, idea: dict, source_save: dict) -> None:
    """Create a page in the Content Ideas database."""
    now = datetime.now(timezone.utc).isoformat()
    title = idea["hook_variations"][0][:255]

    notion.pages.create(
        parent={"database_id": NOTION_IDEAS_DB_ID},
        properties={
            "Name": {"title": [{"text": {"content": title}}]},
            "Source URL": {"url": source_save["url"] or None},
            "Original Author": {
                "rich_text": [{"text": {"content": source_save["author"]}}]
            },
            "Content Type": {"select": {"name": source_save["content_type"]}},
            "Hook Variations": {
                "rich_text": [
                    {
                        "text": {
                            "content": _truncate(
                                "\n".join(
                                    f"{i+1}. {h}"
                                    for i, h in enumerate(idea["hook_variations"])
                                )
                            )
                        }
                    }
                ]
            },
            "Outline": {
                "rich_text": [{"text": {"content": _truncate(idea["outline"])}}]
            },
            "Instagram": {
                "rich_text": [{"text": {"content": _truncate(idea["instagram"])}}]
            },
            "TikTok": {
                "rich_text": [{"text": {"content": _truncate(idea["tiktok"])}}]
            },
            "YouTube": {
                "rich_text": [{"text": {"content": _truncate(idea["youtube"])}}]
            },
            "Status": {"select": {"name": "Draft"}},
            "Created At": {"date": {"start": now}},
        },
    )


def _truncate(text: str, limit: int = 2000) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


# ---------------------------------------------------------------------------
# Claude ideation
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a content strategist specializing in AI and solo founder content.
Your audience is beginner AI solo founders — people who are just starting
to build products or businesses using AI tools, often without a technical
background. They follow creators for practical tips, inspiration, and
frameworks they can act on immediately.

When given an Instagram save (author, caption, content type, collection),
you reframe the core idea for this audience and generate a structured
content brief in JSON.

Return ONLY valid JSON with this schema:
{
  "hook_variations": ["hook 1", "hook 2", "hook 3"],
  "outline": "Hook: ...\\n\\nKey Points:\\n1. ...\\n2. ...\\n3. ...\\n\\nCTA: ...",
  "instagram": "...",
  "tiktok": "...",
  "youtube": "..."
}

hook_variations: 3 distinct hooks (curiosity, contrarian, how-to style).
outline: Hook → 3-5 key points → CTA, written as a structured brief.
instagram: carousel or Reel concept (slides/scenes, caption opener, hashtag strategy).
tiktok: short-form video concept (hook seconds 0-3, structure, trend angle).
youtube: long-form or Shorts concept (title, thumbnail idea, chapter outline).

Keep all text tight and actionable. No filler. No placeholder phrases like
"your audience" — write for beginner AI solo founders specifically.
"""


def _build_user_prompt(save: dict) -> str:
    return textwrap.dedent(f"""
        Instagram save to ideate on:

        Author: {save['author']}
        Content type: {save['content_type']}
        Collection: {save['collection']}
        URL: {save['url']}

        Caption:
        {save['caption'] or '(no caption)'}

        Generate a content brief reframing this for beginner AI solo founders.
    """).strip()


def generate_ideas(client: anthropic.Anthropic, save: dict) -> dict | None:
    """Call Claude and parse the JSON response. Returns None on failure."""
    import json as _json

    try:
        resp = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1500,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_user_prompt(save)}],
        )
        raw = resp.content[0].text.strip()

        # Strip markdown code fences if Claude wraps the JSON
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(
                l for l in lines if not l.startswith("```")
            ).strip()

        return _json.loads(raw)
    except Exception as exc:
        print(f"  [Claude error] {exc}")
        return None


# ---------------------------------------------------------------------------
# Interactive review
# ---------------------------------------------------------------------------

_DIVIDER = "─" * 70


def _print_idea(save: dict, idea: dict) -> None:
    print(f"\n{_DIVIDER}")
    print(f"SOURCE: {save['author']} ({save['content_type']}) | {save['collection']}")
    print(f"URL:    {save['url']}")
    print(f"\nCAPTION (excerpt):\n{save['caption'][:300]}{'...' if len(save['caption']) > 300 else ''}")
    print(f"\n{'═' * 70}")
    print("HOOKS:")
    for i, h in enumerate(idea["hook_variations"], 1):
        print(f"  {i}. {h}")
    print(f"\nOUTLINE:\n{textwrap.indent(idea['outline'], '  ')}")
    print(f"\nINSTAGRAM:\n{textwrap.indent(idea['instagram'], '  ')}")
    print(f"\nTIKTOK:\n{textwrap.indent(idea['tiktok'], '  ')}")
    print(f"\nYOUTUBE:\n{textwrap.indent(idea['youtube'], '  ')}")
    print()


def _prompt_review() -> str:
    """Return 'approve', 'skip', or 'quit'."""
    while True:
        choice = input("  [a]pprove  [s]kip  [q]uit  → ").strip().lower()
        if choice in ("a", "approve"):
            return "approve"
        if choice in ("s", "skip"):
            return "skip"
        if choice in ("q", "quit"):
            return "quit"
        print("  Please enter a, s, or q.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Ideate content from Instagram saves")
    parser.add_argument("--limit", type=int, default=None, help="Max saves to process")
    parser.add_argument("--dry-run", action="store_true", help="Print ideas without saving")
    args = parser.parse_args()

    notion = Client(auth=NOTION_TOKEN)
    claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    print("Fetching unprocessed saves from Notion...")
    pages = _fetch_unprocessed_saves(notion, limit=args.limit)
    print(f"Found {len(pages)} unprocessed save(s).\n")

    if not pages:
        print("Nothing to process. Exiting.")
        return

    approved = 0
    skipped = 0

    for page in pages:
        save = _extract_save_data(page)
        print(f"\nGenerating ideas for: {save['author']} — {save['content_type']}...")

        idea = generate_ideas(claude, save)
        if idea is None:
            print("  Skipping (Claude call failed).")
            skipped += 1
            continue

        _print_idea(save, idea)

        if args.dry_run:
            print("  [dry-run] Skipping save.")
            continue

        decision = _prompt_review()

        if decision == "quit":
            print("\nExiting early.")
            break
        if decision == "skip":
            skipped += 1
            continue

        # Approve: save idea + mark processed
        try:
            _save_idea(notion, idea, save)
            _mark_processed(notion, save["id"])
            approved += 1
            print("  ✓ Saved to Content Ideas and marked processed.")
        except Exception as exc:
            print(f"  ! Notion save failed: {exc}")

    print(f"\nDone — approved: {approved}, skipped: {skipped}")


if __name__ == "__main__":
    main()
