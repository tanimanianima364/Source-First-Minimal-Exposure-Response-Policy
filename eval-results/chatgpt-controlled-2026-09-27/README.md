# ChatGPT controlled case 9 run — 2026-09-27

Status: four new replies collected with controlled memory/settings; all grades remain provisional pending human confirmation. This is a new run under the prospective terminal-LF exception at protocol commit `50cfa6aff32f6ea1b4ed948c25c9a84d2212e6b6`, not a reclassification of the [earlier reference observations](../chatgpt-simplest-2026-09-27/README.md).

## Fixed conditions

- Product: ChatGPT web (`https://chatgpt.com/`), Pro account in regular Windows Chrome, operated through native Windows UI Automation.
- A: pre-addition `7fd8611599c92d87cf8a02ec427c74cddf3cc1cb:PROMPT.md`; B: `50cfa6aff32f6ea1b4ed948c25c9a84d2212e6b6:PROMPT.md`, whose policy body is identical to `852c495`. This isolates the simplest-sufficient-solution paragraph, not the historical English policy or a no-policy control.
- The [preregistration](preregistration.json) was recorded in PR #6 before the first submission: 9a/A → 9a/B → 9b/B → 9b/A, one response per condition. No regeneration, retries, or discarded replies. The frozen [case 9 rubric](../../EVALS.md#9-simplest-sufficient-solution-and-necessary-complexity) is unchanged.
- Every fresh window initially selected `Latest`. Before each submission, the evaluator explicitly selected radio option `GPT-5.6 Sol` and checked the resulting model menu: `5.6 Pro`, Power slider at its rightmost position. The UI did not expose a numeric effort value; this is not labeled “extra high.” Backend model version, sampling parameters, and output limit were unavailable. Cropped menu evidence: [9a/A](9a-A-model.png), [9a/B](9a-B-model.png), [9b/B](9b-B-model.png), [9b/A](9b-A-model.png).
- Policies were saved only in Settings → Personalization → ChatGPT instructions, reopened, and checked. The field removed exactly one terminal LF in both conditions; every other character matched. This transformation was predeclared under the prospective exception. A: 1,147 canonical / 1,146 saved characters; B: 1,283 / 1,282. The original instructions and the unchanged Nickname, Occupation, and More about you fields were empty.
- Canonical/saved SHA-256 for A: `d29df33f3ed087b613f11e8e6f8805f9b2836c4708c98e7647cad21ca5d5b8fd` / `24c00294306df1eaacb915f736cac977f31dedf139d1bf04ae7bbff580f4adfb`.
- Canonical/saved SHA-256 for B: `7ca67a34e23b3715440eb87045d90380da2a3efddafaaa724f5b974920fdaa7a` / `8e298db43576c24dc7fc0a9302b02fe578c3c5d39d1e4335a502476f0a8e7411`.
- Each input was the unchanged synthetic-data wrapper, exact fixture context, and selected request. Neither policy nor rubric was sent in the chat. Input SHA-256: 9a `addcf8ef0606d1ddfa97db8f81f2257e3443d793ed52054ea27fb9ce1cebe77b`; 9b `e5ea1bec419df6124c8288d5b763e934bdab4b36ec648a28ae804fd3c7a2f8cb`. Composer values were checked before sending.
- Each case used a new **Personalized temporary chat**; the mode was checked before submission. No temporary conversation was saved to history.

## Memory and retrieval controls

With explicit user authorization accepting possible memory loss, the evaluator saved the following controls OFF and reloaded the settings page. Persisted state was first verified at **15:06:34 JST**, before any submission:

| UI control | During all cases |
| --- | --- |
| Enable ChatGPT memory | Off |
| Reference my writing style | Off |
| Enable fast answers | Off |
| Enable suggested prompts | Off |
| Reference record history | Off |
| Web search | Off |
| Library search | Off |
| Connector search | Off |

The global memory switch suppresses memory-based personalization/past-chat use; Personalized temporary mode keeps custom instructions active while preventing creation or updates of memories from the evaluation. The combination is required: Personalized temporary mode alone can read existing memories. `Reference record history` concerns recording transcripts/notes and is not mislabeled as a past-chat control. Controls were rechecked around each response; settings switches were saved, not merely toggled in an unsaved form.

