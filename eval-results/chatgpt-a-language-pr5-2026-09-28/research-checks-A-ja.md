# A-ja research — primary-source checks

Checked 2026-09-28 JST against the unmodified [answer](research-A-ja.md) and frozen task/rubric. [UI citation labels](research-A-ja-citation-labels.json) preserve the primary link for each placeholder occurrence in document order; indices skip explicit Markdown links and additional grouped sources were not expanded.

| Primary source | Verified scope and qualifications |
| --- | --- |
| [Zhu v1](https://arxiv.org/pdf/2506.12928v1) | First/used 2025-06-15. GAIA 165, GPT-4.1/CodeAgent, width 4/beam 2 and tables 1–2 on pp.6–7 support baseline 55.76, BoN 63.03, every-step reflection 55.15, threshold <2 56.36, <8 53.33, <5 52.12. Not an all-in monetary comparison. |
| [BATS v2](https://arxiv.org/pdf/2511.17006v2) | First 2025-11-21; v2 2026-08-17; arXiv records COLM acceptance. The model roster and tool-budget versus monetary-cost distinction match. Table 3 p.10 supports BATS 24.6/46.0/27.0 versus ReAct 12.6/31.5/20.5. Table 2 p.6 supports 12.6→12.8, 9.9¢→6.8¢, search 14.24→8.48 and browse 1.36→1.09. Figure 10 / discussion p.23 supports >37% at ~$0.23 versus >$0.50. The authors assign search/browse a $0.001-per-call rate (appendix A); these are their cost assumptions, not verified invoices for the proposed deployment. The results do not establish the proposed joint cost/time limits. |
| [DeepVerifier v2](https://arxiv.org/pdf/2601.15808v2) | First 2026-01-22; v2 2026-04-29; ACL Findings publication confirmed. Table 2 p.6 supports F1 73.17, 61.54 and 25.00. Table 3 supports GAIA-Web 51.11→63.33 at round 4→62.22 at round 10, but it is on PDF p.8, outside the answer's stated pp.6–7. |
| [LLM-as-a-Verifier v2](https://arxiv.org/pdf/2607.05391v2) | First 2026-07-06; v2 2026-07-07. Table 3 p.10 supports Terminal 83.1/92.1/86.5 and SWE 76.1/84.4/78.2. Default granularity/repeats/criteria and candidate-versus-verification accounting are described in the methods. Table 9 is on p.28; p.27 discusses it but is not the table location stated by the answer. Terminal's generator is identified, but the answer does not name its verifier model. |
| [ArcticSwarm v1](https://arxiv.org/pdf/2609.01870v1) | First/used 2026-09-01. Qwen 3.5-27B, 830 tasks, gated isolation/review, table 3 p.7 values 82.6/78.8/74.5, table 13 p.21 majority 63.2/oracle 86.1 at N≈36, and table 14 p.22 24.9M tokens/83.3 median minutes match. Token-equivalent multiplicity must not be read as a verified all-in monetary ratio. |

## Grades

- R1 pass: five empirical studies, two first released after July 1; declared versions predate the cutoff. Publication metadata and unconfirmed statuses are distinguished.
- R2 partial: principal numbers match, but DeepVerifier table 3 and verifier table 9 have incorrect page locations. Verifier-model identity is also incomplete. These are traceability/completeness issues, not fabricated central results.
- R3 pass: specific reflection/decomposition, independent selection/gated coordination and BATS/adaptive-budget comparisons address feedback, selection and accounting; application hypotheses are conditional.
- R4 pass: parent recomputation confirms Zhu +7.27 pp/13.04%; F1 +11.63 pp/18.90%, versus 25.00 +48.17 pp/192.68%; Terminal realized +3.4 pp/4.09%, headroom recovery 37.8%, SWE recovery 25.3%; BATS +0.2 pp/1.59%, cost −31.31%, search −40.45%, browse −19.85%. Source denominators match.
- R5 pass: a fixed-model, no-training initial experiment with independent candidates, conditional verification/repair, all-in hard caps, adverse evidence and no guarantee of deployment success.
- R6 partial: baseline, matching, blinding, task-clustered repeats, caps and stopping rules are present, but the noninferiority uncertainty method fails for unobserved rare errors as detailed below.

## R6 counterexample

The answer applies task-cluster bootstrap to CIs generally, requires the major-error difference to stay within +5 percentage points, and extends 12 to 20 tasks only if a CI crosses a decision threshold. If baseline and candidate observe zero major errors on all 12 tasks × 2 runs, every paired task difference is zero and every empirical bootstrap replicate is zero. The resulting `[0, 0]` interval passes +5 pp, and the conditional extension/inconclusive rule does not trigger.

Yet under an illustrative candidate true error rate of 10%, even 24 independent error-free candidate runs have probability `0.9**24 = 0.0797664`. With independent trials, the exact one-sided 95% upper bound after 0/24 events is `1 - 0.05**(1/24) = 0.117346`, already above 5%; task dependence does not justify treating the 24 runs as stronger independent evidence. Thus absence of observed errors cannot establish the proposed margin using the specified empirical bootstrap. Other adoption gates can pass while this guardrail falsely appears satisfied. This is a flaw in the generated pilot proposal, not a pilot we ran.

No full-task pass. Checks cover decision-bearing primary claims and all four recalculation groups; they do not attest every grouped source or the model's complete search history. Human grading confirmation remains pending.
