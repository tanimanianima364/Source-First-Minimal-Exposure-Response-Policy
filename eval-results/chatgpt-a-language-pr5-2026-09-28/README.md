# PR #5, Japanese A, and English A — 2026-09-28

Nine final replies collected and provisionally graded. No general English-language advantage or overall statistically superior policy is established. Japanese A remains canonical. The research PR5 condition uses one disclosed replacement after an evaluator-side interruption; [amendment and exclusion](research-amendment.json) preserve that deviation. [Plan](plan.json) was committed before the first send at `117dc3d20268984848a7e996b63cf8a5f256e306`, fixing English A and all input/check hashes.

| Task | PR5 (English) | A-ja | A-en |
| --- | --- | --- | --- |
| Version-dependent source attribution | Pass | Pass | Fails required source identification |
| SQLite fixed independent checks | 9/9 | 9/9 | 9/9 |
| Separate post-hoc string-domain diagnostic | Pass | Lone-surrogate initialization fails | Pass |
| Research synthesis | R2 partial: locator/model omissions | R2 partial; R6 rare-error interval flaw | R2 partial: model omissions |

See [grades](grades.md) for separate criteria, raw answers, primary-source checks and execution logs. Author tests also passed (PR5 13, A-ja 10, A-en 13), but passing self-authored tests is not independent proof. None of the research answers is an unqualified full-task pass. The string diagnostic was discovered after collection and cannot be counted as a predeclared benchmark win.

All eight original settings and the original empty custom instructions were restored and read back ([restoration](restoration.json)); the eleven owned browser windows were closed ([record](closed-windows.json)). Restoring switches does not restore any memory content removed earlier. Pro was not used.

Three conditions use one fresh response per task: PR5 (`682f08a`, identical PROMPT blob to PR #5 head `c25a10e`), A-ja (`29ad511`), and its English translation A-en (`117dc3d:PROMPT.en.md`). The tasks are the existing case10, concurrent SQLite implementation, and live AI-literature review. Rubrics and the offline coding harness are unchanged and never sent to the tested chats. This is nine completed task-condition replies plus one excluded interrupted attempt, not the full regression suite.

The translation comparison includes changes in length and tokenization; it cannot prove that English instructions are generally better. PR5 versus A-en compares cumulative policy changes with both instructions in English. PR5 versus A-ja also changes language. Live search results and selected studies may vary; one reply per cell supports only descriptive observations. Human grading confirmation remains required.

Installation requires the same custom-instruction field and exact save/reload readback, allowing only the predeclared removal of one terminal LF in every condition. PR5 has 3,947 characters, A-ja 1,345, and A-en 4,149. Oversized/rejected installation is not-run, never a model failure or permission to truncate. Hidden model versions and sampling controls are unavailable.

Use Personalized temporary chats with custom instructions active, Memory and history reference disabled, and all eight recorded controls OFF except Web search ON for research. Readbacks and selected GPT-5.6 Sol / Extra High 4/5 evidence are required before every send; Pro is prohibited. Restore original settings afterward. OpenAI's [temporary-chat documentation](https://help.openai.com/en/articles/8914046-temporary-chat-in-chatgpt), checked 2026-09-28 JST, distinguishes personalization from memory creation: temporary chats do not create/update memories, while existing memory use remains subject to account settings. Its [memory documentation](https://help.openai.com/en/articles/8590148-memory-in-chatgpt) describes memory/history controls and their side effects. These controls do not suppress the service's separate limited safety context.

[Raw-response manifest](responses.json), [provisional grades](grades.md), and [research citation lookup](research-citation-map.json) preserve the collected evidence. [Setup](setup.json) records controls and limitations. The [prospective input amendment](input-amendment.json), recorded before any coding/research send, permits the composer to remove exactly one terminal LF in those inputs for all three conditions; all other characters remain fixed. Submission files contain timestamps. Equality was checked by the sender guard before clicking Send; separate composer captures were added for later sends and are present where available. Research citation-label arrays follow placeholder occurrence order; explicit Markdown links can make numeric indices skip. Grouped additional links are not fully expanded.
