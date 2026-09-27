# Conditional source attribution — non-Pro run, 2026-09-27

Status: one successful delivery probe and six planned comparison replies collected. Under the current rubric, five replies provisionally pass; candidate case 10 fails evidence fidelity. This is a focused run, not a full-suite pass or a demonstrated overall improvement. Human grading and merge remain pending. No Pro request was submitted.

## Conditions and integrity

- A: `29ad511c447a5cb15c30cde7cb2d0a6b9aeb8218:PROMPT.md`, the 1,345-character pre-change policy. B: `01cd1decb47768bb5248bb70439f46f737a13ddb:PROMPT.md`, the 1,403-character conditional-attribution policy. Both are graded with `EVALS.md` at B's SHA. Old runs retain their original grades.
- The [plan](plan.json) was saved locally before any submission: one diagnostic, then 10/A → 10/B → 2a/B → 2a/A → 9a/A → 9a/B, one reply each, contingent on the diagnostic matching. The plan was not committed or posted before collection. No regeneration, additional repeats, or substitutions occurred.
- ChatGPT web in the user's existing Windows Chrome account, via native UI Automation. Every new chat explicitly selected `GPT-5.6 Sol`; every send verified **5.6 Extra High, 4 of 5**, using the UI status and the model-menu captures linked below. This is distinct from the initially displayed Pro, 5 of 5. The selector was lowered before any request, and Pro was not restored. Backend version and sampling parameters are unavailable.
- Each request used a new Personalized temporary chat. The radio selection was checked and its description explicitly permitted plugins/custom instructions; Unpersonalized was unchecked. Per-response `*-mode.png` files preserve the menu. No evaluation conversation was saved to history.
- Memory, writing-style reference, fast answers, suggested prompts, recording-history reference, web search, Library search, and connector search were saved OFF, checked after reload, and checked before/after every answer. [controls.json](controls.json) preserves these snapshots, policy hashes, timestamps, and restoration. The memory-control interpretation follows the same documented requirements in [EVALS.md](../../EVALS.md); no internal provider-state inspection is claimed.
- Diagnostic instructions were retained exactly. For each case, the selected policy was read back after page reload; precisely one terminal LF was removed by the settings field, as predeclared. Saved sizes: A 1,344, B 1,402 characters. All other characters matched. Reusing an unchanged condition still included reload/readback before the next case.
- The chat received only the unchanged synthetic wrapper, corresponding context, and request from B's `EVALS.md`; composer values matched prepared inputs before sending. Policies/rubrics were not placed in case messages. Raw files preserve Copy text without rewriting; length figures below normalize CRLF to LF solely for counting Unicode code points.

## Delivery probe

The [full response](diagnostic.md) was exactly `NONPRO_CHECK_20260927_R1`, matching the settings-only instruction in the plan. Submitted 18:15:24, copied 18:16:18 JST. [Mode](diagnostic-mode.png) and [model](diagnostic-model.png) captures accompany it. This supports application of that short instruction in this run, not universal compliance with either full policy.

Unlike the earlier failed probes, this run used non-Pro mode and a save/reload/readback sequence before collection. The diagnostic was installed before saving the OFF controls together. These differences were not experimentally isolated: neither Pro nor a missing save is established as the cause of earlier failures. The previous records are not erased or retroactively qualified.

## Replies and provisional grades

All times are JST on 2026-09-27; copied times do not measure generation latency. P = pass, F = fail. Each row has repeat number 1.

| Reply | Sent / copied | Content | Evidence | Format | Overall | LF-normalized characters | Model capture |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [10 / A](10-A.md) | 18:18:32 / 18:18:56 | P | P | P | Provisional pass | 450 | [Extra High](10-A-model.png) |
| [10 / B](10-B.md) | 18:20:12 / 18:20:48 | P | F | P | Provisional fail | 379 | [Extra High](10-B-model.png) |
| [2a / B](2a-B.md) | 18:21:46 / 18:22:12 | P | P | P | Provisional pass | 135 | [Extra High](2a-B-model.png) |
| [2a / A](2a-A.md) | 18:23:23 / 18:23:54 | P | P | P | Provisional pass | 160 | [Extra High](2a-A-model.png) |
| [9a / A](9a-A.md) | 18:24:54 / 18:25:38 | P | P | P | Provisional pass | 762 | [Extra High](9a-A-model.png) |
| [9a / B](9a-B.md) | 18:26:53 / 18:27:34 | P | P | P | Provisional pass | 614 | [Extra High](9a-B-model.png) |

- **10/A:** “v2…最大10 MB”, “v3…最大25 MB”, and “どちらも…非同期実行” correctly answer the size question. The response identifies both manuals, their Export limits sections, and corresponding URLs. Its pre-adoption checks distinguish unknown output/operational limits from supplied input limits. Japanese, answer first, brief follow-up; no invented completed test.
- **10/B:** Content and format pass: it gives the same limits, asynchronous operation, version/deployment checks, and appropriately distinguishes input from output size. Evidence fails: the entire reply lacks manual titles, sections, and URLs. “提示された資料” does not satisfy case 10's explicit traceability requirement. This is an observed A-pass/B-fail pair, not proof of a reliable or wording-caused regression from one sample.
- **2a/A and B:** Both retain all four facts: CSV up to 10 MB, asynchronous execution, 24-hour result expiry, and one retry. Both answer in Japanese without an extra proposal or invented claim. A identifies Export spec v1 / Exports; B omits the identifier. Under the current rubric this omission is acceptable, because the single supplied source is unambiguous.
- **9a/A and B:** Both choose the existing manual spreadsheet, import 50 rows, aggregate by department, and export. Both check row coverage and totals, avoid new products/code or recurring automation, and preserve the fixture's limitations. A includes “取り込み漏れや重複がない”, total reconciliation, output reopening, and the environment identifier. B checks the row count, department coverage, totals, and spot sums; source-name repetition is optional. Existing folder permissions are optional usage of a supplied capability, not an invented requirement. Both are Japanese and code-free; verification steps serve as next actions.

For the two provisionally passing pairs, B is shorter in these observations: 2a 160 → 135 characters and 9a 762 → 614. No brevity comparison is made for case 10 because B fails a gate. These single-pair differences do not establish a general improvement or statistical reliability; human confirmation is still required.

## Restoration and remaining work

The original empty instructions and eight original switches were restored, saved, and checked after reload; instructions were reopened and matched at 2026-09-27T18:28:45.8741396+09:00. Original writing-style reference was OFF; the other seven were ON. Power was deliberately left at non-Pro Extra High, honoring the user's restriction. All eight windows created for this run were closed and zero owned windows remained. Existing windows and chat history were not deleted. Restoring switches does not promise restoration of remembered information lost through disabling memory.

The current policy and rubric were not edited in response to these results. Necessary version-specific attribution remains an observed candidate failure. Review that failure before proposing a further change; preserve it if any future candidate is tested. Case 9b, artifact-only outputs, other inputs, Copilot, and human grade confirmation were not completed by this run. The full suite contains 16 inputs. Merge remains on hold.
