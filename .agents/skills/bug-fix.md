# Skill: Bug Fix (`@bug`, `@update`)

Global rules (model/effort routing, loop limits, verification, scope
control) live in `rules/workflow.md` — this file covers only the
investigation procedure for these two tags.

`@update` is the same shape as `@bug` — a change to how existing behavior
works, rather than a defect. Use `@update` when nothing is actually
"broken," `@bug` when something is.

## CBM workflow

**search → trace → inspect → impact**

## Investigation

1. Search for the relevant implementation.
2. Trace the execution path from the entry point.
3. Inspect the exact functions/components involved.
4. Identify the likely root cause (`@bug`) or exactly what must change and
   what must stay the same (`@update`).
5. Check callers, dependencies, and potential impact.

While investigating, watch for anything that reclassifies the task per
the rules file's Classification Priority — a bug that turns out to touch
security, data integrity, concurrency, or migrations is no longer a plain
LOW-effort fix regardless of how small the eventual diff is.

## Report

For `@bug`:
- Root cause
- Affected files/functions
- Proposed fix
- Potential side effects

For `@update`:
- Current behavior
- Desired behavior
- Files/functions affected
- Implementation plan
- Potential side effects
