# Source-First Minimal-Exposure Response Policy

A response policy for AI chat assistants that prioritizes authoritative sources, complete answers, progressive disclosure of optional depth, and low cognitive load for the user.

## Prompt

- [PROMPT.md](PROMPT.md) — the canonical policy. It keeps simple answers compact, requires all material findings within the requested scope, and defers optional depth to sources. Requested summaries, explanations, and translations still belong in the answer.

## Use

Add the contents of `PROMPT.md` to the assistant's instructions, subject to that environment's higher-priority instructions and safety constraints. Keep evaluation material separate from the policy.

Within the policy, accuracy, completion of the requested scope, and material uncertainty take precedence; explicit user format, language, and scope come next. The four-block layout and length targets are defaults. Artifact-only requests omit extra headings and next directions; ordinary nontrivial answers retain useful next directions.

## Evaluation

[EVALS.md](EVALS.md) contains fixed inputs, pass criteria, and a comparison protocol for the baseline at `682f08ad68a1ec03a57ecec4e0ed8ee5b2893472` and a candidate revision. Grade completeness, evidence, and format before comparing brevity.

The target environments are the ChatGPT and Microsoft Copilot chat applications; no API key is needed. Browser access checks could not reach either chat, so model comparison remains pending. Static review alone does not establish model compliance. Source authority, verification status, and research stopping criteria remain follow-up policy work; the related evaluation cases are diagnostics.
