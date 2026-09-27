# Research and coding comparison — 2026-09-27

Four first replies collected and independently checked. These tasks are separate from the 16-input suite; grades remain provisional pending human confirmation.

A is Japanese policy `29ad511c447a5cb15c30cde7cb2d0a6b9aeb8218`; B is Japanese policy `01cd1decb47768bb5248bb70439f46f737a13ddb`. Fixed order: research A, research B, coding B, coding A, once each, no regeneration or answer repair. Same GPT-5.6 Sol / Extra High 4 of 5, never Pro. Fresh Personalized temporary chats; full policy saved/reloaded/read back with exactly one terminal LF removed. The exact [research](research.txt) and [coding](coding.txt) messages remove only the prepared tasks' terminal LF to match composer retention. [Rubric](rubric.md) is copied unchanged from the prepared evaluator-only version.

Research enables web search, with the other seven controls OFF. Coding disables all eight controls. The same documented [memory eligibility](../../EVALS.md#chatgpt-and-microsoft-365-copilot-chat-runs) and instruction-preserving mode checks as prior same-day runs apply. Each condition has persisted/before/after snapshots in [controls.json](controls.json), including policy hashes and submission/copy timestamps. The same-day control interpretation is documented in the [preceding run](../chatgpt-nonpro-2026-09-27/README.md); it is not an inspection of hidden provider state. No rubric, reference answer or harness enters the evaluated chats. Candidate code is executed separately in an offline disposable environment, never against this repository or account data.

Live search results are not fixed; this is an end-to-end research comparison, not a causal estimate. Code execution reported by the chat is recorded separately from evaluator execution. Backend sampling/revision and internal tool execution are not independently observable. Grades remain provisional until human confirmation; existing failures and merge hold remain.

## Pre-collection validation

[Independent coding checks](checks/README.md) passed on a private reference; three seeded faults were detected. A scheduling-dependent false failure H1 was fixed before any submission: no overlapping snapshot observation is explicitly skipped/unverified, while the final-state check remains. The parent reproduced the forced-completion schedule and a corrupted-final-state countercheck; the reviewer verified only this finding after the single discovery pass. [Plan](plan.json) and [hash manifest](frozen-hashes.json) were finalized locally before the first send; this is not independently timestamped public preregistration.

The first preflight model selection displayed Pro; the send guard prevented a request. It was changed to Extra High4/5 and checked again before submission. Some settings also required a second toggle to reach the target state. A later coding-A menu timing check also stopped before submission; reopening the menu verified Extra High before sending. No case was sent with Pro or mismatched settings. UI progress observations, when available, are only samples of displayed search/status messages, not a complete retrieval trace.

## Research observations

Both first replies are saved. They recommend a fixed-model two-branch investigation followed by evidence verification, include counterevidence, distinguish oracle availability from actual selection, and propose a budgeted falsifiable pilot. Their paper sets differ; no mandatory source list was supplied.

| Reply | R1 discovery | R2 evidence | R3 synthesis | R4 arithmetic | R5 decision | R6 pilot |
|---|---|---|---|---|---|---|
| [A](research-A.md) / [checks](research-checks-A.md) | pass | partial | pass | pass | pass | pass |
| [B](research-B.md) / [checks](research-checks-B.md) | pass | pass | partial | pass | pass | pass |

A's checked central numbers and table/figure IDs match, but several PDF page locators are one page early. B's detailed comparisons are useful, but its closing categorical claim against longer single-agent execution and its causal interpretation of a possible C win exceed the evidence. These partial grades describe specific precision/interpretation problems, not fabricated papers or general inability to reason. Neither gets a full six-dimension task pass. Grades are provisional and have not been confirmed by the user.

The verification notes link to the actual primary versions independently opened by the evaluator. Native ChatGPT citations are copied as nonportable `:chatgpt-content-reference` tokens; A also supplies six ordinary versioned links, whereas B's clipboard copy relies on native citations. We preserve this transport limitation without changing raw replies or treating it as missing citations in the original UI. The visible-text and sampled progress files are bounded UI observations, not complete retrieval logs or proof of every reported document fetch.

## Coding observations

[Detailed criterion grades and source/test evidence](coding-grades.md). Two Python files per answer were extracted without changing their bytes. All runs below use the same frozen offline evaluator and Python 3.12.14 / SQLite 3.53.1.

| Reply | Independent checks | Author tests run by evaluator | C1 | C2–C6 | Full task |
|---|---|---|---|---|---|
| [A](coding-A.md) | 8 pass; one C1 subtest errors | 11/11 pass | fail | pass | provisional fail |
| [B](coding-B.md) | 9/9 pass | 11/11 pass | pass | pass | provisional pass |

A tests membership in a set before checking the operation's type. For `op: []`, it raises `TypeError` instead of the specified `ValueError`. This error occurs before opening the DB; no inventory corruption is observed. Both implementations pass the independent transition, durable replay, rollback, process-crash/retry, contention and snapshot checks. Each snapshot also has an explicit read transaction across both SELECTs, supporting the code-level coherence argument beyond finite stress.

The author suites both pass while the external input check distinguishes the candidates. Both replies report Python 3.13.5 execution themselves; our Python 3.12.14 logs are independent evidence and do not verify those reported model-side executions. No answer was repaired or resubmitted. The single coding pair favors B on this concrete contract check; it does not establish a reliable policy effect, broader coding superiority or an English/Japanese language effect. A failing pair is excluded from brevity comparison.

## Evidence and limits

The unchanged [rubric](rubric.md) retains its pre-collection wording (including "No answers have been collected") as a frozen artifact, not current run status. [Plan](plan.json), [frozen hashes](frozen-hashes.json) and [harness validation](checks/validation.json) establish the locally recorded sequence; they were not publicly timestamped before collection.

Raw replies are unchanged clipboard bytes. Per-case `*-visible.txt` files contain the bounded conversation text exposed by the UI; `*-ui-progress.jsonl` files contain sampled displayed statuses. They exclude unrelated sidebars/history and are neither complete network traces nor hidden reasoning. `*-model.png` captures the selected Extra High Power control; `*-mode.png` captures the selected instruction-preserving temporary mode. GPT-5.6 Sol was explicitly selected via the model radio before each send; the cropped Power images alone do not independently prove the backend model. Submission and copy times include evaluator delays and are not a latency benchmark.

Research sources were checked against the actual versions linked in the two verification notes. Source sets/search results differ, so the pair measures end-to-end research under these visible conditions rather than a fixed-corpus synthesis effect. The research tasks explicitly require citations; they do not resolve the earlier spontaneous-attribution failure. Passing finite tests does not prove every concurrent schedule, arbitrary storage failure or a true mid-commit kill. The full 16-input suite, human grading confirmation and eligible Copilot comparison remain incomplete; existing failures and merge hold remain.

## Restoration and review

The original empty instructions and all eight switches were restored and verified after a successful reload: writing-style reference OFF, the other seven ON. A blocked reload was canceled, pending settings saved, and the verification repeated after reload; the final record contains only that successful persisted check. Five owned windows were closed and zero remained. Other windows/history were not deleted; restoring switches does not recover previously lost memories. Power stayed non-Pro Extra High.

A bounded Tier 2 review covers the pre-collection harness and final evidence/grades. H1 was fixed and specifically verified before collection; the final data review checks extraction, source-based grades, test outcomes and limitations. It is an AI review, not the outstanding human grading confirmation. No policy, prepared task input/rubric or historical result was changed for this run.
