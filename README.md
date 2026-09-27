# Source-First Minimal-Exposure Response Policy

A response policy for AI chat assistants that prioritizes authoritative sources, complete answers, the simplest sufficient solution, progressive disclosure of optional depth, and low cognitive load for the user.

## Prompt

- [PROMPT.md](PROMPT.md) — the single canonical policy, ready to copy as plain text into a chat application's custom instructions. The Japanese text stays under a 1,500-character repository budget, including newlines; it still directs the assistant to use the user's requested language.

## Use

Back up existing custom instructions, paste the complete contents of `PROMPT.md` into the custom instructions field, save, and verify that the full text was retained. Start a new chat and send your request normally. The policy remains subject to the application's higher-priority instructions and safety constraints.

- ChatGPT: use **Settings → Personalization → Custom instructions**. OpenAI recommends storing cross-chat preferences there and keeping task-specific details in the chat message. See [OpenAI's personalization guidance](https://learn.chatgpt.com/docs/prompting#personalize-chatgpt).
- Microsoft 365 Copilot Chat: use **Settings and more → Chat settings → Personalization → Custom instructions → Edit instructions**, then save. See [Microsoft's custom instructions guide](https://support.microsoft.com/en-us/microsoft-365-copilot/customize-how-microsoft-365-copilot-responds-to-you).

The 1,500-character budget is a project constraint, not a verified limit for every product. If the field is unavailable or cannot save the complete text, record that limitation instead of silently truncating it or treating a chat-message insertion as the same installation.

Within the policy, accuracy, completion of the requested scope, and material uncertainty take precedence; explicit user format, language, and scope come next. The four-block layout and length targets are defaults. Artifact-only requests omit extra headings and next directions; ordinary nontrivial answers retain useful next directions.

## Evaluation

[EVALS.md](EVALS.md) contains 15 fixed inputs and criteria for testing the policy saved in custom instructions. The added pair tests reusing existing capabilities for a one-off task and preserving necessary operational requirements for recurring work. Send only the synthetic-data wrapper, case context, and request in the chat; do not paste the policy or grading criteria there. The external-search prohibition belongs only to those synthetic evaluation messages, never to the saved policy.

Compare with the historical policy only where it can be saved unchanged. If it does not fit, test against a separately labeled control with no project policy; this does not measure improvement over the historical policy. Grade completeness, evidence, and format before comparing brevity.

To isolate the simplest-sufficient-solution addition, compare against the unchanged policy at `7fd8611599c92d87cf8a02ec427c74cddf3cc1cb`, following the focused comparison in `EVALS.md`. Keep this comparison separate from the historical and no-policy controls.

Controlled comparisons require custom instructions to remain active while memory reads, memory creation/updates, and past-chat reference are suppressed throughout both conditions. Fixed settings or a temporary-chat label alone are insufficient. Results without verified memory controls are separate **memory-uncontrolled reference observations**, excluded from improvement/regression judgments and aggregate comparisons; see the eligibility rules in `EVALS.md`.

The target products are ChatGPT and Microsoft 365 Copilot Chat; no API key is needed. The [source-identification follow-up](eval-results/chatgpt-source-id-2026-09-27/README.md) tests a 1,345-character clarification: source omission persists, although JSON/translation-only checks pass. A separate short instruction also was not followed, so instruction delivery versus model noncompliance remains unresolved. The clarification is not a demonstrated fix. A [new controlled ChatGPT case 9 run](eval-results/chatgpt-controlled-2026-09-27/README.md) collected four replies with memory controls and per-chat model/Power checks: all provisionally pass content/format but fail source identification. No improvement is demonstrated, and human grade confirmation remains pending. The [resumed ChatGPT run](eval-results/chatgpt-simplest-2026-09-27/README.md) preserves four case 9 replies with provisional per-response passes, separately labeled as memory-uncontrolled reference observations; no improvement or full-suite claim follows. The [earlier browser attempt](eval-results/simplest-solution-2026-09-27.md) checked policy storage in a personal Microsoft account, separately from the planned work/school comparison, but obtained no model replies because of access/send failures. Source authority and verification status remain follow-up policy work; the related cases are diagnostics. The policy now bounds additional research to unresolved points affecting the decision; these synthetic fixtures do not validate that behavior in live research.
