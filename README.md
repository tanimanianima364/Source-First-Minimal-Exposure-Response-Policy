# Source-First Minimal-Exposure Response Policy

A response policy for AI chat assistants that prioritizes authoritative sources, complete answers, progressive disclosure of optional depth, and low cognitive load for the user.

## Prompt

- [PROMPT.md](PROMPT.md) — the single canonical policy, ready to copy as plain text into a chat application's custom instructions. The Japanese text stays under a 1,500-character repository budget, including newlines; it still directs the assistant to use the user's requested language.

## Use

Back up existing custom instructions, paste the complete contents of `PROMPT.md` into the custom instructions field, save, and verify that the full text was retained. Start a new chat and send your request normally. The policy remains subject to the application's higher-priority instructions and safety constraints.

- ChatGPT: use **Settings → Personalization → Custom instructions**. OpenAI recommends storing cross-chat preferences there and keeping task-specific details in the chat message. See [OpenAI's personalization guidance](https://learn.chatgpt.com/docs/prompting#personalize-chatgpt).
- Microsoft 365 Copilot Chat: use **Settings and more → Chat settings → Personalization → Custom instructions → Edit instructions**, then save. See [Microsoft's custom instructions guide](https://support.microsoft.com/en-us/microsoft-365-copilot/customize-how-microsoft-365-copilot-responds-to-you).

The 1,500-character budget is a project constraint, not a verified limit for every product. If the field is unavailable or cannot save the complete text, record that limitation instead of silently truncating it or treating a chat-message insertion as the same installation.

Within the policy, accuracy, completion of the requested scope, and material uncertainty take precedence; explicit user format, language, and scope come next. The four-block layout and length targets are defaults. Artifact-only requests omit extra headings and next directions; ordinary nontrivial answers retain useful next directions.

## Evaluation

[EVALS.md](EVALS.md) contains 13 fixed inputs and criteria for testing the policy saved in custom instructions. Send only the synthetic-data wrapper, case context, and request in the chat; do not paste the policy or grading criteria there. The external-search prohibition belongs only to those synthetic evaluation messages, never to the saved policy.

Compare with the historical policy only where it can be saved unchanged. If it does not fit, test against a separately labeled control with no project policy; this does not measure improvement over the historical policy. Grade completeness, evidence, and format before comparing brevity.

The target products are ChatGPT and Microsoft 365 Copilot Chat; no API key is needed. Saving custom instructions and model behavior have not been verified in either product. Browser access checks encountered HTTP 403 at ChatGPT and a sign-in page at `m365.cloud.microsoft`. The earlier region restriction at the personal Copilot site was not a Microsoft 365 test. Source authority, verification status, and research stopping criteria remain follow-up policy work; the related cases are diagnostics.
