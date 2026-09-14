# Skill: New Feature (`@feature`)

Global rules (model/effort routing, loop limits, verification, scope
control) live in `rules/workflow.md` — this file covers only the
investigation procedure for this tag.

## CBM workflow

**architecture → search → trace → impact**

## Investigation

1. Understand the relevant architecture.
2. Search for existing related implementations.
3. Trace the current flow the feature will interact with.
4. Identify affected files, functions, routes, models, and components.
5. Check whether similar functionality already exists (see Existing Code
   First in the rules file).
6. Determine the smallest change that fits the existing architecture.

## Report

- Relevant architecture
- Existing related functionality
- Affected areas
- Implementation plan
- Potential side effects
