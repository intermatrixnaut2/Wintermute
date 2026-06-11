---
name: storyboard-words
description: Read a storyboard PDF page by page and derive creative words, titles, and lines in the user's established voice, learned from a reference work. Use when the user asks to derive words from a storyboard, caption panels, name sequences, or pull creative language out of a binder/storyboard PDF.
---

# Storyboard → Creative Words

Derive creative language from a visual storyboard, written in the user's own
voice as learned from a reference piece of their finished work.

## Inputs

Arguments: `$ARGUMENTS` may contain one or two PDF paths:
`/storyboard-words <storyboard.pdf> [reference.pdf]`

Defaults when no arguments are given:

- **Storyboard (source images):**
  `/Users/intermatrixnaut/Documents/Claude AI personal Assistant/Binder_duex.pdf`
- **Voice reference (the user's finished work):**
  `/Users/intermatrixnaut/Documents/Claude AI personal Assistant/01story10-pdf.pdf`

Both paths contain spaces — always quote them in shell commands. Prefer the
Read tool (which renders PDF pages visually) over any text-extraction CLI;
the artwork matters as much as any text on the page.

## Step 1 — Learn the voice from the reference

Read the reference PDF in full before looking at the storyboard. PDFs over
10 pages require the `pages` parameter; read in chunks of up to 20 pages.

While reading, build a short **voice profile** (write it out before moving
on, so it anchors the rest of the session):

- Diction: concrete vs. abstract, invented words, recurring vocabulary
- Rhythm and length: fragments vs. full sentences, line breaks, repetition
- Imagery domains the user returns to (light, machinery, water, bodies...)
- Tone: deadpan, mythic, intimate, clinical — name it precisely
- How words sit against images in their work: titles? captions? floating
  phrases? narration?

Do not summarize the reference's plot. The deliverable from this step is
*how the user writes*, not what they wrote about.

## Step 2 — Walk the storyboard

Read the storyboard PDF page by page (again, chunked with `pages` if long).
For each page or panel:

1. Note the visual beat in one plain sentence (composition, subject, motion,
   mood) — this is scaffolding, kept brief.
2. Derive the creative words **in the learned voice**: offer 2–4 options per
   beat, ranging from a single word to a short line. These should read like
   the user wrote them, not like alt-text or a synopsis.

Resist generic description ("a figure stands in shadow"). The point is the
leap from image to language the way the reference work makes that leap.

## Step 3 — Synthesize and deliver

After the page-by-page pass:

- Pull out throughlines: words or images that recurred and could title the
  whole sequence. Offer 3–5 candidate titles.
- Note any pages where the storyboard's energy shifts — act breaks the
  language should honor.

Write the full output to a markdown file alongside the storyboard PDF
(same folder, e.g. `Binder_duex — words.md`), structured as:

```
# <working title candidates>
## Voice profile (one short paragraph)
## Page-by-page words
### p.1 — <one-line visual note>
- option 1
- option 2
...
## Throughlines & titles
```

Then give the user a short in-chat summary: the voice profile, the three
strongest lines from the whole pass, and the title candidates. Ask nothing
unless a PDF is missing or unreadable — if a default path doesn't exist,
ask the user for the correct location rather than guessing.
