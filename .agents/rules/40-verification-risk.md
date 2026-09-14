# Verification & Risk

## Effort vs Risk

Effort measures reasoning/implementation complexity.
Risk measures consequence if wrong.

They are separate axes.

A LOW-effort task can require strong verification when it involves security,
data integrity, migrations, concurrency, shared contracts, or external side
effects.

A HIGH-effort task does not automatically require FULL verification if its blast
radius is isolated and targeted/component checks provide sufficient confidence.

## Verification tiers

### TARGETED
Use first for most changes:
- focused test;
- changed-file lint/type check;
- narrow command/check;
- manual visual/UI spot-check when behavior is visual.

### COMPONENT
Use when the change crosses a meaningful integration boundary, such as:
- shared service;
- shared schema;
- API contract;
- queue/cache interaction;
- caller/callee relationship where local verification is insufficient.

### FULL
Use when justified by:
- broad blast radius;
- shared infrastructure or data changes;
- delivery requirements;
- inability of targeted/component checks to provide sufficient confidence;
- confirmed high-impact security/data-integrity/migration risk.

Do not run every test/lint/typecheck/build by default for a small isolated change.

## Risk override

Choose the verification tier from both effort and risk.

Minimum guidance:

- Security/data-integrity/concurrency/migration risk present → at least COMPONENT.
- Confirmed security vulnerability or migration touching shared data → FULL unless a documented project constraint makes a narrower check demonstrably sufficient.
- MEDIUM change crossing a shared API/schema boundary → at least COMPONENT.
- HIGH but isolated low-risk UI change → does not automatically require FULL.

Risk overrides the default effort-based verification floor.

## After implementation

1. Run the selected verification tier.
2. If it fails, diagnose the failure directly before widening scope.
3. Do not restart broad investigation unless the failure creates new evidence.
4. Use CBM for unintended-impact checks only where useful.
5. Review the final Git diff.
6. Report failures and remaining uncertainty clearly.

## Verification ≠ investigation

Verification exists to test the implementation, not to trigger a generic reread.

A verification failure should widen investigation only when the evidence points
beyond the current local/component explanation.

## Quality protection

Never reduce verification or necessary analysis solely to save quota.
Save quota by eliminating repeated or unjustified work.
