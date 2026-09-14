# Skill: Architecture Change (`@architect`)

Global rules (model/effort routing, loop limits, verification, scope
control) live in `rules/workflow.md` — this file covers only the
investigation procedure for this tag.

## CBM workflow

**architecture → search → trace → dependencies → impact**

## Investigation

1. Get the current architecture.
2. Identify relevant system boundaries.
3. Search for related implementations.
4. Trace important execution paths.
5. Identify dependencies and callers.
6. Determine the blast radius.
7. Compare the current architecture with the proposed architecture.

Do not modify files during investigation.

## Report

- Current architecture
- Relevant boundaries
- Dependencies
- Affected components
- Proposed architecture
- Migration plan
- Risks

After implementation is approved and done, update `ARCHITECTURE.md` to
match — it's committed to Git, so it should stay accurate. Keep durable
project context there too (common commands, service boundaries,
project-specific conventions, known constraints) rather than creating a
second context file — one durable-context file is easier to keep from
drifting than two.
