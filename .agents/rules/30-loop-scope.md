# Loop & Scope Control

## Bounded task template

For non-trivial tasks, establish:

```text
Task: <what must change>

Scope:
- <target files/directories/symbols>

Do not:
- scan unrelated areas
- refactor unrelated code
- change dependencies unless necessary
- repeat established searches

Done when:
- <concrete acceptance criterion>

Verify with:
- <targeted command/check>

Stop when:
- acceptance criteria are satisfied

Default maximum:
- 2 edit/verify cycles
```

## Investigation escalation

Pass 1:
- targeted search/trace/inspection.

Pass 2 only if evidence is insufficient:
- investigate the specific missing fact;
- do not broaden into a repository-wide rescan.

After Pass 2:
- escalate the model or split the task if ambiguity remains.

## Implementation cycles

Default:
**2 edit/verify cycles.**

A third cycle is allowed only when the next action is:
- concrete;
- materially different from prior attempts;
- likely to produce new evidence or resolve a real remaining defect.

For genuinely complex HIGH/VERY HIGH tasks, raise the limit explicitly before
implementation rather than discovering the need through repeated looping.

If the same strategy repeats without new evidence:
**stop → summarize → reassess → escalate or split.**

## Verification failures

A failed check does not automatically restart the entire investigation.

First classify the failure:
- **Local** → fix and rerun the focused check.
- **Component-level** → widen to COMPONENT verification.
- **Architectural** → revisit investigation only when the failure's evidence indicates a broader cause.

Broaden only when new evidence justifies it.

## Scope categories

Separate:

- **Required changes** — part of the approved plan; implement them.
- **Discovered-but-unrelated issues** — report; do not fix in the same pass.
- **Optional improvements** — mention; do not act unless requested.

## Scope expansion

Scope may expand mid-task only when necessary for:
- correctness;
- security;
- compatibility;
- required functionality;
- an existing contract that cannot otherwise be preserved.

If implementation reveals many more files, a different subsystem, a new
API/schema contract, or materially larger blast radius for another reason:
stop and report the revised scope before continuing.

Never silently expand an approved task.

## Minimal change

Prefer the smallest safe change that satisfies the acceptance criteria.
Do not turn a feature/bug fix into an unrelated refactor.
