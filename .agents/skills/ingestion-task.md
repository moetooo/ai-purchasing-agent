# Skill: Ingestion & Background Tasks (`@ingestion`, `@task`)

Global rules (model/effort routing, loop limits, verification, scope
control) live in `rules/workflow.md` — this file covers only the
investigation procedure for these two tags.

## `@ingestion`

Use for changes touching the AniList / Jikan / MangaDex ingestion
pipeline: `anilist_client.py`, `jikan_client.py`, `mangadex_client.py`,
`discovery.py`, `enrich.py`, `merge.py`, `normalize.py`,
`deduplicate.py`, `upsert.py`.

### CBM workflow

**source → transform → merge/dedupe → validate → sink**

### Investigation

1. Identify which source client is involved and its pagination/rate-limit
   handling.
2. Trace the pipeline stage(s) affected (discovery → enrich → merge →
   normalize → deduplicate → upsert).
3. Check how records from different sources are merged and deduplicated,
   so the fix doesn't reintroduce duplicate or conflicting titles.
4. Check `upsert.py` for idempotency — re-running ingestion shouldn't
   create duplicate rows or corrupt stored embeddings.
5. Check what happens on partial failure (one source API errors
   mid-run): is the pipeline resumable, or does it need a clean restart?
6. Identify downstream impact — ingested data feeds `embedding.py` /
   `retrieval.py`, so a data-quality issue here can surface as a bad
   `/recommend` result.

### Report

- Source(s)/stage(s) affected
- Duplicate/idempotency risk
- Partial-failure behavior
- Downstream impact on embeddings/retrieval
- Proposed fix

External API failures, rate limits, and actual response payloads are
runtime behavior CBM can't verify from static code — flag clearly when a
fix depends on live API behavior you haven't observed.

## `@task`

Use for changes to Celery tasks — definitions, triggers, retries, or what
a task writes to Postgres/Redis.

### CBM workflow

**task definition → trigger → retry policy → idempotency → result
handling**

### Investigation

1. Find the task definition and where it's triggered from (an API route,
   another task, or a schedule).
2. Check the retry configuration (max retries, backoff) and what happens
   after final failure.
3. Check idempotency — can the task safely run twice without duplicating
   or corrupting data?
4. Trace what the task writes to, and whether concurrent runs could race.
5. Identify how failures are surfaced — logged, silently swallowed, or
   retried indefinitely?

### Report

- Task location and trigger
- Retry/idempotency behavior
- Race/concurrency risk
- Proposed fix

Actual task timing, queue backlog, and worker crashes are runtime
behavior — CBM can trace the code path but not observe live queue state.

A real idempotency or race-condition finding in either tag is a
Classification Priority signal (rules file, Section 3, concurrency) —
reclassify upward regardless of diff size.
