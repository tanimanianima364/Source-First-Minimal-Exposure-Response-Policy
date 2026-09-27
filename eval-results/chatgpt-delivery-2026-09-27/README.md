# Custom-instruction delivery diagnostic — 2026-09-27

Status: three single-shot diagnostic replies collected; none returned the required marker. Cause remains unresolved. These are not case 9 scores, policy comparisons, or evidence that the source-identification revision works. `PROMPT.md`, fixture inputs, and rubrics are unchanged from `c3c527e14315fec9b8b79532f0fbb8850b5148fe`. Human grade confirmation and the PR merge hold remain pending.

## Procedure and observations

The [initial plan](plan.json) was saved locally before either memory-OFF submission. After both failed, the [extension plan](extension-plan.json) was saved before the single memory-ON submission. Plans were not separately committed or posted before running. Each condition used a new Chrome window/chat; no regeneration or replacement. The instruction appeared only in the custom-instruction settings, and each user message was exactly `適用確認`.

The diagnostic instructed an exact one-line reply of `DELIVERY_CHECK_20260927_R2`. Its saved/read-back contents matched the plan exactly, without newline normalization. The original instruction field was empty. The editor and Personalization panel exposed no separate “Enable customization” switch; this observation does not establish an internal enable flag.

Each chat explicitly selected `GPT-5.6 Sol`; menu captures show `5.6 Pro` and Power at the rightmost position: [normal](normal-model.png), [temporary](temporary-model.png), [memory ON](memory-on-model.png). Hidden backend version and numeric reasoning settings are not known.

For the first two probes, the eight controls in [controls.json](controls.json) were OFF after the initial Save/Reload and before/after each answer: memory, writing-style reference, fast answers, suggested prompts, recording-history reference, web search, Library search, and connector search. The normal chat did not enable temporary mode. In the temporary chat, the menu's Personalized radio was explicitly checked, and its description said it could reference plugins and custom instructions ([capture](temporary-mode.png)); Unpersonalized was unchecked. This resolves the meaning of the visible selector for this run, not retrospectively for earlier runs.

For the extension, memory was ON and the other seven controls read OFF before/after the reply. Enabling memory also changed Library search to ON; it was returned OFF before submission. A fresh temporary menu explicitly selected Personalized and described memory, plugins, and custom instructions ([capture](memory-on-mode.png)). The diagnostic instruction was reopened and checked unchanged. Settings interactions included unavailable Save controls and later an unsaved-changes/reload confirmation; therefore the extension's control snapshots are UI observations, not independent proof that every OFF value was durably saved. Existing memory was allowed in any event, so this is an exploratory diagnostic only.

## Complete replies and exact-match results

All times are JST on 2026-09-27; capture times are copying times, not generation latency. Reply files preserve Copy text as UTF-8. SHA-256 values and pre/post setting snapshots are in [controls.json](controls.json).

| Condition | Submitted | Captured | Complete reply | Required marker |
| --- | --- | --- | --- | --- |
| [Normal / memory OFF](normal.md) | 17:52:13 | 17:53:17 | はい、適用されています。 | Absent |
| [Personalized temporary / memory OFF](temporary.md) | 17:54:19 | 17:55:05 | 確認しました。指示は適用されています。 | Absent |
| [Personalized temporary / memory ON](memory-on.md) | 17:57:35 | 17:58:35 | 適用されています。 | Absent |

All three fail the predeclared exact-match diagnostic. Statements that instructions are applied are model self-reports, not verification. No condition supplied positive evidence of applying this saved instruction. These observations neither prove that custom instructions are universally disabled nor distinguish delivery failure, application behavior, or model noncompliance. Switching to normal chat or enabling memory did not produce a successful probe in these attempts; a general causal conclusion is not supported.

The [Custom Instructions documentation](https://help.openai.com/en/articles/8096356-chatgpt-custom-instructions), [Temporary Chat documentation](https://help.openai.com/en/articles/8914046-temporary-chat-in-chatgpt), and [Memory documentation](https://help.openai.com/en/articles/8590148-memory-in-chatgpt) were checked on the same date. Temporary Chat documents the distinction between Personalized and Unpersonalized, including custom-instruction use. Documentation and saved field text alone cannot verify delivery to a particular response.

## Restoration and remaining work

The eight original switch values were restored and checked after Save and an unobstructed Reload; original empty custom instructions were reopened and verified at 18:01:27 JST. The original values were writing-style reference OFF and the other seven ON. The four windows created for this run were closed, with zero owned windows remaining; other browser windows were untouched. Remote debugging remained unused. No claim is made that toggling memory restores previously remembered information.

The one regular diagnostic conversation remains in chat history; neither temporary conversation was saved. Restoring memory may allow later use of the retained regular conversation. No existing chat history was deleted.

Do not keep extending the policy to compensate for this unresolved diagnostic. The next useful step is an independently observed manual application check or provider investigation of this minimal reproduction before more policy-effect comparisons. Prior case 9 source-identification failures remain recorded, without attributing them specifically to wording. These three diagnostics do not complete the 15-input suite or human grading.
