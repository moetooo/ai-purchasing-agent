# Context & Session Efficiency

## Context order

Start with the smallest useful context:

1. target file/symbol;
2. direct callers/callees/imports;
3. relevant tests/configuration;
4. broader architecture only when required.

Use the relevant Skill instead of reading unrelated task procedures.

## Search/CBM discipline

Use the smallest relevant CBM operation:

**Search → targeted Trace → exact Snippet → Impact**

Use Architecture when placement/system design is genuinely in question.
Use Runtime Traces only when static evidence cannot establish the required fact.

### Bounded investigation

**Pass 1:** targeted investigation using the relevant Skill's CBM workflow.

**Pass 2:** only if evidence is insufficient; investigate the specific missing
fact, not the whole repository again.

After Pass 2, if ambiguity remains:
- escalate the model, or
- split the task.

Do not continue open-ended exploration.

## Do not over-parallelize

Prefer sequential evidence gathering when one result determines the next step.
Do not launch several searches merely to confirm a conclusion the existing
evidence already supports.

Parallel investigation is appropriate only when sub-questions are genuinely
independent and concurrency materially speeds useful progress.

## Avoid repeated context

Reuse established evidence in the current task.
Do not:
- repeat identical searches;
- reopen unchanged files without a new reason;
- rescan the repository after a local verification failure unless evidence points to a broader issue;
- reread entire workflow files when a section/Skill is sufficient.

Navigation should use section names and Skill names, not fixed line numbers.

## Repository exclusions

Keep `.antigravityignore` current. Exclude irrelevant large/generated content
such as:

- `.venv/`
- `__pycache__/`
- `*.pyc`
- `dist/`
- `build/`
- `coverage/`
- generated files
- logs and large dumps
- model/index/cache artifacts such as `*.faiss`, `*.index`, `dump.rdb` when not relevant

Adapt exclusions to the real repository.

## Terminal efficiency

Use the narrowest command that answers the current question.

Do not automatically run:
- full builds;
- full test suites;
- package-manager operations;
- repository-wide scans.

Run them when scope, risk, or delivery requirements justify them.
Do not rerun a command that already produced the needed evidence unless
something material changed.
Never skip a command that correctness genuinely requires just to save quota.

## Context compression

Summarize/compress supporting material such as long logs, repetitive docs,
historical discussion, or large retrieved text.

Do not aggressively compress source code that will be modified; implementation
detail is more valuable there than the context savings.

## Sessions

Start a new session for a genuinely independent task.

Keep the same session for:
- follow-up questions;
- failures from the same task;
- small corrections;
- continued implementation of the same approved plan.

Do not reset context merely to reset; rediscovering the same repository facts
wastes agent work.

Close/remove irrelevant open files when they are no longer useful to the task.
