# Instagram Saves → Notion Sync

Zero-friction pipeline: save something on Instagram → it automatically syncs into
Notion twice a day → on demand, Claude turns saves into content briefs.

## Architecture

```
Instagram (browser session) ──► sync.py ──► Notion: Instagram Saves DB
                                                        │
                                                   /ideate  (Claude Code)
                                                        │
                                              Notion: Content Ideas DB
```

## Setup

### 1. Prerequisites

- Python 3.11+
- A Notion integration with access to both databases (see below)
- An Anthropic API key (for `ideate.py` / `/ideate`)

### 2. Notion databases

Create two databases in Notion and share them with your integration.

**Instagram Saves** (used by `sync.py` and `/ideate`):

| Property | Type |
|---|---|
| Name | Title |
| Author | Text |
| Caption | Text |
| URL | URL |
| Content Type | Select (Post / Reel / Carousel) |
| Collection | Select |
| Post ID | Text |
| Processed | Checkbox |
| Synced At | Date |

**Content Ideas** (used by `ideate.py` and `/ideate`):

| Property | Type |
|---|---|
| Name | Title |
| Source URL | URL |
| Original Author | Text |
| Content Type | Select |
| Hook Variations | Text |
| Outline | Text |
| Instagram | Text |
| TikTok | Text |
| YouTube | Text |
| Status | Select (Draft / Approved / Published) |
| Created At | Date |

### 3. Get Instagram session cookies

1. Open Chrome and log in to instagram.com
2. Open DevTools → Application → Cookies → `https://www.instagram.com`
3. Copy the values for: `sessionid`, `csrftoken`, `ds_user_id`

These cookies last ~90 days. Re-run `setup.sh` when they expire.

### 4. Run setup

```bash
cd instagram-notion-sync
bash setup.sh
```

On first run it creates `config.env` from the template. Fill it in, then
re-run `setup.sh` — it installs dependencies, writes the launchd plist,
loads the agent, and runs a smoke-test sync.

### 5. Manual sync

```bash
source config.env
.venv/bin/python3 sync.py
```

## Part 2: Content ideation

### Option A — CLI script (`ideate.py`)

Processes all unprocessed saves interactively in the terminal:

```bash
source config.env
.venv/bin/python3 ideate.py            # all unprocessed saves
.venv/bin/python3 ideate.py --limit 5  # process at most 5
.venv/bin/python3 ideate.py --dry-run  # print without saving
```

For each save you'll see the content brief and be prompted to approve or skip.

### Option B — Claude Code slash command (`/ideate`)

Inside a Claude Code session in this repo, type `/ideate`. Claude will:

1. Fetch unprocessed saves from Notion
2. Generate content briefs in-context (no API key needed — uses the active Claude session)
3. Walk you through review interactively
4. Save approved briefs to Content Ideas and mark originals as processed

## Files

```
instagram-notion-sync/
├── sync.py              # Part 1: Instagram → Notion background sync
├── ideate.py            # Part 2: CLI ideation tool (uses Claude API)
├── requirements.txt
├── config.example.env   # Template — copy to config.env
├── setup.sh             # One-command setup
├── state.json           # Auto-generated; tracks synced post IDs
├── sync.log             # Auto-generated; sync run history
└── launchd/
    └── com.wintermute.instagram-sync.plist  # macOS scheduler

.claude/
└── commands/
    └── ideate.md        # /ideate slash command
```

## Troubleshooting

**"401 Unauthorized" from Instagram** — session cookies have expired. Re-extract
from the browser and update `config.env`, then re-run `setup.sh`.

**"object_not_found" from Notion** — check that the integration is shared with
both databases and that the IDs in `config.env` are correct (32 hex chars, no
hyphens).

**launchd agent not running** — check
`~/Library/Logs/wintermute-instagram-sync-error.log` and verify the plist was
loaded: `launchctl list | grep wintermute`.
