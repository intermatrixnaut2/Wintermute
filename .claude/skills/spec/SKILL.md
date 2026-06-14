---
name: spec
description: Turn a rough idea into a precise build spec BEFORE writing any code. Saves the spec to SPEC.md with Goal, In scope, Out of scope, Requirements, Structure, Edge cases, and Done checklist sections. Use when the user runs /spec [idea] and wants a spec written first, before implementation begins.
---

# Spec — Idea → Precise Build Spec

Turn the user's rough idea into a tight, testable spec saved to `SPEC.md`.
**Do not write any implementation code.** The spec is the deliverable.

## Input

`/spec [idea]`

- **idea**: a rough description of what the user wants to build. May be a
  single sentence or several paragraphs — both are fine.

## Behaviour

1. **Read the repo first.** Glob for existing files, read `CLAUDE.md` and any
   relevant source files, and understand the tech stack and conventions already
   in use. The spec must fit what already exists.

2. **Resolve ambiguity without asking** — make a sensible call and label it
   `Assumption:`. Only ask the user a question if a requirement is *genuinely*
   ambiguous and getting it wrong would force a full rewrite (e.g. the target
   platform is completely unknown). Ask at most one question; never block on
   minor details.

3. **Write `SPEC.md`** (overwrite if it already exists) using the template
   below.

4. **Output the spec in chat** — paste the full contents so the user can read
   it without opening the file. Add a one-line note at the end: "Spec saved to
   SPEC.md. Run /review against this spec once the build is done."

## SPEC.md template

```markdown
# Spec: <short title>

_Generated: <date>_

## 1. Goal
One sentence. What are we building and why?

## 2. In Scope
Bullet list. Every feature or behaviour that WILL be built.

## 3. Out of Scope
Bullet list. Things deliberately NOT built in this iteration.
Be specific — vague items like "no auth" are fine only when auth
is genuinely irrelevant. Call out common scope-creep traps.

## 4. Requirements
Numbered list. Each item must be independently testable — a human
or automated check should be able to mark it PASS or FAIL without
ambiguity.

1. …
2. …

_Assumption: [any call made without asking the user]_

## 5. Structure
Files, folders, and key components. Show the tree for new projects;
for additions to an existing project, show only new/changed paths.

```
src/
  new-module/
    index.ts       — entry point
    …
```

## 6. Edge Cases
Table or bullet list. What could go wrong, and what the expected
behaviour is in each case.

| Scenario | Expected behaviour |
|---|---|
| … | … |

## 7. Done Checklist
The requirements from §4 restated as checkboxes, for use with /review.

- [ ] 1. …
- [ ] 2. …
```

## Rules

- Sections must appear in the order above; do not rename or drop any.
- Requirements (§4) must be testable. Avoid adjectives like "fast",
  "nice", "clean" — replace them with measurable criteria or cut them.
- Out of Scope (§3) must have at least two items; if nothing obvious
  exists, name the two most tempting extensions and rule them out.
- Done Checklist (§7) must mirror §4 exactly — same numbering, same
  wording, just as checkboxes.
- No implementation code appears anywhere in the spec or in chat output.
