# /ideate — Instagram Saves → Content Ideas

Turn unprocessed Instagram saves from Notion into actionable content briefs
for beginner AI solo founders. Review each brief, then save approved ones to
the Content Ideas database and mark the original save as processed.

---

## What to do when this command runs

**Step 1 — Fetch unprocessed saves**

Use the Notion MCP tool to query the Instagram Saves database.
Filter for `Processed = false`, sorted by `Synced At` ascending.

Extract for each result:
- `Author` (rich_text)
- `Caption` (rich_text)
- `URL` (url)
- `Content Type` (select)
- `Collection` (select)
- Page ID (for the update call later)

If there are no unprocessed saves, tell the user and stop.

---

**Step 2 — Ideate on each save**

For each unprocessed save, reframe the content for **beginner AI solo founders**
(people building products or businesses with AI, often non-technical). They want
practical tips, actionable frameworks, and inspiration they can use today.

Generate a complete content brief with these sections:

### Hook Variations (3 total)
Write three distinct hooks targeting different emotional triggers:
1. **Curiosity hook** — makes them need to know the answer
2. **Contrarian hook** — challenges a common assumption they hold
3. **How-to hook** — promises a clear, specific outcome

### Structured Outline
```
Hook: [paste best hook here]

Key Points:
1. [concrete, actionable point]
2. [concrete, actionable point]
3. [concrete, actionable point]
(add up to 2 more if the topic demands it)

CTA: [one specific action to take right now]
```

### Platform Breakdowns

**Instagram** (carousel or Reel):
- Format: carousel / Reel / static
- Slide 1 / opening scene: [hook execution]
- Slides 2–6 / scenes: [key points mapped to slides or cuts]
- Final slide / outro: [CTA + save prompt]
- Caption opener (first 125 chars)
- 5 hashtags

**TikTok** (short-form video):
- Hook (seconds 0–3): [exact words or action]
- Structure: [scene-by-scene, 30–60 sec]
- Trend angle or audio suggestion
- On-screen text for key moment

**YouTube** (long-form or Shorts):
- Title (A/B: two options)
- Thumbnail concept (visual + text overlay)
- Chapter outline (if long-form, 5–10 min)
  OR Shorts structure (60 sec) if the topic is better served short

---

**Step 3 — Present for review**

Show a clearly formatted brief for each save. After showing the brief, ask:

> **Approve this idea?**
> `[y] Save to Content Ideas` | `[s] Skip` | `[q] Stop processing`

Wait for the user's input before moving to the next save.

---

**Step 4 — Save approved ideas**

For each approved brief, create a new page in the Content Ideas database with
these properties:

| Property | Value |
|---|---|
| Name (title) | Hook variation #1 (truncated to 255 chars) |
| Source URL | Original Instagram post URL |
| Original Author | Author from the save |
| Content Type | Same as the save |
| Hook Variations | All 3 hooks, numbered, as rich text |
| Outline | Full structured outline as rich text |
| Instagram | Full Instagram breakdown as rich text |
| TikTok | Full TikTok breakdown as rich text |
| YouTube | Full YouTube breakdown as rich text |
| Status (select) | `Draft` |

Then update the original Instagram Saves page: set `Processed = true`.

Tell the user: ✓ Saved and marked processed.

---

**Step 5 — Summary**

When all saves are processed (or user quits early), print:

```
Done — approved: X  |  skipped: Y  |  remaining: Z
```

---

## Tone guidance for the ideation

- Write like a practitioner, not a coach
- Concrete specifics beat vague advice ("use GPT-4 to draft your onboarding email" beats "use AI to save time")
- Assume zero budget, one person, limited time
- The audience follows creators to shortcut learning — respect that with density
- No filler phrases: "In today's video", "Let me know in the comments", "Don't forget to like"
- Every hook should be completable in under 15 words
