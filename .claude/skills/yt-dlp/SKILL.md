---
name: yt-dlp
description: Download a YouTube (or other supported site) video or audio using yt-dlp. Invoke with /yt-dlp <url> [options]. Supports optional flags: --audio-only, --quality <format>, --output <dir>. In remote/phone sessions, uploads the result to Google Drive so the file is accessible.
---

# yt-dlp Download Skill

Downloads video or audio from YouTube and other supported sites. Works in local and remote/phone sessions.

## Usage

```
/yt-dlp <url> [--audio-only] [--quality <format>] [--output <dir>]
```

- `url` — required, the video URL (YouTube, SoundCloud, Twitter/X, etc.)
- `--audio-only` — extract audio only, saved as MP3
- `--quality <format>` — e.g. `best`, `720p`, `1080p` (default: `best`)
- `--output <dir>` — local directory to save to (default: `~/Downloads` if it exists, else the repo root)

## Step 1 — Ensure yt-dlp is available

Run:
```bash
which yt-dlp || pip install yt-dlp
```

Also check for ffmpeg (needed for merging video+audio and MP3 conversion):
```bash
which ffmpeg || apt-get install -y ffmpeg 2>/dev/null || echo "ffmpeg not available — best single-format will be used"
```

## Step 2 — Determine output directory

- If `--output <dir>` was given, use it.
- If `~/Downloads` exists, use it.
- Otherwise, use `/tmp` (or the session scratchpad).

In a remote/phone session (no local `~/Downloads`), plan to upload the result to Google Drive after download.

## Step 3 — Build and run the yt-dlp command

For **video** (default):
```bash
yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" \
  --merge-output-format mp4 \
  -o "<output_dir>/%(title)s.%(ext)s" \
  "<url>"
```

For **audio only** (`--audio-only`):
```bash
yt-dlp -f "bestaudio" \
  --extract-audio --audio-format mp3 --audio-quality 0 \
  -o "<output_dir>/%(title)s.%(ext)s" \
  "<url>"
```

For a specific quality like `720p`:
```bash
yt-dlp -f "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best" \
  --merge-output-format mp4 \
  -o "<output_dir>/%(title)s.%(ext)s" \
  "<url>"
```

Capture the filename of the downloaded file by running yt-dlp with `--print filename` first, or parse the output for "Destination:" or "has already been downloaded".

## Step 4 — Remote/phone session: upload to Google Drive

If running in a remote execution environment (container, no `~/Downloads`, phone session), after the download succeeds:

1. Use `mcp__Google_Drive__create_file` to upload the downloaded file to Google Drive.
   - Set the file name to the video title with extension.
   - Set the MIME type appropriately (`video/mp4` or `audio/mpeg`).
2. Share the resulting Drive link with the user.

> Note: Google Drive MCP `create_file` may require the file content as base64 or a path — check available parameters. If direct upload isn't supported, tell the user the local path and offer to copy it to a repo folder and push instead.

## Step 5 — Report to user

Tell the user:
- The video title
- File size (use `ls -lh`)
- Where it was saved (local path and/or Google Drive link)
- Duration if visible in yt-dlp output

## Error handling

- **429 / rate limited**: retry once after 30 s, or suggest the user try again later.
- **Private/age-restricted video**: inform the user; suggest `--cookies-from-browser chrome` if running locally.
- **Format not available**: fall back to `best` and note the format used.
- **ffmpeg missing**: use `yt-dlp -f best` (single pre-muxed stream) and warn that quality may be limited.
- **Proxy 403 / tunnel blocked**: the remote execution environment's network proxy blocks direct YouTube connections. In this case, inform the user that downloads must be run in a local Claude Code session (desktop/CLI), not a web/phone remote session.
