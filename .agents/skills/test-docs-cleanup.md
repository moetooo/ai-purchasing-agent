# Skill: Test / Docs / Cleanup (`@test`, `@docs`, `@cleanup`)

Global rules (model/effort routing, loop limits, verification, scope
control) live in `rules/workflow.md` — this file covers only the
investigation procedure for these three tags.

## `@test`

### CBM workflow

**search → implementation → trace → test**

1. Find the implementation.
2. Trace important execution paths.
3. Identify critical behaviors, edge cases, error paths.
4. Identify dependencies that should be mocked.

Do not modify production code unless explicitly required.

The project's `tests/` directory may be Git-ignored intentionally — don't
change `.gitignore` just to make it visible to CBM. CBM's index skips
git-ignored files, so read existing tests directly from disk when you
need to see what's already covered.

## `@docs`

Use for `README.md`, `ARCHITECTURE.md`, comments, or workflow files — no
code behavior change. Skip the full investigate → approve cycle; this is
low-risk.

1. Make the edit.
2. If it's `ARCHITECTURE.md` and the described architecture changed, a
   quick architecture check is enough to confirm it still matches the
   code.
3. Report what changed.

No tests/build needed, unless the docs contain code samples that should
be verified.

## `@cleanup`

### CBM workflow

**search → callers → dead code → impact**

Before removing anything:

1. Search for the implementation.
2. Find all usages/callers.
3. Check whether it is actually reachable or used.
4. Identify dependencies.
5. Determine whether removal affects another feature.

Report whether it is safe to remove and why. Do not remove code simply
because it appears unused without checking its usage.
