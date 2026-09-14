# Skill: LLM / RAG Change (`@llm`)

Global rules (model/effort routing, loop limits, verification, scope
control) live in `rules/workflow.md` — this file covers only the
investigation procedure for this tag.

Use for changes touching the retrieval-and-generation flow: `embedding.py`
→ `retrieval.py` → `llm.py` (Groq/Llama).

## CBM workflow

**trace flow → prompt/context → output handling → fallback**

## Investigation

1. Trace the flow from embedding through retrieval to the LLM call.
2. Find where the prompt is constructed and what retrieved context feeds
   into it.
3. Check how the LLM's output is parsed/validated before being returned —
   is malformed or unexpected output handled?
4. Check fallback behavior if the LLM call is slow, rate-limited, or
   errors.
5. Separate what's verifiable by code/tests from what needs a human
   judgment call (recommendation *quality* isn't something a unit test
   can confirm).

## Report

- Flow affected (embedding / retrieval / prompt / output parsing)
- Fallback/error handling
- What can be verified by tests vs. what needs manual spot-checking
- Proposed change

Prompt and output quality aren't caught by normal tests — after
implementing, spot-check a few real queries manually rather than relying
only on automated checks.
