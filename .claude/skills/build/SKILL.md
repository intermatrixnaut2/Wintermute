---
name: build
description: Read SPEC.md and implement it exactly — nothing extra. Build only what is in "In scope" and "Requirements". Write anything outside the spec under "Suggestions". Work through requirements in order, announcing each requirement number as it is satisfied. End with a full built/not-built checklist.
---

# Build from SPEC.md

Read `SPEC.md` in the project root and implement it exactly as written.

## Rules

1. **Scope** — implement only what appears under "In scope" and "Requirements". If a feature, behaviour, or abstraction is not stated in the spec, do NOT add it.
2. **Suggestions** — if you notice something useful that is not in the spec, list it under a "Suggestions" section at the end of your response. Do not build it.
3. **Order** — work through the requirements in the order they are numbered. After completing each one, say: `✓ Requirement N — <one-line summary>`.
4. **Small changesets** — keep each change small and self-contained so it is easy to review. Prefer editing existing files over creating new ones.
5. **Honesty** — never claim a requirement is done unless you have actually written the code. If you cannot build something, say so and explain why.

## Workflow

1. Read `SPEC.md` in full.
2. Confirm what is "In scope" and list the requirement numbers you are about to implement.
3. Implement each requirement in order, announcing it when done.
4. After all requirements, output a summary table:

```
## Build summary
| # | Requirement | Status |
|---|-------------|--------|
| 1 | ...         | built  |
| 2 | ...         | NOT built — <reason> |
```

5. If there is anything worth suggesting that was not in the spec, list it under `## Suggestions`.
