---
name: storyboard-words
description: Read a storyboard PDF page by page and develop it in the user's own voice — either fleshing the rough symbol interpretations into full story scenes with emotive dialogue (Viaticum register), or deriving compressed creative words and titles (01story10 register). Use when the user asks to flesh out a storyboard, write dialogue for panels, derive words from a storyboard, caption panels, or develop the Binder/DeuxSept boards into narrative.
---

# Storyboard → Story (and Words)

The user's storyboards are a *rough first-round interpretation of symbols* —
not finished compositions. The job is to take that first pass and develop it
in one of the user's two established voices, learned from their own work.

## Inputs

`/storyboard-words [mode] [storyboard] [reference]`

- **mode**: `flesh` (default) or `words` — see Registers below.
- **storyboard**: defaults to `Binder_duex.pdf`
- **reference**: defaults per mode (Viaticum for `flesh`, 01story10 for `words`)

## Source files — local first, Drive fallback

Local paths (when running on the user's Mac; always quote — they contain
spaces). All live in `/Users/intermatrixnaut/Documents/Claude AI personal
Assistant/`:

| File | Local name | Google Drive file ID |
|---|---|---|
| Storyboard | `Binder_duex.pdf` | `13dkLKkHTFQYZr4rqaaE50m61d-1dh1sl` |
| Narrative voice reference | `Viaticum.docx` | `1auWya9C-r5q1EDFRpXDAzlR36IxUNeLe` |
| Mythic voice reference | `01story10-pdf.pdf` | `1-jdYdmY9RuoLpaig0IAS5GWWerhXsczA` |

If a local path doesn't exist (e.g. running in a remote/web session), read
the same file through the Google Drive MCP tools using the file ID above
(`read_file_content` for text; for the storyboard's *images*, download the
PDF via `download_file_content` to a temp file and view pages with the Read
tool). Prefer the Read tool for PDFs wherever possible — the artwork and
symbols matter as much as any text.

## The two registers

Both reference works share one universe (Kincaide McQuade, Anastasia,
Vauhgohd the Organicycle, S.T.A.R.E., I.D.Y., biocomputers like
Ghayllieuxjah). They differ in mode, and the skill must keep them distinct:

- **Narrative register — `flesh` (Viaticum):** first-person or close-third
  prose, linear scenes, conventional sentences whose strangeness lives in
  what they describe. Intimate, domestic stakes inside cosmic events.
  Emotive dialogue carries the scenes: characters reassure, plead, tease,
  grieve, and say goodbye. Invented words are rare and land hard.
- **Mythic register — `words` (01story10):** coded stanza-sections,
  sound-driven alliterative lines, neologisms as fabric, archetypal
  characters, no stable narrator. Compressed phrases, not scenes.

## Step 1 — Learn the voice

Read the reference for the chosen mode in full (chunk PDFs with `pages`,
max 20 per request). Write out a short voice profile before continuing.
For `flesh` mode, study Viaticum's dialogue especially:

- How characters address each other by full name at emotional peaks
  ("Kincaide Alexis McQuade...")
- Reassurance and care as the dominant emotional currents — tenderness
  against the backdrop of an overwhelming event
- Dialogue tags that carry gesture and material detail (a tie straightened,
  a card extended with two fingers)
- Farewells as set-pieces ("Hugs and kisses. Sugarbear wishes.")

## Step 2 — Walk the storyboard

Read the storyboard page by page. For each page or panel, remember: what's
drawn is a **rough first-round interpretation of symbols**. Treat each
symbol as a seed, not a spec — identify what it gestures at, then develop
past it. For each beat note briefly: the symbol/figure as drawn, what it
plausibly encodes in this universe, and the emotional charge implied.

## Step 3 — Develop

**`flesh` mode (default):** write each page or run of related pages as a
full prose scene in the Viaticum register:

- Ground the scene in a body and a point of view; let dialogue do the
  emotional work — characters speaking their wonder, fear, and devotion
  rather than the narrator naming it.
- Keep continuity with the existing mythos (characters and machines above)
  unless the storyboard clearly introduces new figures — then name them in
  the user's naming style and note that they're new.
- Where a symbol is genuinely ambiguous, write the scene for the strongest
  reading and add a one-line aside `[symbol on p.N could also read as ...]`
  so the user can redirect on the next round. This is a first fleshing-out,
  meant to be revised.

**`words` mode:** as before — 2–4 compressed options per beat in the
01story10 register, then throughlines and 3–5 title candidates.

## Step 4 — Deliver

Write the full output to a markdown file next to the storyboard when local
(`Binder_duex — story.md` / `— words.md`); in remote sessions, save it in
the repo under `planning/` and offer to also upload it to the same Drive
folder. Structure for `flesh` mode:

```
# <working title>
## Voice profile
## Scenes
### Scene 1 (pp. N–M) — <one-line beat>
<prose with dialogue>
[symbol notes, if any]
...
## Open questions for round two
```

Finish with a short in-chat summary: the strongest scene, any new characters
introduced, and the list of ambiguous symbols awaiting the user's call.
