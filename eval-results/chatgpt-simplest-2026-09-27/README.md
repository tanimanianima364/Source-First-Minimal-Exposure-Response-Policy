# ChatGPT simplest-solution reference observations — 2026-09-27

Status: four full replies collected; each provisionally passes the required-content, evidence, and format gates. Grades below are AI-assisted grades against the frozen [case 9 criteria](../../EVALS.md#9-simplest-sufficient-solution-and-necessary-complexity) at `852c495bb6df67ac485d2dc26ad3ee666d8b4775`. Human confirmation is pending.

These are **memory-uncontrolled reference observations**, excluded from controlled comparisons, improvement/regression judgments, brevity comparisons, and aggregate comparisons. They do not establish a full 15-input suite pass or satisfy the PR's measured-comparison merge condition. The [earlier unsuccessful browser attempt](../simplest-solution-2026-09-27.md) remains a separate record.

## Conditions and installation

- Product: ChatGPT at `https://chatgpt.com/`, the user's regular Windows Chrome profile, operated through Windows UI Automation. The account menu displayed `Pro`.
- Model selection: `Latest` was selected when inspected after 9a/A; no model radio option was changed. Attempts to inspect the Power menu did not expose a verifiable value, so constancy of that control was not established. The resolved model/version and sampling controls were also unavailable. This run must not be labeled with the user's earlier `GPT-5.6 / extra high` report for case 2a.
- A: pre-addition `7fd8611599c92d87cf8a02ec427c74cddf3cc1cb:PROMPT.md`; B: candidate `852c495bb6df67ac485d2dc26ad3ee666d8b4775:PROMPT.md`. This is separate from historical `682f08a` and no-policy controls.
- Both policies were installed only in Settings → Personalization → ChatGPT instructions. The saved field was reopened and checked before use. Each lost exactly its final LF: A saved 1,146 characters; B saved 1,282. The rest of each body matched exactly. This does not establish the protocol's strict unchanged-text installation condition.
- Canonical/saved SHA-256 for A: `d29df33f3ed087b613f11e8e6f8805f9b2836c4708c98e7647cad21ca5d5b8fd` / `24c00294306df1eaacb915f736cac977f31dedf139d1bf04ae7bbff580f4adfb`.
- Canonical/saved SHA-256 for B: `7ca67a34e23b3715440eb87045d90380da2a3efddafaaa724f5b974920fdaa7a` / `8e298db43576c24dc7fc0a9302b02fe578c3c5d39d1e4335a502476f0a8e7411`.
- Original project instructions and the Nickname, Occupation, and More about you fields were empty. The three profile fields were left unchanged. No personalization or tool switches were changed.
- `Enable ChatGPT memory` and `Reference record history` were ON. The latter concerns recording transcripts/notes, not proof of suppressed past-chat reference. Memory controls were not disabled or cleared to obtain eligibility.
- Each input used a separate new **Personalized temporary chat**; that mode was checked before submission. The UI stated that it can reference memory, plugins, and custom instructions. [OpenAI's temporary-chat documentation](https://help.openai.com/en/articles/8914046-temporary-chat-in-chatgpt), checked on 2026-09-27, says Personalized temporary chats can use existing memory/custom instructions and do not create or update memories. Thus custom instructions were active, but memory-read suppression was not established. No temporary conversation was saved into history by the evaluator.
- Predeclared selection: 9a and 9b, one response per condition, order 9a/A → 9a/B → 9b/B → 9b/A. The two B requests overlapped in generation; the policy remained B until both completed. No answer was regenerated or discarded.
- Each composer value was checked against the prepared wrapper + exact case context + selected request before sending. No policy or rubric appeared in the submitted message. Input SHA-256: 9a `addcf8ef0606d1ddfa97db8f81f2257e3443d793ed52054ea27fb9ce1cebe77b`; 9b `e5ea1bec419df6124c8288d5b763e934bdab4b36ec648a28ae804fd3c7a2f8cb`.
- Full final responses were captured with ChatGPT's Copy button after completion. The linked Markdown files preserve the copied UTF-8 text, including CRLF and Markdown hard-break spaces. UI chrome and displayed thinking summaries are not part of the response artifacts. Capture times are observation times, not latency measurements.
- This resumed run covers ChatGPT only. No new Copilot response was collected; its earlier personal-account access failures are preserved in the earlier record.
- Restoration: at 14:40:18 JST, reopening the settings field confirmed the original empty instructions and all three unchanged, empty profile fields. Memory and Reference record history were rechecked ON at 14:40:00 JST. No memory was deleted or personalization switch changed by the evaluator.

## Responses and provisional grades

All times below are JST (UTC+09:00), 2026-09-27; repeat number is 1 throughout.

| Case / condition | Submitted | Captured | Required content | Evidence | Format | Overall |
| --- | --- | --- | --- | --- | --- | --- |
| [9a / A](9a-A.md) | 14:21:31 | 14:23:09 | Pass | Pass | Pass | Provisional pass |
| [9a / B](9a-B.md) | 14:28:55 | 14:31:52 | Pass | Pass | Pass | Provisional pass |
| [9b / B](9b-B.md) | 14:29:44 | 14:33:49 | Pass | Pass | Pass | Provisional pass |
| [9b / A](9b-A.md) | 14:35:00 | 14:39:28 | Pass | Pass | Pass | Provisional pass |

### 9a / A

- Required content: chooses the installed spreadsheet, imports and groups/sums by department, checks row coverage and totals, and rereads the exported CSV. “既存のスプレッドシートで手動集計” and “元データの対象数値の全体合計 ＝ 部署別合計をすべて足した値” support the grade. No runner, added product, custom code, or recurring workflow is recommended; no clarification blocks the answer.
- Evidence: identifies “提示資料「Aggregation environment」revision r1、section「Available capabilities」”. The detailed checks are proposed user actions, with no invented built-in retry guarantee, retention period, benchmark, or claim of executed validation.
- Format: Japanese, recommended approach first, no executable code. Inline output filenames and the total-equality check are not code implementations.

### 9a / B

- Required content: chooses “導入済みの表計算機能を手動で”, covers import, department grouping and sum, verifies all rows, checks overall and per-department totals, and reopens the exported CSV. “欠落・重複なく取り込まれているか確認” supports row coverage. No unnecessary system or prerequisite clarification is introduced.
- Evidence: names the supplied document/revision/section and ties the three available spreadsheet capabilities to it. Cleanup and verification are instructions to perform, not claims that they were already run or are unspecified built-in features.
- Format: Japanese, approach first, no executable code; the verification steps supply the next actions.

### 9b / B

- Required content: selects “既存の承認済み自動実行基盤＋集計スクリプト＋既存共有フォルダー”, with a schedule, durable runner logs, and role-limited input/work/output access. A stable processing key, input/version checks, nonpublic staging, one-time atomic publication, and checking committed output on retry explain duplicate prevention. It explicitly does not rely on the runner supplying that guarantee.
- Verification covers expected department totals/counts, unattended scheduled execution, retries after partial writes and after publication but before the success log, recorded failures/log retention, and rejected unauthorized read/write/delete operations. In particular, “出力確定後、成功ログを残す前に異常終了” is covered by checking the committed result. No unapproved product or distributed system is required.
- Evidence: identifies the fixture and labels the rest as a design proposal. “これらは共有フォルダーの既知の機能ではなく、確認が必要な条件です” correctly limits atomicity/durability claims; adopting the proposal is conditional on verifying those properties. No retention duration, measured performance, or executed verification is invented.
- Format: Japanese, recommended configuration first, no code. Its implementation detail preserves the explicitly required failure behavior; the frozen rubric does not impose a length cap.

### 9b / A

- Required content: selects the existing runner, one aggregation/retry-control script, and the shared folder, with scheduled unattended execution, retained logs, and role-based permissions. “重複防止はスクリプトの設計と保存先の保証を組み合わせて実現” is implemented through a stable business-date key, input/output checks, staged output, atomic non-replacing publication, and skipping valid committed output on retries.
- Verification covers known totals/counts, unattended scheduling, partial writes, a crash after output publication but before success logging, failure-log persistence, and unauthorized input/output access. The explicit “確定直後の障害” test requires no additional output, append, or overwrite on retry. No new product or speculative distributed system is required.
- Evidence: identifies the supplied document/revision/section and calls the retry scheme and tests design proposals. It explicitly marks atomic/durable publication and 50,000-row performance unverified, supplies acceptance checks, and invents no retention period or executed validation.
- Format: Japanese, proposed minimum configuration first, no executable code; the tests and adoption conditions give concrete next steps.

## Artifact integrity

SHA-256 of the exact copied response files:

- `9a-A.md`: `eca5e629e46f8fb9c69697416f633c6232f86745f538ee1b61f98b60ca21f280`
- `9a-B.md`: `66e502d7f5a6920fc123dfab6b59af090807ffcfb2f784c0172a6b73f8e758b2`
- `9b-B.md`: `2252525aae624a54645c0f65ee710664fb6621a34488b75118529043d2462b29`
- `9b-A.md`: `65cbe304969549dcc85ea35a210e18d936147af741d0373213a8e39b3b3da6d2`

Record checks passed: raw-file byte/hash equality, exact fixture inputs, saved-policy normalization, unchanged policy/rubric, local links, and annotation whitespace. Raw Markdown hard-break spaces and CRLF were preserved rather than reformatted. One Tier 1 read-only agent review checked all four grades and the stated limitations with no actionable findings; it is not human grade confirmation.

## Remaining work

Human grade reconciliation, an eligible controlled comparison, Copilot response collection, and the full suite remain outstanding. Per-response rubric passes in this record are not evidence that adding the policy paragraph improved behavior. Keep the PR unmerged under its existing measured-comparison condition.
