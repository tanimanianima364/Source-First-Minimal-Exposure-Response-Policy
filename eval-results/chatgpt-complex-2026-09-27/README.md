# Complex synthetic follow-up — 2026-09-27

Four planned responses collected. All pass source fidelity and output format; each misses at least one mandatory content item in the frozen checklist, so all are provisional content/overall failures. The main design decisions are largely correct. This is not a general ranking of the policies; human confirmation and merge remain pending.

## Conditions

- A: `29ad511c447a5cb15c30cde7cb2d0a6b9aeb8218:PROMPT.md`; B: `01cd1decb47768bb5248bb70439f46f737a13ddb:PROMPT.md`. Both are Japanese. This compares the policies around conditional source attribution, not the isolated simplest-solution addition or English versus Japanese.
- The [plan](plan.json), exact [rollout memo input](rollout.txt), [incident JSON input](incident.txt), and [rubric](rubric.md) were saved locally before the first submission. They were not committed or published beforehand. Input preflight found that the composer removed the terminal LF; both fixture files were finalized without it before any send. The frozen inputs and criteria were not revised after seeing replies.
- Order: rollout A → rollout B → incident B → incident A, one response each, no regeneration, substitution, or selective retry. These two synthetic follow-ups are separate from the existing 16-input suite. The rollout task does not explicitly demand citation URLs; the incident JSON explicitly requires source identifiers and URLs. Neither difference between tasks is treated as an A/B effect.
- ChatGPT web in the existing Windows Chrome account, native UI Automation, with explicit `GPT-5.6 Sol` selection and **5.6 Extra High, 4 of 5** verified before every send. No Pro use. Backend revision and sampling settings are unavailable.
- New Personalized temporary chat per reply; selected radio and custom-instruction-permitting description checked. All eight controls OFF: memory, writing-style reference, fast answers, suggested prompts, recording-history reference, web search, Library search, and connector search. Controls checked after reload and before/after every reply. No synthetic URL was fetched, and no policy, grading criteria, or other case was placed in the chat message.
- Current supporting official documentation was opened on 2026-09-27: [Memory](https://help.openai.com/en/articles/8590148-memory-in-chatgpt) and [Temporary Chat](https://help.openai.com/en/articles/8914046-temporary-chat-in-chatgpt). Personalized temporary chats permit custom instructions; temporary chats do not create/update memories, while account controls suppress personalization reads. Internal provider behavior is not independently inspected.
- Each policy was saved only in custom instructions and verified after an unobstructed reload/readback, with exactly one terminal LF removed (A 1,344, B 1,402 saved characters). Preflight encountered unsaved-change dialogs and a record-history toggle that remained ON; these were resolved before the first send. Later condition changes also required waiting for save completion and canceling a premature reload dialog. No case was sent until policy and OFF-control checks passed.
- Raw replies preserve Copy output bytes, including CRLF and Markdown spacing. Character counts normalize CRLF to LF only; JSON validity is checked by parsing the complete unmodified reply. Automatic grades remain provisional until human review.

## Results

[Detailed per-item grades and supporting text](grades.md). P = pass; F = fail. All times JST, 2026-09-27. Copy times are not latency measurements. Character counts are descriptive only and include formatting.

| Response | Sent / copied | Content | Evidence | Format | Unmet content items | Characters | Model / mode |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [Rollout A](rollout-A.md) | 19:51:16 / 19:54:08 | F | P | P | 6 | 7422 | [Model](rollout-A-model.png) / [Mode](rollout-A-mode.png) |
| [Rollout B](rollout-B.md) | 19:55:43 / 20:00:14 | F | P | P | 1, 6 | 6348 | [Model](rollout-B-model.png) / [Mode](rollout-B-mode.png) |
| [Incident B](incident-B.md) | 20:01:08 / 20:02:18 | F | P | P | 3 | 2877 | [Model](incident-B-model.png) / [Mode](incident-B-mode.png) |
| [Incident A](incident-A.md) | 20:03:48 / 20:04:55 | F | P | P | 3 | 2824 | [Model](incident-A-model.png) / [Mode](incident-A-mode.png) |

- Both rollout replies reject the original plan, choose the existing local Python path, compare available time with implementation effort, reconcile output after interrupted publication, and treat shared-storage guarantees as unverified. A lacks several concrete acceptance tests; B adds missing-input and overlapping-start checks, but omits v3's 25 MB comparison figure. Both make backup restoration testing conditional instead of requiring the unconditional check in this rubric.
- Both incident replies reject the hotfix, correctly identify a 12,000-yen excess and unknown remaining batch state, stop blind retries, respect cancellation authority, and explicitly refuse an exactly-once guarantee. Both omit explicit preservation of original input and request/timeout logs. Both complete replies parse as JSON with exactly the requested keys and string/array-of-string types, and both include all six source URLs.
- No overall winner or brevity advantage is reported. The memo source pointers are traceable without URL repetition; the incident task explicitly requests URLs. Neither result erases the earlier case 10 attribution failure. The required acceptance set includes evaluator-selected checks: checklist omissions are not blanket claims that these otherwise useful answers are dangerous or incorrect.

## Integrity, restoration and remaining work

[controls.json](controls.json) preserves saved policy hashes, all 12 persisted/before/after control snapshots, raw response hashes, timestamps and restoration. [frozen-hashes.json](frozen-hashes.json) verifies the plan, rubric and two inputs stayed unchanged after their pre-submission finalization. It is a local integrity record, not an independently timestamped public preregistration. Raw copies match their temporary capture files byte for byte. The current PROMPT.md, existing 16 inputs/rubrics, and all historical response files are unchanged.

The original empty custom instructions and eight controls were restored and read back after reload: writing-style reference OFF, other seven ON. Power stayed non-Pro Extra High. Five owned windows were closed, with zero remaining after asynchronous closure completed. Other windows/history were not deleted. Restoration of settings does not promise recovery of memory lost when disabling it.

This is one response per task/condition on one product/model. It measures requested reasoning and constraint coverage in supplied synthetic material, not real production recovery, executed code, live documentation retrieval, statistical reliability, or language effects. It is not a full 16-input suite pass and does not establish that the conditional-attribution wording caused any omission. Human grade confirmation, remaining eligible evaluations, and merge remain pending.