Supporting official documentation, checked 2026-09-27: [Memory in ChatGPT](https://help.openai.com/en/articles/8590148-memory-in-chatgpt), [Temporary Chat](https://help.openai.com/en/articles/8914046-temporary-chat-in-chatgpt), and [Custom Instructions](https://help.openai.com/en/articles/8096356-chatgpt-custom-instructions). Eligibility relies on controls plus documentation, not model self-report. Provider-internal behavior and hidden sampling settings are not independently observable.

## Provisional grades

All timestamps are JST (UTC+09:00), 2026-09-27; repeat 1 throughout. Capture timestamps record when Copy was used after completion, not response latency. Raw Markdown preserves the copied UTF-8 bytes, CRLF, and hard-break spaces, excluding UI chrome and thinking summaries.

| Case / condition | Submitted | Captured | Content | Evidence | Format | Overall |
| --- | --- | --- | --- | --- | --- | --- |
| [9a / A](9a-A.md) | 15:10:01 | 15:11:48 | Pass | Fail | Pass | Provisional fail |
| [9a / B](9a-B.md) | 15:14:03 | 15:19:20 | Pass | Fail | Pass | Provisional fail |
| [9b / B](9b-B.md) | 15:19:21 | 15:23:24 | Pass | Fail | Pass | Provisional fail |
| [9b / A](9b-A.md) | 15:24:32 | 15:28:10 | Pass | Fail | Pass | Provisional fail |

### 9a / A

Content: recommends “承認済みの表計算機能を手動で使う方法”, imports CSV, groups/sums by department, checks row coverage and duplicates, reconciles overall totals, spot-checks departments, and reopens the exported CSV. Conditional manual file records do not introduce an automation runner, product, custom code, or recurring workflow.

Evidence: **fails to identify the supplied document**. The full response does not name `Aggregation environment`, its revision, or its section; “この環境” is not a document identifier. Its capability claims otherwise agree with the fixture and its checks are proposed, not claimed executed.

Format: Japanese, recommended approach first, no executable code. Inline filenames and an equality check are not code implementations.

### 9a / B

Content: recommends “インストール済みの表計算機能を手動で使う方法”, imports and checks all 50 data rows, groups/sums departments, checks department coverage and overall totals, spot-checks groups, and rereads the CSV. It explicitly does not add the runner. Optional manual file retention stays within the supplied environment.

Evidence: **fails to identify the supplied document**, with no document title, revision, or section in the full reply. Available capabilities and proposed checks are otherwise distinguishable; no executed validation is claimed.

Format: Japanese, approach first, no executable code. Both 9a replies fail an evidence gate, so no brevity comparison is made for this pair. The shared failure does not show an improvement or a new regression caused by the added paragraph.

### 9b / B

Content: uses the approved runner, one aggregation job, and the shared folder. Preserves unattended scheduling, retained execution logs, and role-based input/work/output permissions. A stable batch ID, input/output hashes, staged output plus manifest, and atomic non-replacing publication implement retry safety rather than assuming the runner provides it. The response explicitly handles “確定出力公開後、成功ログ記録前” by validating the committed result and skipping another write. Tests cover expected totals/counts, unattended execution, partial failures, post-publication crashes, recorded errors/log retention, and denied unauthorized access. It makes atomic publication an unverified acceptance condition, not an established folder capability. No added product or speculative distributed system is prescribed.

Evidence: **fails document identification**. “提供された環境説明” does not name `Aggregation environment` or its revision/section. The response otherwise distinguishes known capabilities from its proposed implementation and does not claim completed tests or invent a retention duration or measured performance. Its early exactly-once statement is explicitly qualified by the later “重要な成立条件” and concluding acceptance condition.

Format: Japanese with the recommended three-component approach first. Fenced blocks show a system diagram, a batch-ID example, and an output layout, not executable code; the frozen case 9 format rule does not prohibit such illustrative blocks.

### 9b / A

Content: uses the approved runner, one batch script, and the existing shared folder with unattended scheduling, retained logs, and role-based permissions. Stable batch identity, immutable input/rule claims, deterministic output, atomic non-replacing publication, and validation of an already committed output implement retry safety. “出力はあるが完了記録がない” is explicitly handled by checking the output and repairing only the completion record. Acceptance tests cover totals/counts, scheduling, partial writes, crashes immediately after publication, recorded failures, and denied unauthorized operations. Atomic folder operations are explicitly unverified adoption conditions. No added product or speculative distributed system is required.

Evidence: **fails document identification**. The opening refers to “提示された revision r1”, acknowledging the revision, but never names the environment document or its section. This is partial source information rather than identification of the supplied `Aggregation environment` document. The remaining capability/design distinction is maintained; no completed validation, measured performance, or concrete retention duration is invented. The log-retention test's “保存期間後も検索” is imprecise relative to its surrounding requirement to retain logs for the necessary period; it does not state a fictitious known duration.

Format: Japanese, configuration first, no executable code; fenced diagrams, paths, and identifier formulas illustrate the proposed design.

## Interpretation and outstanding work

The provisional outcome is a shared source-identification failure under both policies on both inputs. These observations do not demonstrate an improvement or a new regression from the simplest-solution paragraph. Neither pair clears all gates, so no brevity winner or aggregate comparison is reported. The required-content passes support only these particular proposed solutions, not a general reliability claim.

Human grade reconciliation remains pending: the user explicitly said they had not checked the earlier grades themselves. This run does not establish a full 15-input pass or Microsoft 365 Copilot performance; no new Copilot reply was collected. Keep the PR unmerged pending its existing human-confirmation and evaluation conditions. Any source-identification fix and rerun must be recorded as a new candidate/run, without replacing these answers or relaxing the frozen rubric.

## Restoration and record integrity

[Control snapshots and submission/capture times](controls.json) preserve all eight flags before and after each reply. Model-menu crops above contain only the menu, excluding personal sidebar/history information.

At **15:29:43 JST**, after saving and reloading, the six switches explicitly changed from ON were verified ON again: Enable ChatGPT memory, Enable fast answers, Enable suggested prompts, Reference record history, Web search, and Connector search. Reference my writing style remained OFF; Library search was ON after restoration of the parent controls. Those two dependent controls were observed OFF after memory was disabled, but their pre-disable values were not independently captured or directly changed; no claim of an independent original-state check is made for them. At **15:30:00 JST**, reopening the editor verified the original empty instructions and all three unchanged empty profile fields. Only evaluation-owned browser windows were closed. Restoring switches does not demonstrate restoration of any information lost through disabling memory; the user had explicitly accepted that possible loss.

SHA-256 of the exact copied reply files:

- `9a-A.md`: `1c7f0e1556c2c46a8e79f152e07c11c4e7d6d991fb94d309faae98fa0afbd7e5`
- `9a-B.md`: `b0e2c5b3dd89a688b5dab28422f2f973a212f113e4121b10fe8ec4832f46bcb7`
- `9b-B.md`: `ae16785d9093e29723a34ea36a28295044005d27e5130a1a6c34ef129239ae0b`
- `9b-A.md`: `3e4080eb1d256c8d96ce7a2c55702607ae2ca488a1f0710adbe2f59d2edee645`

Record checks passed: private Copy captures and committed artifacts are byte-identical; exact fixture inputs, saved-policy normalization, eight pre/post control values, policy/rubric preservation, local links, and annotation whitespace were checked. Raw CRLF and Markdown hard-break spaces were intentionally preserved. One Tier 1 read-only review independently checked the four grades and record consistency with no actionable findings; it is not human confirmation or an independent browser rerun.

## Subsequent human feedback

After opening the four replies and grading record, the user said “Bの方が全体的にいいと思います” and authorized proceeding with a source-identification fix. This is a qualitative preference for B over A, not confirmation of every rubric grade, a claim that B passed, or merge approval. Raw replies and provisional grades above remain unchanged.
