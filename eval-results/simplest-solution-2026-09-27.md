# Simplest-solution evaluation attempt — 2026-09-27

Status: static checks passed; behavioral evaluation **not run to completion**. No model response was collected, so no case is graded and no improvement/regression claim is made.

## Frozen comparison

- Baseline: `7fd8611599c92d87cf8a02ec427c74cddf3cc1cb:PROMPT.md` (pre-addition, 1,147 characters).
- Candidate: `19c08d56cfa624765159e2a01ef58aa895eca5f7:PROMPT.md` (1,283 characters).
- Candidate SHA-256: `7ca67a34e23b3715440eb87045d90380da2a3efddafaaa724f5b974920fdaa7a`.
- Cases: [9a and 9b](../EVALS.md#9-simplest-sufficient-solution-and-necessary-complexity), one response per condition. Planned order: 9a baseline, 9a candidate, 9b candidate, 9b baseline.
- Each prepared message contains only the shared synthetic-data/no-external-search wrapper, the exact case context, and the selected user request. No policy text or rubric is included.

## Static checks

- Candidate: 1,283 Unicode characters and 1,283 UTF-16 code units, including newlines; under the repository's 1,500-character budget.
- Removing exactly the added paragraph reproduces the baseline policy byte for byte.
- The original 13 inputs and grading criteria are unchanged; the suite now has 15 inputs.
- Local Markdown links and `git diff --check` passed.
- A Tier 1 read-only review found no in-scope blockers in the policy, paired cases, or comparison protocol. This is not a model evaluation.
- The synthetic fixtures do not test real-world research stopping behavior.

## ChatGPT access

The user reported enabling Chrome remote debugging and allowing the connection. The WebSocket connected, but Playwright initialization received no usable response and timed out, including a retry outside the sandbox. A Windows UI Automation fallback also failed with a WSL interop error. The cause was not established.

No ChatGPT custom instructions were changed and no case was submitted. Model/mode and memory eligibility were not verified in this attempt. At the end, the user confirmed switching Chrome remote debugging back OFF; that restoration was user-reported, not independently inspected.

## Copilot storage and access observation

- URL: `https://m365.cloud.microsoft/chat`, in the Windows evaluation Edge profile.
- Account: **personal Microsoft account**, confirmed by the user and the UI. This is separate from the planned work/school Microsoft 365 Copilot Chat comparison.
- Loaded composer mode: `自動` (Auto). The underlying model/version, sampling controls, and account tier were not established.
- Visible settings: custom instructions ON, saved memories ON, shared experiences OFF, ad personalization OFF, analytics OFF, web search ON. Past-chat reference suppression was not established.
- Any responses from these conditions would be **memory-uncontrolled reference observations**, excluded from controlled comparisons and aggregate improvement/regression judgments.
- Original custom instructions were empty. Both policy bodies were saved and checked by reopening the settings field. In both cases, the UI removed exactly the final LF: baseline 1,146 saved characters; candidate 1,282 saved characters. No instruction content was omitted. This normalization is recorded explicitly; this storage check does not establish the protocol's strict unchanged-text installation or controlled-comparison eligibility.

The first 9a baseline send attempt at **12:34:41 JST** encountered `セキュリティ チェックが必要です`. After the user reported completing that check, the page displayed `要求を完了できませんでした。更新して、もう一度お試しください。` Following that refresh instruction, one more send was attempted at **12:36:24 JST**, with the same request-failure message. No assistant reply or successfully posted conversation message was observed; no model response was retried or discarded.

The candidate was subsequently checked for settings storage only. It was not submitted for a model response. The original empty custom instructions were restored and the unsent fixture draft was cleared. Reopening settings confirmed the empty field and all six original switch values. Personalization switches were not changed.

| Case / condition | Outcome | Grade |
| --- | --- | --- |
| 9a / baseline | Two access/send attempts; no reply | Not graded |
| 9a / candidate | Not attempted after access failure | Not graded |
| 9b / candidate | Not attempted after access failure | Not graded |
| 9b / baseline | Not attempted after access failure | Not graded |

## Remaining work

Collect eligible full replies under verified installation and memory conditions, preserve the exact saved text and execution metadata, and reconcile provisional grades with a human. The personal-account access attempt is not a substitute for the planned product comparison. Full-suite behavior, the new pair's behavior, and improvement over the baseline remain unverified. Keep the PR unmerged pending the required measured results and review approval.
