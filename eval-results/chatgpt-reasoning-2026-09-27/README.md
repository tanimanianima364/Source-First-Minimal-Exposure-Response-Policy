# Closed-world reasoning comparison — 2026-09-27

All four planned replies were collected. Both policies provisionally solve both questions, including valid optimality/minimality, safety and progress arguments. No reasoning-quality winner is established. This run grades correct solutions with checkable proofs, not citation repetition, answer length, or an added operational checklist. Human confirmation and the existing merge hold remain pending.

## Design and conditions

- A: `29ad511c447a5cb15c30cde7cb2d0a6b9aeb8218:PROMPT.md`; B: `01cd1decb47768bb5248bb70439f46f737a13ddb:PROMPT.md`. Both Japanese, same model. This is not a language comparison or the isolated simplest-solution comparison.
- [Optimization input](optimization.txt): adversarial three-scenario, two-stage selection with budget, prerequisites, incompatibilities and pair bonuses. Requires all optimal initial choices, feasible contingent policies, global upper bounds, a fixed-choice comparison and sensitivity to extra budget.
- [Concurrency input](concurrency.txt): serialized wrapping counters versus overlapping writers, minimal counterexamples, a repaired snapshot proof, progress guarantees and arbitrary finite counter width. All memory semantics are supplied; real-language/CPU details are excluded.
- [Plan](plan.json), [rubric](rubric.md), [oracle code](verify_oracles.py), and [oracle output](oracle-output.json) were saved locally before submission; not publicly committed before collection. The inputs have no terminal newline to avoid composer trimming. Expected answers and rubric never enter the evaluated chats.
- Order: optimization A → optimization B → concurrency B → concurrency A, once each. No regeneration, replacement or result-driven criterion change. These two questions are separate from the 16-input synthetic regression suite and prior complex-task checklists.
- Existing Windows Chrome account, ChatGPT web, native UI Automation. Each new chat explicitly selects GPT-5.6 Sol and verifies **5.6 Extra High, 4 of 5**. No Pro requests. Backend revision and sampling settings are unavailable.
- Fresh Personalized temporary chat each time; radio selection/description verifies custom instructions remain permitted. Memory, writing-style reference, fast answers, suggested prompts, record-history reference, web search, Library search and connector search all OFF; persisted/before/after snapshots per response. The same [documented memory eligibility](../../EVALS.md#chatgpt-and-microsoft-365-copilot-chat-runs) as prior same-day runs applies, not a claim of internal provider-state inspection.
- Each policy installed only in settings, reloaded and read back, identical to its canonical text except removal of one terminal LF (A 1,344, B 1,402 saved characters). Composer text must match the exact question. Raw Copy bytes are retained, including line endings, spacing and any UI math markers.

## Oracle checks

Run `python3 eval-results/chatgpt-reasoning-2026-09-27/verify_oracles.py` from the repository root; it uses the Python standard library and prints the saved oracle output.

Optimization is checked by exhaustive enumeration of contingent policies, independently cross-checked against per-first-pair scenario maxima. Fixed-choice policies are enumerated separately. For concurrency, 495 serialized and 34,650 unrestricted program-order interleavings of two writers and one reader attempt are explored. These finite checks validate counterexamples and minimum completed-writer counts within that model; they do not replace the general repaired-safety, linearizability, progress, or arbitrary-width proofs required of each answer.

## Results

[Detailed provisional grades](grades.md). P = pass. All times JST, 2026-09-27; copy timestamps are not generation latency. Character counts normalize CRLF to LF and include formatting; they are descriptive, not a reasoning score.

| Response | Sent / copied | Solution components | Proof | Format | Characters | Model / mode |
| --- | --- | --- | --- | --- | --- | --- |
| [optimization-A](optimization-A.md) | 20:18:27 / 20:22:27 | O1–O4: P | P | P | 5053 | [Model](optimization-A-model.png) / [Mode](optimization-A-mode.png) |
| [optimization-B](optimization-B.md) | 20:23:37 / 20:27:54 | O1–O4: P | P | P | 4951 | [Model](optimization-B-model.png) / [Mode](optimization-B-mode.png) |
| [concurrency-B](concurrency-B.md) | 20:28:29 / 20:34:33 | C1–C4: P | P | P | 4598 | [Model](concurrency-B-model.png) / [Mode](concurrency-B-mode.png) |
| [concurrency-A](concurrency-A.md) | 20:36:15 / 20:40:12 | C1–C4: P | P | P | 5061 | [Model](concurrency-A-model.png) / [Mode](concurrency-A-mode.png) |

- Both optimization answers derive the adaptive optimum 13, all optimal initial pairs BE/BG, the fixed-choice optimum 12, and the budget-11 optimum 15 uniquely at DE. Each supplies valid global upper bounds. Every one of the 39 table rows in each reply was checked for feasible witnesses, score values and exact maxima. The old initial pairs remain at guarantee 13 when only their later decisions are reoptimized.
- Both concurrency answers give valid minimal counterexamples (two completed writers for serialized mod-4; zero for overlapping nonwrapping writers). Both prove repaired successful-reader safety, distinguish wait-free failure from success after writers cease, and generalize wraparound to every k≥1. Their different event schedules and linearization points are valid alternatives, not conflicting conclusions.
- Both policies succeed on these questions; there is no observed correctness/proof advantage. One response per task/condition cannot establish equal general reasoning ability or attribute differences to the policy. The internal reasoning process and any internal computation are unobserved; this is an answer-level problem-solving comparison. These closed-world questions do not test live-source retrieval or resolve the earlier case 10 attribution failure.

## Integrity, restoration and limits

[controls.json](controls.json) records policy hashes, saved character counts, all 12 persisted/before/after control snapshots, raw response hashes, timestamps and restoration. [frozen-hashes.json](frozen-hashes.json) confirms the plan, two inputs, rubric, oracle script and oracle output stayed unchanged from their local pre-submission finalization. This is not independently timestamped public preregistration. Raw replies and cropped model/mode images match the private capture files byte for byte. The existing policy, old inputs/rubrics and historical replies were not changed.

The original empty instructions and all eight settings were restored and verified after reload (writing-style reference OFF, the other seven ON). An unsaved-settings reload dialog was canceled, changes saved, and the final verification performed only after a successful reload. Five owned windows were closed, with zero remaining; other windows/history were not deleted. Power remained non-Pro Extra High. Restoring switches does not recover memory that may have been lost on disabling it.

The oracle received an independent mathematical review; response grading and record consistency received a separate bounded review. Parent checks separately cover the general concurrency arguments, which cannot be established by the finite interleaving explorer alone. Grades remain provisional until human confirmation. This result neither rerates previous failures nor completes the 16-input suite, Copilot evaluation, language comparison, repeated trials or the existing merge conditions. Merge remains on hold.
