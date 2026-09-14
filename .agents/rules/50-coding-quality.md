# Coding Safety & Quality

## Existing code first

Search for existing functionality before creating new logic.
Prefer reuse when it fits the existing architecture and conventions.

## Preserve architecture

- Follow established project patterns.
- Keep abstractions proportionate to the task.
- Do not introduce dependencies unless necessary.
- Do not silently change public API behavior.
- Preserve existing behavior unless a change is explicitly requested.

## Focused implementation

- Keep changes minimal and cohesive.
- Do not modify unrelated files.
- Do not refactor unrelated code during a feature or bug fix.
- Do not turn discovered optional improvements into unrequested work.

## Evidence discipline

- Distinguish confirmed facts from hypotheses.
- Do not claim runtime behavior from static code alone.
- For external APIs, queues, caches, background workers, and production-only behavior, state when runtime evidence is required.
- Do not treat one inconclusive search as proof of root cause.

## Refactoring boundary

Use refactoring to improve internal structure, readability, duplication, or
separation of responsibility while preserving intended externally observable
behavior.

Do not use `@refactor` as a reason to expand a bug/feature task into unrelated
cleanup.

## Final review

Before finishing:
- review the final Git diff;
- check for accidental unrelated edits;
- check public API/contract changes;
- check that documentation/architecture notes still match implemented behavior.
