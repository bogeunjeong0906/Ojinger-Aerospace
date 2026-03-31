---
name: clarification-fallback
description: "Ask the user for clarification only when missing information materially blocks a stable implementation, while preventing question overuse through batching and fallback defaults. If the user cannot answer, follow repository policy first and industry standards second."
argument-hint: "blocking ambiguity and default path"
user-invocable: true
---

# Clarification and Fallback

Use this skill when the request contains ambiguity that could materially change behavior, safety, compatibility, or acceptance criteria.

## Goals

- Prevent broken outcomes caused by guessing through major ambiguity.
- Prevent endless question loops for details that can be resolved from policy or standard practice.
- Make fallback assumptions explicit and defensible.

## Ask-or-Assume Rule

- Ask for clarification only when the missing information materially blocks a stable implementation.
- Do not ask for cosmetic or low-impact preferences that can be resolved safely from project policy or established conventions.
- Batch related questions into one concise clarification round instead of asking repeatedly.

## Authority and Routing

- In the current TAS-only workspace, TAS asks the user directly when clarification is genuinely required.
- If a future multi-agent workflow is restored, non-user-facing agents should surface blocking ambiguities to the user-facing coordinator instead of asking directly.
- Always include a recommended default path so one clarification round is enough.

## Fallback Order

1. Use explicit user requirements when they are available and clear.
2. If the user cannot answer or the answer is incomplete, follow repository policy, local conventions, and documented project standards.
3. If the repository does not define the matter, follow industry-standard practice.
4. Record the chosen assumption in the active artifact instead of hiding it.

## Question Budget Guardrails

- Prefer one bundled clarification round per materially blocked decision set.
- If the request can proceed safely using project policy or industry standard, do not ask.
- If the user reply is still insufficient after one round, stop looping and proceed with the fallback order above unless the change would be unsafe or prohibited.

## Typical Cases That Justify Asking

- The target behavior is ambiguous enough to change functionality.
- Compatibility or migration expectations are undefined.
- Security, privacy, or data-handling requirements are unclear.
- Multiple plausible implementations exist with materially different tradeoffs and no project rule resolves the choice.

## Typical Cases That Should Not Trigger Asking

- Naming or phrasing details that are covered by local style.
- Minor formatting choices.
- Low-risk defaults already established elsewhere in the repository.

## Output Template

Use [assets/clarification-decision.template.md](./assets/clarification-decision.template.md) when recording whether the task asked the user or used a fallback assumption.
