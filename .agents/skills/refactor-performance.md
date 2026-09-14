# Skill: Refactor & Performance (`@refactor`, `@performance`)

Global rules (model/effort routing, loop limits, verification, scope
control) live in `rules/workflow.md` — this file covers only the
investigation procedure for these two tags.

## `@refactor`

### CBM workflow

**trace → callers → dependencies → impact**

### Investigation

1. Find the current implementation.
2. Trace important callers.
3. Identify dependencies and downstream consumers.
4. Check whether the code is shared by multiple features.
5. Determine whether the refactor changes behavior or only structure.

### Report

- Current structure
- Callers
- Dependencies
- Safe refactoring boundary
- Potential breakage
- Recommended approach

Preserve existing behavior unless explicitly asked otherwise.

## `@performance`

### CBM workflow

**trace → hotspots → dependencies → runtime**

### Investigation

1. Trace the relevant execution path.
2. Identify expensive or repeated operations.
3. Find database and external-service dependencies.
4. Look for unnecessary calls, repeated computation, N+1 patterns, or
   redundant processing.
5. If the path touches the cache (`cache.py`), check whether it's being
   hit as expected, or whether misses/invalidation are the actual cost.
6. Identify the smallest safe optimization.

Separate what's proven from source code, what's only a possible
bottleneck, and what requires runtime measurement. Do not claim a
bottleneck is confirmed without runtime evidence when runtime measurement
is required — this is investigation depth, not something to shortcut for
quota.
