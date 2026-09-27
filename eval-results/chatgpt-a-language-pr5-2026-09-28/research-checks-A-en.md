# A-en research response primary-source checks

Checked 2026-09-28 JST against downloaded primary PDFs in `/tmp/source-first-a-english/pdfs`. This is a scoped check of the saved A-en response, not a full literature review or a check of PR5/A-ja research replies.

## Result

R1, R3, R4 and R5 provisionally pass for the saved A-en reply. R2 is partial because the Li/Kim table rows omit the generation-model identities required by task requirement 2. The omission prevents an unqualified full-task pass, although the decision-critical metadata, main numerical claims and four recalculations checked below are supported by the cited primary texts, but not every citation token or every sentence in the long answer was independently verified.

| Paper | Primary source check |
| --- | --- |
| [Park et al., "Scaling Discovery through Test-Time Communication"](https://arxiv.org/pdf/2609.21032v1) | arXiv v1 dated 2026-09-17. PDF text supports ARC-AGI-3 / polyomino / MNIST / Terminal-Bench, Sonnet/Opus 4.6 and GPT-5.6 Sol, Figure 3 token-efficiency 3.8x and 4.9x, low-compute <=400K output-token caveat, Figure 4 0.2x per-agent budget caveat, and Table 3 Terminal-Bench single 52.53%, independent pass@2 62.36%, team@2 60.67%. |
| [Heuillet and Peddiraju, "CIPHER"](https://arxiv.org/pdf/2607.14386v1) | arXiv v1 dated 2026-07-15. PDF text supports Haiku 3.5 / Sonnet 3.7 setup; Tables 3-5 include M=1/3/5, leader/self aggregation, Infi CIPHER(1,1) 69.13 with 19K/2K tokens, CIPHER-dagger(10,5) 81.06 with 86K/5K tokens; limitation section says no fully compute-matched five-independent baseline. |
| [Wan et al., "Inference-Time Scaling of Verification"](https://aclanthology.org/2026.findings-acl.1243.pdf) | arXiv v1 2026-01-22, v2 2026-04-29, ACL Findings 2026 PDF available. PDF text supports DeepVerifier meta-eval 75.00 precision, 71.43 recall, 75.56 accuracy, 73.17 F1; GAIA Full Claude-3.7 52.22 -> 60.12 -> 58.93; BrowseComp 5.0 -> 10.0 then 9.0; verifier rounds are the scaling unit. |
| [Li et al., "Benchmark Test-Time Scaling of General LLM Agents"](https://arxiv.org/pdf/2602.18998v1) | arXiv v1 dated 2026-02-22. PDF text supports General AgentBench domains including search/coding/reasoning/tool use; Appendix cost table as token-cost accounting; Figure 8 says pass@K exceeds self-choice and self-choice can degrade as K grows; GPT-5 verifier generally underperforms the best self-choice line. |
| [Kim et al., "Towards a Science of Scaling Agent Systems"](https://arxiv.org/pdf/2512.08296v3) | arXiv v1 2025-12-09, v3 2026-04-08. PDF text supports six benchmarks, 260 configurations, five architectures, mean 4,800 reasoning tokens/trial and tool-call access; Table 5 success SAS .466, Independent .370, Decentralized .477, Centralized .463, Hybrid .452; mean turns 7.2 / 11.4 / 26.1 / 27.7 / 44.3; BrowseComp-Plus Decentralized +9.2% is supported. |
| [Zhu et al., "Scaling Test-time Compute for LLM Agents"](https://arxiv.org/pdf/2506.12928v1) | arXiv v1 dated 2025-06-15. PDF text supports GAIA with GPT-4.1/CodeAgent; Table 1 baseline 55.76 and BoN 63.03; Table 2 every-step reflection 55.15 and selective reflection 56.36; Table 3 voting 56.8, scoring 59.39, listwise 63.03; Table 5 pass@1/2/4 is present. |

## Recalculation checks

- Zhu BoN: 63.03 - 55.76 = +7.27 percentage points; 7.27 / 55.76 = 13.04% relative. The answer labels this as the realized merged score, not pass@K.
- DeepVerifier: GAIA Full 52.22 -> 60.12 is +7.90pp and +15.13% relative; 60.12 -> 58.93 is -1.19pp.
- Park Terminal-Bench: 62.36 - 52.53 = +9.83pp, 9.83 / 52.53 = 18.71%; team@2 60.67 - 52.53 = +8.14pp, 15.50% relative. The answer correctly warns that pass@2 is candidate availability, not selected-answer accuracy.
- CIPHER token count: 19K + 2K = 21K; 86K + 5K = 91K; 91 / 21 = 4.33x. Score 81.06 - 69.13 = +11.93pp; 11.93 / 69.13 = 17.26% relative. The answer correctly says this is not all-in fixed-model cost evidence.

## Limitations

The response's UI citation labels were captured separately in `research-A-en-citation-labels.json`; the Markdown placeholder tokens alone are not treated as missing citations. This check did not independently verify every UI citation target, all source excerpts, or the answer's full paper-selection search process. PR5 was subsequently subject to an evaluator-side interruption, documented in research-amendment.json; A-ja research was not yet run, so no PR5-vs-A-en or A-ja-vs-A-en research comparison is established.

Parent verification additionally checked Zhu tables 1/2/3 on PDF pages 6/7/8, Kim v3 page 21 reasoning-token statement, Li section 4.3 selection caveat, and DeepVerifier tables 3/4. These support the cited locators and budget distinctions. The current source pages confirm the declared first/revision dates; peer-review statuses marked unconfirmed are not treated as proven absence of publication.
