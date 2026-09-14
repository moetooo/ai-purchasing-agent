# AI Coding Core Rule

## Purpose

Guide safe, high-quality coding while minimizing **unnecessary** agent work.
Optimize for:

**Correctness → confidence → quota efficiency → minimal redundancy**

Quota efficiency must come from removing waste, never from skipping necessary
reasoning, investigation, tests, or verification.

This rule recommends model/effort choices but cannot change Antigravity's model
selector or read live quota. The user selects the recommended model manually.

## Navigation

Do not reread every workflow or Skill for every task.

Use this routing:

- Overall process → this file
- Model + effort → `10-model-routing.md`
- Context/session/navigation → `20-context-efficiency.md`
- Loops/scope → `30-loop-scope.md`
- Verification/risk → `40-verification-risk.md`
- Coding quality → `50-coding-quality.md`
- Task-specific investigation/implementation → relevant Skill

Skill procedures are task-specific. Load/use only the relevant Skill(s).

## Tags & Skills

Use an action tag when the task fits one. Tags may combine; apply the union of
relevant procedures, with the more specific tag driving investigation order.

| Tag | Skill | Typical starting effort |
|---|---|---|
| `@bug` | `bug-fix` | LOW* |
| `@update` | `bug-fix` | LOW* |
| `@feature` | `feature` | MEDIUM |
| `@refactor` | `refactor` | MEDIUM |
| `@performance` | `security-performance` | MEDIUM |
| `@cleanup` | `test-docs-cleanup` | LOW* |
| `@test` | `test-docs-cleanup` | LOW* |
| `@docs` | `test-docs-cleanup` | LOW* |
| `@api` | `api-database` | MEDIUM |
| `@database` | `api-database` | MEDIUM* |
| `@security` | `security-performance` | MEDIUM* |
| `@architecture` | `refactor` | HIGH* |
| `@ingestion` | `ingestion-task` | MEDIUM |
| `@task` | `ingestion-task` | MEDIUM |
| `@llm` | `llm-rag` | MEDIUM |


'typical starting effort' is only a prior. Actual classification is governed
by `10-model-routing.md` after evidence is gathered.

When a tag is used:

1. Follow the relevant Skill.
2. Use CBM when relevant.
3. Do not modify files during investigation unless the user explicitly asks for investigation-and-edit in one step.
4. Report the provisional and confirmed model/effort classifications.
5. Wait for approval before implementation unless the user explicitly asks to implement immediately.
6. Verify according to `40-verification-risk.md`.
7. Keep the approved scope focused.

## Core Workflow

For non-trivial work:

**Understand → Investigate → Plan → Approve → Implement → Verify → Test → Git Diff**

Investigation:
- Build enough evidence to establish the current flow and likely root cause.
- Do not scan unrelated areas.
- Reuse facts already established in the current task.
- Distinguish confirmed facts from hypotheses.
- Do not modify files during investigation.

Plan:
- State affected files/components, key risks, acceptance criteria, verification tier, and confirmed effort/model.

Implementation:
- Make the smallest safe change that satisfies the approved plan.
- Preserve existing behavior unless a behavior change is requested.
- Do not refactor unrelated code.
- Do not introduce dependencies unless necessary.
- If scope materially expands or crosses a subsystem boundary, stop and report the revised scope before continuing.

## Fast Path

Use the fast path only when **all** are true:

1. The change is 1–2 lines in one location.
2. Correctness is objective and unambiguous (for example typo, comment, log wording, or trivial constant).
3. There is no security, data-integrity, migration, compatibility, concurrency, or visual/look-and-feel implication.

Never use the fast path for UI/styling work, multi-location changes, ambiguous behavior, security-sensitive changes, migrations, or data-integrity/concurrency issues.

If in doubt, use the full cycle.

## Quality Before Quota

Never skip:
- caller/dependency analysis for a shared function;
- migration/compatibility analysis for meaningful schema/API changes;
- security/data-flow analysis;
- evidence needed to establish a root cause;
- verification required by risk.

Safe to avoid when not justified:
- whole-repository scans for isolated tasks;
- duplicate searches;
- re-reading unchanged context;
- broad builds/tests for trivial changes;
- broad verification when targeted verification is sufficient.

## Reporting

Keep reports concise and non-repetitive.

Before investigation:
```text
Provisional effort: <LOW/MEDIUM/HIGH>
Starting model: <Gemini model> + <effort>
Why: <one line>
```

After initial investigation:
```text
Confirmed effort: <LOW/MEDIUM/HIGH>
Recommended model: <Gemini model> + <effort>
Why: <one line>
Reclassified because: <change or "no change">
Escalate if: <specific trigger>
```

Before implementation:
```text
Plan: <one line>
Affected: <files/components>
Key risks: <or "none identified">
Verification tier: <TARGETED/COMPONENT/FULL>
```

After implementation:
```text
Changed: <summary>
Review model: <model> + <effort>
Verification performed: <what ran>
Remaining uncertainty: <or "none">
```

## Standing Principles

- Understand first. Classify honestly. Modify second. Verify at the right depth. Stop when done.
- Existing code first.
- Minimal focused changes.
- No silent scope expansion.
- No open-ended loops.
- No quota optimization at the expense of correctness.
