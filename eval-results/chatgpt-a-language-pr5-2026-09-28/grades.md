# Provisional grades

AI-assisted grades, pending human confirmation. Grade against the unchanged criteria in plan.json; these known tasks and one run per condition do not establish a language effect or universal ranking.

## Case 10

| Condition | Content | Evidence | Format | Basis |
| --- | --- | --- | --- | --- |
| PR5 | Pass | Pass | Pass | Chooses v3; states 25 MB vs 10 MB and asynchronous jobs; names both manuals/Export limits with matching URLs; proposes operational checks without claiming completed tests. |
| A-ja | Pass | Pass | Pass | Same correct decision and limits; table preserves async behavior; identifies both manual sections and URLs; checks scope/size definition/operational requirements. |
| A-en | Pass | Fail | Pass | Correct limits/choice/async behavior and bounded pre-adoption checks, but no manual titles, section identifiers or URLs. |

[PR5](case10-PR5.md) and [A-ja](case10-A-ja.md) include both `https://example.invalid/q/v2#export-limits` and `https://example.invalid/q/v3#export-limits`. [A-en](case10-A-en.md) ends with the limits of the supplied information and contains neither URL nor manual/section attribution. Its concision cannot offset the evidence failure; exclude it from brevity comparisons.

## Coding — A-ja

[Coding answer](coding-A-ja.md), [unaltered extracted files](coding-A-ja/extraction.json), [independent tests](coding-A-ja-independent.log), [author tests run by evaluator](coding-A-ja-author.log).

The frozen C1–C6 harness passes; subsequent literal-input-domain inspection finds a C1 limitation below, so the complete coding task is not an unqualified pass. The fixed independent harness passes 9/9; the answer's own suite passes 10/10 in the evaluator's Python 3.12.14 offline namespace. The model reports a separate Python 3.13.5 run with 10 tests; that report is not independently attested by our execution.

- C1: tuple-based operation validation safely rejects `op=[]`; keys, IDs, integer/bool/range checks precede replay, and unknown SKUs are checked in the transaction before request lookup.
- C2/C3: `BEGIN IMMEDIATE` covers state changes and durable canonical-command/status records. Reservation existence precedes stock checks, terminal rows are retained, and every business outcome is recorded. All corresponding independent traces pass.
- C4/C5: independent precommit-kill, committed-but-undelivered replay, full rollback, simultaneous requests/transitions and bounded external-lock checks pass. Connections close in `finally`; results return only after COMMIT. These tests do not simulate arbitrary storage failure or every schedule.
- C6: `snapshot()` explicitly begins a read transaction before both SELECTs and commits afterward. The independent consistency stress passes. The author suite uses independent spawned processes with a Barrier, bounded joins and exit-code checks, but does not itself test the independent harness's crash/snapshot cases.

## Coding — A-en

[Coding answer](coding-A-en.md), [extraction](coding-A-en/extraction.json), [independent tests](coding-A-en-independent.log), [author tests](coding-A-en-author.log).

C1–C6 provisionally pass. The frozen independent harness passes 9/9 and the author suite passes 13/13 in the offline evaluator. The answer reports a separate Python 3.13.5 execution; we independently ran the extracted blocks in Python 3.12.14, not the downloadable sandbox files.

The operation type guard precedes dict membership. Canonical binary encoding fixes field order and uses length prefixes; the storage encoding supports lone surrogates as well as ordinary Unicode. The SKU preflight precedes replay and runs outside the write transaction; this is sound for the task's immutable SKU set. `BEGIN IMMEDIATE` serializes mutations and records each original result; commit precedes return and exception rollback is guarded by `in_transaction`. `snapshot()` encloses both reads in one explicit transaction. Concurrency/recovery evidence is bounded by the fixed independent tests, not an arbitrary-failure guarantee.

## Post-hoc valid-string diagnostic

After reading A-en's explicit surrogate handling, the evaluator added one [diagnostic](unicode-diagnostic.py), separately from the frozen nine-test harness. The fixture allows any Python `str` of length 1–128; it does not restrict strings to Unicode scalar values. A lone-surrogate string has length one and meets that literal input contract. Python documents the distinction between a surrogate in `str` and its UTF encoding in [codecs / Error Handlers](https://docs.python.org/3.12/library/codecs.html#error-handlers). The diagnostic initializes such a SKU, reserves it with surrogate-containing IDs, replays the request, and checks the snapshot. Apply the same diagnostic to all three candidates; do not repair generated code.

[A-ja fails](coding-A-ja-unicode.log) in `init_db` with `UnicodeEncodeError`; [A-en passes](coding-A-en-unicode.log). This is a narrow C1 valid-input-domain failure for A-ja despite 9/9 on the frozen harness. It does not show stock corruption or ordinary-input failure, and was discovered after seeing answers, so it is exploratory evidence, not a predeclared benchmark win. [PR5 also passes](coding-PR5-unicode.log); all three candidates received the identical diagnostic. The runner is the unchanged isolated runner from plan.json, copied to a temporary directory with this diagnostic named `test_contract.py`.

## Coding — PR5

[Coding answer](coding-PR5.md), [extraction](coding-PR5/extraction.json), [independent tests](coding-PR5-independent.log), [author tests](coding-PR5-author.log).

C1–C6 provisionally pass. The frozen independent harness passes 9/9; the evaluator-run author suite passes 13/13; the same post-hoc lone-surrogate diagnostic passes. The model's reported Python 3.13.5 run is separate from these Python 3.12.14 checks.

Input validation rejects invalid types before set membership and validates SKUs before replay. BLOB identifiers with `surrogatepass` preserve accepted strings; canonical JSON uses fixed keys and ASCII escaping. `BEGIN IMMEDIATE` protects reads, decisions, writes and persisted outcomes through COMMIT; exception handling rolls back and closes the connection. Both snapshot queries finish inside one explicit read transaction. The author tests use independently spawned processes with controlled starts and bounded joins. These code paths and bounded checks support the requested API guarantees under the stated SQLite/local-storage assumptions, not arbitrary failures or all schedules by enumeration.

## Coding summary

| Condition | Frozen independent checks | Evaluator-run author tests | Separate post-hoc diagnostic |
| --- | --- | --- | --- |
| PR5 | 9/9 | 13/13 | Pass |
| A-ja | 9/9 | 10/10 | Fail: lone-surrogate SKU initialization |
| A-en | 9/9 | 13/13 | Pass |

The frozen harness found no difference in ordinary contract traces. The narrow exploratory boundary does not establish a general English advantage. All research: not graded yet.
