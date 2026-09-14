# Skill: API & Database (`@api`, `@database`)

Global rules (model/effort routing, loop limits, verification, scope
control) live in `rules/workflow.md` — this file covers only the
investigation procedure for these two tags.

## `@api`

### CBM workflow

**routes → search → trace → callers → impact**

Check: **Route → Request/Response Models → Service → Database/External
Services → Frontend Callers**

### Investigation

1. Find the API route.
2. Find request and response models.
3. Find the service implementation.
4. Find frontend/API callers.
5. Check validation and error handling.
6. Trace the current request flow.
7. Identify compatibility risks.

### Report

- Current API flow
- Affected components
- Required changes
- Compatibility risks
- Implementation plan

## `@database`

### CBM workflow

**schema → search → trace → callers → impact**

Check: **Model/Schema → Queries → Services → API → Frontend**

### Investigation

1. Find the relevant database model/schema.
2. Find queries using it.
3. Find services consuming those queries.
4. Trace affected data flow.
5. Identify API/frontend consequences.
6. Identify migration or compatibility issues.
7. If the model touches a pgvector column, check whether the change
   affects embedding dimensions, indexes, or existing stored vectors.

### Report

- Current schema/data flow
- Affected queries
- Affected services
- API/frontend impact
- Migration concerns — if a schema migration is required, say so
  explicitly (migration file, backward compatibility, rollback) before
  implementing

A real migration or backward-compatibility risk here is a Classification
Priority signal (rules file, Section 3) — it reclassifies the task
upward regardless of how small the code change looks.
