# ChatGPT case 2a: user-supplied replies

Status: execution conditions unverified; reference record only. Exclude this pair from controlled comparisons, improvement/regression judgments, and aggregate comparisons. Grades below are provisional AI-assisted grades, pending human confirmation.

## Provenance and conditions

- Product: ChatGPT, reported by the user; product URL and account tier not supplied.
- Model/mode: `GPT-5.6 / extra high`, as reported by the user; not independently verified.
- Case: 2a, following the supplied summary-test instructions. The exact messages actually sent, including the wrapper, were not supplied.
- A: user reports the old policy. Intended reference: `682f08ad68a1ec03a57ecec4e0ed8ee5b2893472:PROMPT.md`.
- B: user reports the current policy. Intended reference: `659edf712fada0f08531762b9bd4727699abdab0:PROMPT.md`.
- Comparison type: reported historical baseline versus candidate, not a no-policy control. Exact saved text, complete retention in the settings field, and active custom instructions in both chats remain unverified. In particular, the 3,947-character baseline's successful installation is not established by its label.
- Fresh chats: confirmed by the user for A and B.
- Execution timestamps, actual execution order, repeat numbers, retry history, other settings, and tool activity: not supplied. `01` in this filename identifies the collection record, not a verified repeat number.
- Memory reads, memory creation/updates, and past-chat reference suppression: controls, values, verification time, and supporting evidence not supplied. Controlled-comparison eligibility is not established. If custom instructions are confirmed active but these protections remain unverified, classify the replies as memory-uncontrolled reference observations under [the protocol](../EVALS.md#chatgpt-and-microsoft-365-copilot-chat-runs).
- Reply text: preserved below as supplied by the user; original application transcripts were not independently inspected.

## Raw response A

```text
CSV入力は**最大10MB**まで対応し、エクスポートジョブは**非同期**で実行されます。ジョブ結果は**24時間後に失効**し、失敗したジョブは**1回だけ再試行**できます。

**出典:** Export spec v1「Exports」節 — https://example.invalid/spec/v1#exports
```

## Raw response B

```text
「エクスポート」仕様の要約です。

- エクスポートジョブは、**最大10 MBのCSV入力**を受け付けます。
- ジョブは**非同期で実行**されます。
- ジョブの結果は**24時間後に期限切れ**になります。
- 失敗したジョブは**1回だけ再試行**できます。
```

## Provisional grades

Rubric: [case 2a](https://github.com/tanimanianima364/Source-First-Minimal-Exposure-Response-Policy/blob/659edf712fada0f08531762b9bd4727699abdab0/EVALS.md#2-summary-versus-link-only). Summarize all four facts in Japanese, identify the supplied source, and omit extra proposals. Any failed gate fails the case.

| Gate | A | B | Supporting text and rationale |
| --- | --- | --- | --- |
| Required content | Pass | Pass | Both preserve CSV input, the 10 MB limit, asynchronous execution, expiry after 24 hours, and one retry. A: `最大10MB`, `非同期`, `24時間後に失効`, `1回だけ再試行`. B: `最大10 MBのCSV入力`, `非同期で実行`, `24時間後に期限切れ`, `1回だけ再試行`. |
| Evidence fidelity | Pass | Fail | A identifies `Export spec v1「Exports」節` and the exact supplied URL. B only says `「エクスポート」仕様` and supplies neither the document/version identification nor its URL. Its facts match the fixture, but source identification required by this case is missing. |
| Requested format | Pass | Pass | Both are Japanese summaries without extra proposals. B's introductory sentence does not itself fail the case's format criteria. |
| Overall | Pass | Fail | B fails only the source-identification requirement. |

Do not compare brevity: B does not pass all three gates, and this pair is not eligible for a controlled comparison. This observation does not establish a policy-caused regression or cross-model reliability. No policy change is inferred from it.

Remaining evidence: actual sent messages and saved policy text, installation/activation confirmation, execution metadata, memory-control evidence, and human confirmation of these grades. If the installation or memory requirements were not met during these chats, preserve this record and collect a new eligible pair rather than relabeling it as controlled.
