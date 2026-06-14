---
name: review
description: Grade the current build against SPEC.md like a strict senior engineer — then fix and loop. Reads the "Done checklist" in SPEC.md, marks each item PASS or FAIL with a one-line reason and the file where it's handled (or missing), fixes every FAIL, re-checks, and repeats until everything passes or hits a real blocker.
---

# /review — Build Grade & Fix Loop

Grade the current build against the "Done checklist" in `SPEC.md`, fix every failure, and loop until the build is clean.

## Step 0 — Locate SPEC.md

Read `SPEC.md` in the repo root. If it doesn't exist, stop immediately and tell the user:

> **Blocker:** `SPEC.md` not found. Create it with a "Done checklist" section — a markdown checklist of acceptance criteria — then re-run `/review`.

Do not invent checklist items. Do not proceed.

## Step 1 — Extract the checklist

Find the section in `SPEC.md` headed **"Done checklist"** (case-insensitive; also accept "Done Checklist", "Checklist", "Acceptance Criteria", or a markdown checklist `- [ ]` / `- [x]` block). Extract every item as a discrete testable requirement.

If the section is missing or empty, stop and tell the user which heading to add.

## Step 2 — Audit each item

For every checklist item, verify it against the actual code. Do not assume — open the relevant file(s) and confirm. Mark each item:

```
[ PASS ]  <item text>
          → <file>:<line-or-function>  — <one-line reason it passes>

[ FAIL ]  <item text>
          → <file or "MISSING">  — <one-line reason it fails>
```

Rules for marking:
- **PASS** only if you read the code and it satisfies the requirement end-to-end. UI features that can't be verified by code inspection alone should be marked FAIL unless the code path is unambiguous.
- **FAIL** if the feature is absent, broken, incomplete, or only partially implemented.
- If a requirement is ambiguous, note it inline but do not mark it PASS on ambiguity alone.

## Step 3 — Prioritise the FAILs

List every FAIL in priority order:

1. Crashes / broken core loop (renders nothing, loads nothing)
2. Missing required features explicitly named in SPEC.md
3. Wrong behaviour (feature exists but does the wrong thing)
4. Missing polish/UX the spec calls for
5. Anything else

## Step 4 — Fix loop

Work through the FAILs from highest to lowest priority. For each:

1. State what you're fixing and why.
2. Make the minimal correct change. Do not refactor unrelated code.
3. After fixing, re-read the changed code to confirm the fix is sound.
4. Do not mark the item PASS until the fix is in place and verified.

After fixing all FAILs, return to Step 2 and re-audit the full checklist from scratch. Repeat the fix loop until:

- Every item is PASS → go to Step 5, or
- You hit a genuine blocker you cannot resolve (missing asset, external dependency, browser-only API that can't be tested statically, requires user input/hardware, etc.) → stop and explain the blocker clearly: what it is, why you can't fix it, and what the user needs to do.

## Step 5 — Final PASS report

Output a clean summary:

```
## Build Review — PASS

All N checklist items verified.

| # | Item | File | Status |
|---|------|------|--------|
| 1 | ...  | src/main.js:42 | PASS |
...

No blockers. Build meets spec.
```

If any items remain unresolvable, output a PARTIAL PASS report that clearly separates PASS items from blocked items, and explains each blocker in one plain sentence.

## Constraints

- Never mark something PASS that you didn't actually verify by reading the code.
- Never skip re-auditing after fixes — a fix to item 3 can break item 1.
- Do not add features, refactor, or improve things not covered by the checklist.
- Keep fixes minimal and targeted.
- If SPEC.md has no checklist but has other content, read it for intent — but still stop and ask the user to add a formal checklist before grading.
