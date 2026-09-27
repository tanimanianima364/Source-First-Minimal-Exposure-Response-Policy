# Research and implementation tasks — prepared 2026-09-27

Two new tasks, not executed and not added to the existing 16-input regression suite. They test literature discovery/synthesis and executable concurrent programming, respectively. Policy text and historical results are unchanged.

- Send only [research.txt](research.txt) for a live literature review of how to allocate inference compute for a research assistant. It requires recent empirical work, cross-paper reconciliation, numerical checking and a falsifiable deployment recommendation. Do not prepend the synthetic-data/no-search wrapper.
- Send only [coding.txt](coding.txt) for a complete standard-library SQLite inventory implementation and tests. The challenge is durable replay semantics, atomic batches, process contention and recovery, not adding infrastructure.
- Keep [rubric.md](rubric.md) and the reference notes below out of the evaluated chats. The research task asks the model to find papers itself; the reference set is deliberately not an answer key.

## Future A/B execution

Use A `29ad511c447a5cb15c30cde7cb2d0a6b9aeb8218` and B `01cd1decb47768bb5248bb70439f46f737a13ddb` if continuing the same comparison. Both are Japanese; this does not isolate prompt language. Before collection, freeze exact inputs, criteria, coding checks and policy bytes/hashes, trial count/order and execution capabilities. Verify non-Pro mode and existing [memory/custom-instruction eligibility](../../EVALS.md#chatgpt-and-microsoft-365-copilot-chat-runs); no Pro calls. No browser setting changes or model calls were made to prepare these tasks.

Research needs web search ON in both conditions. Save full answers, retrieved version/URL/locator/access-time records and any available tool traces; do not equate a correct link with observed retrieval. Search results and selected papers can differ, so this is an end-to-end live-research comparison, not a controlled causal estimate. The fixed publication cutoff controls eligible evidence, not the search index. A later fixed-corpus synthesis comparison must be labeled separately because it removes discovery as a skill being tested. Coding must use identical execution/tool access for both conditions; distinguish the model's reported tests from independent evaluator execution. Existing restoration, human-confirmation and merge-hold conditions remain unchanged.

## Task-construction source checks (not required citations)

Primary pages checked on 2026-09-27. These are a starting set, not exhaustive coverage or independently reproduced experiments. Notes distinguish inspected sections from abstract-only access; future graders must verify the actual sources used by each answer.

| Primary source/version | What was inspected / useful distinction |
| --- | --- |
| [Benchmark Test-Time Scaling of General LLM Agents, v1](https://arxiv.org/html/2602.18998v1) | Sections 4.1–4.3: distinguishes sampled candidate availability from self-selection; longer interaction histories and independent sampling have different limitations. Its model/task/selection setting must not be silently equated with later work. |
| [FineVerify, v2](https://arxiv.org/html/2606.00660v2) | Table 1 and Sections 3.2/3.4, Appendix C.4: GPT-5-mini average accuracy 59.2%→67.4% is +8.2 percentage points (about 13.9% relative), not +8.2% relative. Four trajectories are used versus one for Pass@1; Table 9's rounded $0.45/$0.11 is about 4.09x, not proof of meeting the fictional 4x deployment cap. These are paper-reported costs, not current API prices. |
| [Scaling Discovery through Test-Time Communication, v1](https://arxiv.org/html/2609.21032v1) | First posted September 17; Figures 3–4 and accompanying analysis distinguish resource regimes. Communication gains coexist with overhead and low-budget failures; same per-agent resources, same total actions and actual token use are different comparisons. Results on games/optimization do not guarantee gains in literature review. |
| [When Agents Slow Down, v1](https://arxiv.org/abs/2609.15309v1) | First posted September 14. Metadata/abstract only checked; HTML retrieval failed. The abstract describes budget-dependent marginal gains and intermediate-score feedback. Full methods and numeric results remain to be checked before scoring claims based on them. |

## Readiness

Inputs and review criteria are prepared; no A/B responses, execution harness, candidate test runs or scores exist for these tasks yet. A bounded design review checks ambiguity and evidence claims; it cannot establish benchmark validity or task difficulty empirically. Create and freeze independent coding checks before the first candidate is collected. Do not publish a pass/fail or a policy ranking from this preparation alone.
