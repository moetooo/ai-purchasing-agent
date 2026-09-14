# Skill: Security Fix (`@security`)

Global rules (model/effort routing, loop limits, verification, scope
control) live in `rules/workflow.md` — this file covers only the
investigation procedure for this tag. In particular, see the rules
file's **Security Rule**: a confirmed vulnerability is never LOW effort
and never qualifies for the Fast Path, regardless of diff size.

## CBM workflow

**search → trace → data flow → impact**

Follow the relevant data from: **Entry Point → Validation/Sanitization →
Processing → Database/External Service → Output**

## Investigation

Identify:

- Where the data enters
- How it is validated
- How it is transformed
- Where it is stored/sent
- Where it is ultimately used
- Potential attack or exposure paths

Do not modify files during investigation.

## Report

- Root cause
- Safest minimal fix

State explicitly which category the vulnerability falls into (injection,
auth, authz, sensitive-data exposure, boundary failure, or other) — this
determines whether the confirmed effort is MEDIUM or HIGH per the rules
file's Security Rule.
