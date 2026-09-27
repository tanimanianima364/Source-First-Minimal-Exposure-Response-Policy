# Provisional solution grades

A solution is judged against the frozen questions and rubric. Correct numbers, valid witnesses and general/exhaustive proofs are checked separately. Sources and brevity are not correctness gates. Human confirmation remains pending.

## Optimization A — provisional pass

- **O1 pass:** guarantee 13, exactly BE/BG, with G/D/C and A/F/C additions and all six correct scores/costs.
- **O2 pass:** exhaustive admissible first-pair list contains exactly 13 pairs. Its budget-10 scenario-maxima table gives valid global bounds, not just the winning witnesses.
- **O3 pass:** fixed-addition optimum 12 via BC→G or BG→C, scores 12/13/13. A separate 13-row fixed-choice table supplies the upper bound. It explains max/min order and the strict gap using BG.
- **O4 pass:** budget-11 optimum 15 uniquely DE, additions A/B/C, scores 15/16/17. All 13 rows are bounded. The answer distinguishes keeping the original policy, optimizing additions with BE/BG fixed, and changing the initial pair to DE; only the last raises the guarantee to 15.
- **Proof validation:** programmatically checked all 39 candidate-table rows against the oracle, including every displayed addition witness, score, budget and maximum. Tied witnesses such as AF→B versus AF→E are accepted when their listed score and guarantee are correct. The candidate enumeration is exhaustive and the upper-bound argument is valid.
- **Format pass:** Japanese explanatory answer with checkable tables/formulas, no reliance on external information.

## Optimization B — provisional pass

- **O1/O2 pass:** 13, exactly BE/BG, correct feasible policies and an exhaustive 13-pair budget-10 maxima certificate.
- **O3 pass:** 12 with BC→G or BG→C, a separate fixed-choice upper-bound table, and a correct quantifier-order explanation using BG. It does not choose an initial pair after observing the scenario.
- **O4 pass:** 15 uniquely DE with A/B/C additions. Its budget-11 table is exhaustive; it explains why BE gains no new additions, BG improves S2 but not its guarantee, and DE changes the worst-case optimum after reoptimization.
- **Proof validation:** all 39 displayed candidate-table rows were programmatically verified against the oracle, including addition feasibility, all stated scores and exact maxima. Different tied witnesses from A are valid.
- **Format pass:** Japanese, explicit checkable witness/calculation and global certificate. Neither a missing source label nor response length is penalized.

## Concurrency B — provisional pass

- **C1 pass:** complete mod-4 event trace returns `(0,2)` with `a=b=0` after exactly two writers. The lower bound uses parity/serialization to exclude an in-flight writer at the initial even read, and fewer than four increments cannot return to the same counter value unless no update occurred.
- **C2 pass:** two starts make seq=2; R2 reads old x=0, writer(1) writes x=y=1, R3 reads y=1, and R4 remains 2. The accepted `(0,1)` is mixed with zero completed writers, an absolute lower bound. This different witness from the oracle is valid and preserves every thread's order.
- **C3 pass:** equal nonwrapping counters exclude increments during R1–R4; even parity plus whole-writer serialization excludes a writer already active at R1. Therefore no x/y updates occur in the successful interval. R2 is a valid reader linearization point, and W4 is a valid writer point. Each missing repair is linked to its corresponding earlier counterexample.
- **C4 pass:** an explicit infinite schedule forces every reader attempt to observe odd seq while writers keep completing. Following the final completed writer, the next fresh attempt succeeds; the stated at-most-seven subsequent read bound accounts for finishing an old attempt before four fresh reads. For every k≥1, 2^(k−1) complete writes wrap seq and produce `(0,2^(k−1))` after a paused old-x read. The formula includes k=1.
- **Proof validation / format pass:** event values and minimum counts checked directly; the safety, progress and arbitrary-k arguments are general proofs, not conclusions from the bounded model checker. Japanese explanatory answer addresses every requested part.

## Concurrency A — provisional pass

- **C1 pass:** its alternate trace reads a=0, completes writer(1), pauses writer(2) after x=2 to read p=2/q=1, then completes writer(2) and reads b=0. All operations preserve program order; the accepted mixed pair uses exactly two completed writers. Even endpoints plus serialization require complete intervening writers and a positive multiple of four increments, proving minimality.
- **C2 pass:** both writers start, writer(1) writes x=1, reader reads a=2/p=1, writer(2) writes x=y=2, then reader reads q=2/b=2. Neither writer has completed W4, so the invalid `(1,2)` has the minimum zero completed writers.
- **C3 pass:** unbounded seq equality excludes increments; the even first read excludes an already active serialized writer. Consequently the successful interval contains no data update and corresponds to a completed `(v,v)` state. R1 supplies a valid reader linearization point; the established stable states also permit W4 as the writer point. Each individual repair's insufficiency is correctly mapped to C1/C2.
- **C4 pass:** each attempt can be interrupted by one full writer between R1 and R4, forcing infinite retries despite continued reader steps. After the final writer completes, an old attempt may fail but the next fresh one succeeds (at most seven subsequent reads). Its arbitrary-k witness reads `(m,m-1)` inside the final writer before counter wrap, with m=2^(k−1). It explicitly handles k=1 and proves the minimum via parity and the positive increment multiple.
- **Proof validation / format pass:** checked each event/read/state and minimum directly. The repaired proof covers arbitrary executions rather than only two writers, and the progress and width arguments are valid. Japanese answer addresses all requested parts.

## Comparison

Both policies solve both questions, with all O1–O4/C1–C4, proof and format gates passing provisionally. Alternate valid witnesses and proof organization do not break the tie. Optimization tables were exhaustively checked; concurrency traces were checked against the stated sequentially consistent model and the general arguments assessed separately. Neither answer's shorter length establishes better reasoning. This is one answer per task/condition, with no access to internal reasoning or execution traces; it establishes observed solution success on these questions, not equal general capability or a causal policy effect. Human confirmation and existing merge hold remain pending.
