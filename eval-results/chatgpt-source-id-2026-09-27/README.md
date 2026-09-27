# ChatGPT source-identification follow-up — 2026-09-27

Status: six planned replies plus a separately preregistered delivery diagnostic collected; all AI-assisted grades remain provisional until human confirmation. Source omission remains unresolved, and the failed diagnostic prevents attributing it specifically to policy wording. This run compares the preferred B with a narrow source-identification revision. It is separate from the earlier pre-addition A/B comparison and preserves the [prior failures](../chatgpt-controlled-2026-09-27/README.md).

## Preregistered conditions

- B0: `94f0699a6fc61efdb99d8d13b34b4f1cb5e9b155:PROMPT.md`, the earlier B. B1: candidate commit recorded in [preregistration.json](preregistration.json), 1,345 characters. Only the source paragraph changed: name user-supplied documents and known versions/sections; do not append source text outside explicit artifact-only formats.
- [EVALS.md](../../EVALS.md) inputs and rubrics are unchanged. Before sending any input, the plan was recorded in PR #6: 9a/B0 → 9a/B1 → 9b/B1 → 9b/B0, one each; followed by candidate-only 3a and 3b, one each. No retries, regeneration, or replacement of earlier answers. The two format checks are not comparisons.
- Product: ChatGPT web (`https://chatgpt.com/`), Pro account in regular Windows Chrome; operated through Windows UI Automation. Each new chat explicitly selected `GPT-5.6 Sol`, with menu display `5.6 Pro` and Power slider at the rightmost position. Hidden backend version and sampling parameters are unavailable; no numeric effort label is inferred.
- Policies were saved only in Settings → Personalization → ChatGPT instructions, then reopened and verified. The predeclared normalization allows exactly one terminal LF removed by the field in each policy, with all other characters identical. B0 is 1,283 canonical / 1,282 saved characters; B1 is 1,345 / 1,344. The original instructions and three profile fields were empty.
- Each request used a new **Personalized temporary chat** and the identical wrapper + fixture + selected input, without policy or rubric text in the chat. Composer contents were checked before send. No temporary chat was saved to history.
- With the user's continuing authorization accepting possible memory loss, all eight controls were saved OFF and verified after reload at 16:05:35 JST: Enable ChatGPT memory, Reference my writing style, Enable fast answers, Enable suggested prompts, Reference record history, Web search, Library search, Connector search. These values were checked before and after every response. This time all eight original values were captured before changing memory: writing style OFF, the other seven ON.
- Global memory OFF suppresses memory-based/past-chat personalization; Personalized temporary mode preserves custom instructions and prevents creating/updating memories during evaluation. Record history concerns recordings, not proof of past-chat suppression. Eligibility uses actual controls plus the [Memory](https://help.openai.com/en/articles/8590148-memory-in-chatgpt), [Temporary Chat](https://help.openai.com/en/articles/8914046-temporary-chat-in-chatgpt), and [Custom Instructions](https://help.openai.com/en/articles/8096356-chatgpt-custom-instructions) documentation checked earlier on the same date, not model self-report. No provider-internal memory inspection is claimed.

## Responses and provisional grades

Times are JST on 2026-09-27, repeat 1. Capture times mark copying completed responses, not generation latency. Original Copy text is preserved as UTF-8 with its CRLF and Markdown hard-break spaces.

| Case / condition | Submitted | Captured | Content | Evidence | Format | Overall |
| --- | --- | --- | --- | --- | --- | --- |
| [9a / B0](9a-B0.md) | 16:06:42 | 16:07:50 | Pass | Fail | Pass | Provisional fail |
| [9a / B1](9a-B1.md) | 16:09:45 | 16:11:18 | Pass | Fail | Pass | Provisional fail |
| [9b / B1](9b-B1.md) | 16:12:35 | 16:16:12 | Pass | Fail | Pass | Provisional fail |
| [9b / B0](9b-B0.md) | 16:17:48 | 16:22:01 | Pass | Fail | Pass | Provisional fail |
| [3a / B1](3a-B1.md) | 16:23:33 | 16:23:55 | Pass | Pass | Pass | Provisional pass |
| [3b / B1](3b-B1.md) | 16:25:07 | 16:26:04 | Pass | Pass | Pass | Provisional pass |

### 9a / B0

Content: recommends the installed spreadsheet, import, department grouping/summing, row-count and department coverage, total reconciliation, and spot checks. “今回の50行の単発処理には不要” excludes the automation runner. Optional manual record keeping is within the supplied environment; no new product, code, or recurring automation is introduced.

Evidence: fails to identify the supplied environment document; the full reply contains neither its name nor revision/section. Example department values are explicitly examples, and a pivot-like feature is conditional, not invented as a verified capability. Format: Japanese, recommendation first, no executable code.

### 9a / B1

Content: uses the installed spreadsheet, imports and checks 50 rows, groups/sums departments, reconciles all-row totals, checks department coverage, spot-checks 2–3 departments, and reopens the exported CSV. It excludes the automation runner and proposes no new product/code or recurring workflow. Counting by department is explicitly conditional on that feature being available.

Evidence: fails to identify the environment document despite the new instruction; no document title, revision, or section appears. No completed test or unsupported retry guarantee is claimed. Format: Japanese, recommendation first, no executable code. The shared 9a evidence failure does not establish improvement; neither reply qualifies for a brevity comparison.

### 9b / B1

Content: retains the approved runner, aggregation job, shared folder, schedule, logs, and role-based permissions, with stable business-date keys, staging, input/output hashes, and non-replacing atomic publication as its main route. Tests cover totals/counts, scheduling, partial writes, crashes after publication, failures/log retention, and denied access.

The final acceptance section's alternative “ランナーが同一処理キーの同時実行を確実に排除し、かつ再実行前の完了判定が行える” is less precise than its atomic-publication route. This is a non-gating ambiguity: the answer elsewhere requires staged complete output, hashes, and failure-injection tests allowing only a valid complete final result or no result. The frozen rubric asks for an explicit retry-safety design and those focused checks, which are present. It does not justify assuming the completion check ignores all the validation described elsewhere. **Required content provisionally passes**; adopting an implementation would still require the proposed tests.

Evidence: fails to identify `Aggregation environment`, revision r1, or its section; “提示されたケース” is not identification. The unknown atomic/serialization capabilities are conditional, rather than falsely claimed already verified. Format: Japanese, recommended configuration first, no executable code; text diagrams, output paths, and the key formula are illustrative.

### 9b / B0

Content: uses the approved runner, one aggregation job, and existing shared folder with scheduling, retained logs, and role-based access. Stable date keys, complete staged output plus manifest, atomic non-replacing publication, and matching input/job/output hashes on retry explicitly implement duplicate protection. It handles a crash after publication but before success logging and rejects missing/corrupt manifests. Tests cover totals/counts, unattended execution, partial writes, post-publication failure, retained failure logs, and unauthorized access. Atomicity is an unverified prerequisite throughout; “この試験に失敗した場合、以降の試験結果にかかわらず、重複防止要件は不合格” prevents a weaker fallback from being treated as sufficient.

Evidence: fails to identify the supplied document; “ケース” and “提示された承認済み機能” do not provide its name, revision, or section. Proposed controls and tests are distinguished from fixture capabilities; there is no claimed completed validation or invented concrete retention/performance figure. Format: Japanese, recommendation first, no executable code; paths, layout, and a prose sequence are illustrative.

### 3a / B1 — candidate-only format check

The complete response parses as JSON equal to `{"max_mb":10,"async":true,"retention_hours":24,"retries":1}`. It includes exactly the required keys and faithful values, with no headings, code fence, source appendix, or next steps. All three gates provisionally pass; no external source identifier is required for this artifact-only case. This is not a baseline comparison.

### 3b / B1 — candidate-only format check

The entire reply is a Japanese translation of the four supplied facts: CSV up to 10 MB, asynchronous execution, result expiry after 24 hours, and one retry for failed jobs. There is no heading, source appendix, extra proposal, or invented fact. All three gates provisionally pass; this is not a baseline comparison.

## Policy integrity

- B0 canonical / saved SHA-256: `7ca67a34e23b3715440eb87045d90380da2a3efddafaaa724f5b974920fdaa7a` / `8e298db43576c24dc7fc0a9302b02fe578c3c5d39d1e4335a502476f0a8e7411`.
- B1 canonical / saved SHA-256: `314912776cf72a3fd4151ddaed0b7e44cb43ae5398f68df1ee925d5c6335b543` / `1e3d01b413badfe10e33ae92acf81560da9fb752e5568f757fb75a6256cde500`.

## Separate instruction-delivery diagnostic

After the six planned replies, a [separate diagnostic plan](diagnostic-plan.json) recorded in PR #6 before submission used only a short custom instruction: when the user sends `適用確認`, reply with the single line `SOURCE_POLICY_ACTIVE_20260927`. The short instruction was saved and reopened; only its final LF was removed. The diagnostic used a new Personalized temporary chat with the same eight OFF controls, model selection, and Power position ([menu](diagnostic-model.png)). No policy fixture or grading rubric was sent; it is not a case 9 retry or a policy effectiveness score.

Submitted 16:27:51 JST, captured 16:28:27 JST. The [full response](diagnostic.md) was: “承知しました。何の適用状況を確認しますか？対象の設定・ルール・変更内容などを送ってください。” It did **not** match the predeclared marker. This establishes failure to follow that saved diagnostic instruction in this run, not the cause. It does not prove that all custom instructions are disabled, nor distinguish failure of application/delivery from model noncompliance. UI storage and mode checks alone do not resolve that uncertainty.

## Interpretation

The four new case 9 replies all omit the document identifier. Both policies satisfy the required-content and format gates in these replies, and both candidate-only artifact formats pass. Neither case 9 pair clears all three gates, so there is no brevity comparison. A single response per condition does not establish a wording-specific behavioral effect.

The failed delivery diagnostic further limits attribution: the observed failures remain failures, but cannot be isolated to the source-paragraph wording. Do not relabel them as passes, erase them as access failures, or claim the source omission was fixed. Settings were controlled and saved, but successful instruction delivery/obedience was not established. No full-suite, Copilot, or cross-model reliability claim follows. Human grade confirmation and the existing merge conditions remain pending.

The 1,345-character candidate remains an **unvalidated proposed clarification**, not a demonstrated behavioral fix. Further wording expansion is deferred while the instruction-application uncertainty remains unresolved. The user's earlier preference for B remains qualitative feedback, not rubric or merge approval.

## Restoration and integrity

[Control snapshots and timestamps](controls.json) retain original settings, persisted OFF settings, each response's pre/post checks, and restored values. Cropped model/Power evidence: [9a/B0](9a-B0-model.png), [9a/B1](9a-B1-model.png), [9b/B1](9b-B1-model.png), [9b/B0](9b-B0-model.png), [3a/B1](3a-B1-model.png), [3b/B1](3b-B1-model.png). These crops exclude private chat history.

At **16:31:28 JST**, after saving and reloading, all eight settings matched the captured original values: writing style OFF and the other seven ON. At **16:31:39 JST**, reopening the editor verified the original empty custom instructions and unchanged empty profile fields. Only evaluation-owned windows were closed. Settings restoration is not a claim to restore information lost by disabling memory; the user had accepted that possible loss.

SHA-256 of the raw copied replies:

- `9a-B0.md`: `36102c3e93231ff574f3ff5ccf7801b609b0f2e00efb997019b473e7801baa5f`
- `9a-B1.md`: `d4ef3c458ebbfee0641fcc0a5bd56fc308868fe0b01edcb5c01fc8cc4695e701`
- `9b-B1.md`: `7bda7f35cbeb59d0b0fefa15c43a386a159d017ab46e5e84a720b699dc921632`
- `9b-B0.md`: `9465dc9d5b6c89f658bbe60f5030f0122403ba6aeeb4ee62493b73b9778600cb`
- `3a-B1.md`: `fe37a2519b6332bf61cffc1292627012b2fbc1b4aeb930949bbd68bcd182087d`
- `3b-B1.md`: `5ab3a59364449ea28051bb5071ca04f29ae2a677dc5ed63bc432f8715c00327d`
- `diagnostic.md`: `3dd838ac9e1760b4ab5eb81437e3ea4d11fed0694dca221b681090fd2a20d82e`

Diagnostic instruction canonical/saved SHA-256: `635040b77fa0429004af2427f7d26cb4b29987683f476e6b65bfc343770f7f89` / `0618f85ea4d0fc3d27da94f84f32436fe60671a0b5f18f1931da82fd25225f35`. The exact instruction and input are in the diagnostic plan.

Record checks passed: raw byte/hash equality, exact fixture inputs, canonical/saved policy equality except the declared terminal LF, JSON semantics, all pre/post controls, restoration, model-menu crops, local links, budget, and unchanged rubric. One Tier 1 read-only results review identified an overly strict initial content-fail grade for 9b/B1. Parent triage accepted the finding and corrected it against the frozen rubric; focused table/navigation checks confirmed the correction. No additional agent review round was required. Other grades and the diagnostic/restoration limits had no material findings. This remains AI-assisted, not human grade confirmation.
