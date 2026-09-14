# Model & Effort Routing

**Single source of truth:** this file owns all model/effort routing decisions.
Skills must not define their own model names, providers, or effort ladders.

## Model ladder

- **LOW** → Gemini 3.8 Flash — Low
- **MEDIUM** → Gemini 3.8 Flash — Medium
- **HIGH** → Gemini 3.8 Flash — High
- **VERY HIGH / unresolved high-risk** → Gemini 3.1 Pro — High

Gemini 3.7/3.6 Flash are fallback alternatives at the same effort level only
when the preferred model is unavailable/degraded/unsuitable.

Never recommend Claude, GPT, Sonnet, Opus, Gemini 2.x, Gemini 3.5, or invented
model/effort combinations.

## Effort is independent of the action tag

Tags provide starting priors only. Actual effort comes from evidence.

### LOW
A single well-understood location or trivial coordinated change with no
meaningful cross-module reasoning or behavioral risk.

LOW must never be selected merely because the final diff is small.

### MEDIUM
A few files/functions or a small cross-module flow where scope is well-defined
and reasoning is tractable.

### HIGH
Ambiguous root cause/design after investigation, cross-subsystem reasoning,
meaningful migration/backward-compatibility risk, security/data-integrity risk,
large refactor, concurrency complexity, or a meaningful failure at the previous
rung.

### VERY HIGH
Strong architectural tradeoffs or unresolved high-risk reasoning after HIGH.

## Classification priority

When signals conflict, classify in this order:

1. Security / safety / data-integrity risk
2. Architectural / cross-system complexity
3. Behavioral / compatibility / migration risk
4. Concurrency / distributed-state risk
5. Scope / file count
6. Final diff size

A higher-priority signal overrides a lower-priority signal.

Examples:
- One-line SQL injection fix → not LOW.
- One-file auth bypass → not LOW.
- Tiny race-condition/data-integrity fix → not LOW.
- Simple null-check bug → may remain LOW.
- Small cross-module feature → typically MEDIUM.

## Security floor

Any **confirmed security vulnerability** is at least MEDIUM effort.

Use HIGH when meaningful reasoning is required for:
- SQL/command injection;
- authentication;
- authorization;
- sensitive-data exposure;
- security-boundary failures;
- serious security/data-integrity interaction.

A confirmed security vulnerability is never Fast Path.

## Provisional → Confirmed effort

Before investigation:
- state provisional effort;
- state starting model;
- give one-line rationale.

After the initial investigation pass:
- state confirmed effort;
- update the recommended model if evidence changed the classification;
- state the evidence that confirmed or changed it;
- state the escalation trigger.

Reclassify immediately when investigation reveals security, data-integrity,
concurrency, migration, compatibility, architectural, or unexpected
cross-module risk.

## Risk is not effort

Effort measures reasoning/implementation complexity.
Risk measures consequence if wrong.

Do not use one as a substitute for the other. Verification risk overrides are
handled in `40-verification-risk.md`.

## Routing table

| Effort | Model | Default verification floor |
|---|---|---|
| LOW | Gemini 3.8 Flash — Low | TARGETED |
| MEDIUM | Gemini 3.8 Flash — Medium | COMPONENT when integration boundary matters |
| HIGH | Gemini 3.8 Flash — High | COMPONENT; FULL when blast radius/risk requires it |
| VERY HIGH | Gemini 3.1 Pro — High | FULL when unresolved high-risk reasoning remains |

These floors are not substitutes for the risk override.

## Escalation

**3.8 Flash Low → 3.8 Flash Medium → 3.8 Flash High → 3.1 Pro High**

Escalate because evidence requires it, not because a task merely sounds large.
Do not jump a straightforward LOW task directly to Pro.

Model selection is guidance only. The user manually selects the model and should
use Antigravity's actual usage/quota information as the source of truth for
remaining capacity.
