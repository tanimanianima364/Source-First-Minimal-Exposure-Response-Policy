# Coding verification — provisional

The [frozen rubric](rubric.md) and nine [independent checks](checks/README.md) were fixed before collecting either candidate. Extracted files preserve the exact bytes inside the first reply's two Python code blocks; no repairs, follow-up prompts or dependencies were added. Extraction offsets and SHA-256 values are recorded per candidate. Both independent and author tests run separately in the offline sandbox with CPython 3.12.14 / SQLite 3.53.1. Human confirmation remains pending.


## A

[Reply](coding-A.md), [extraction](coding-A/extraction.json), [implementation](coding-A/inventory.py), [author tests](coding-A/test_inventory.py), [independent log](coding-A/independent-tests.txt), [author-test log](coding-A/author-tests.txt).

Independent checks: **8 methods pass; C1 errors on one invalid-input subtest**, exit 1, no skips. Author suite: **11/11 pass**, exit 0. Both logs are evaluator executions. The reply separately reports Python 3.13.5, 11 tests and 3.395 seconds; those are model-reported, not our measured environment/results. Our author-suite run uses Python 3.12.14 and takes 0.319 seconds; this difference is not a policy speed comparison.

| Criterion | Grade | Concrete evidence |
|---|---|---|
| C1 API/input | fail | `apply_batch(db, [{"request_id":"q","op":[],"reservation_id":"r"}])` raises `TypeError`, although the contract requires `ValueError` for invalid operation types. `_validate_commands`, line 83, tests membership in a set before ensuring `op` is a string. The frozen C1 subtest catches the failure; other C1 subtests complete. Validation occurs before DB connection, so this failure does not corrupt inventory. |
| C2 transitions | pass | The C2 check passes, including terminal IDs, conflict-before-stock, cancellation restoration and no second shipment decrement. `apply_batch` reads/checks stock and updates it under the same `BEGIN IMMEDIATE` writer transaction. |
| C3 durable replay | pass | The C3 check passes for successes, all failure statuses, reordered keys, batch duplicates and fresh-process replay. Canonical JSON and original status in `requests` are committed with state changes; replay does not recompute the result. |
| C4 atomicity/recovery | pass | Both C4 checks pass: rollback of new records after a later invalid/conflicting command or hook exception, termination while paused before commit, and retry after commit without result delivery. Prior committed records remain. `_rollback`, the precommit hook, commit-before-return and connection `finally` match these results. |
| C5 concurrency | pass | All three C5 checks pass: spawned-process oversell/identical-request/cancel-ship races and finite external-lock failure without partial state. `_connect` sets a 5-second timeout. The author suite additionally contains three Barrier-controlled process races, bounded joins, child exit-code and queue error checks. |
| C6 snapshot/proof/tests | pass | `snapshot` explicitly begins a transaction encompassing both fully fetched SELECT results before commit. The C6 stress check verifies conservation during observed concurrent snapshots and the final 150-reservation count. Author tests exercise failure rollback and real process contention, but miss the invalid unhashable `op` case and do not replace the independent crash/snapshot checks. |

Full coding task: **provisional fail**, specifically the public invalid-input exception contract. No observed concurrency, replay, recovery or inventory-safety failure follows from this error. Preserve the failed first answer; do not repair it and report the repaired code as the original result.

The candidate's author tests bound their joins but do not explicitly terminate children on their own assertion-failure paths. They completed in this run; the evaluator's external sandbox deadline supplies cleanup if a future run stalls. This limits standalone test-runner robustness, not the observed passing process-race results.

## B

[Reply](coding-B.md), [extraction](coding-B/extraction.json), [implementation](coding-B/inventory.py), [author tests](coding-B/test_inventory.py), [independent log](coding-B/independent-tests.txt), [author-test log](coding-B/author-tests.txt).

Independent checks: **9/9 pass**, exit 0, no skipped or unverified observations. Author suite: **11/11 pass**, exit 0. These are evaluator executions. The reply separately reports Python 3.13.5 and 11 passing tests; that runtime and execution claim are model-reported, not independently established by our run.

| Criterion | Grade | Concrete evidence |
|---|---|---|
| C1 API/input | pass | Import and public return shapes pass `test_C1_shapes_and_input_validation`. `_validate_command` checks exact keys, IDs, strict integer bounds and operation type; all syntax is checked before opening the transaction, and unknown SKUs are checked before replay. `_key`/`_from_key` use BLOB identifiers with `surrogatepass`; no external packages. |
| C2 transitions | pass | `test_C2_transitions_and_precedence` checks conflict-before-stock, cancellation restoration, shipment without a second decrement and terminal IDs. `apply_batch` checks reservation existence before conditional stock decrement; cancellation and shipment require RESERVED. Conservation also survives the concurrent and snapshot checks. |
| C3 durable replay | pass | `test_C3_replay_success_failures_order_duplicates` checks saved successes/failures, reordered keys, duplicates and restart. Canonical JSON and the original status are stored in `request_log` in the same write transaction; replay returns that status without re-evaluating current inventory. |
| C4 atomicity/recovery | pass | Both C4 checks pass: later invalid/conflicting commands and injected exceptions leave no new records; terminating a worker paused before commit leaves no effect; retry after commit without result delivery applies once and returns the original result. `BEGIN IMMEDIATE`, hook before `commit`, return after commit, rollback on `BaseException` and connection closure agree with the explanation. |
| C5 concurrency | pass | All three C5 checks pass with independent spawned processes: oversell, identical request and cancel/ship races; external held lock produces a bounded failure without partial state. `_connect` specifies a 5-second busy timeout. The candidate's own process tests use readiness/start events, bounded joins, child exit checks and propagated exceptions. |
| C6 snapshot/proof/tests | pass | The C6 stress check verifies conservation in observed concurrent snapshots and checks the final count of 150 reservations. `snapshot` begins an explicit read transaction before either SELECT and commits after both, supplying the transaction argument that finite stress alone cannot prove. The author suite includes failures and real process contention; its 11 tests alone do not cover all independent recovery/snapshot obligations. |

Full coding task: **provisional pass**. The code and explanation agree on transaction, replay and snapshot boundaries. This is bounded evidence under the stated API and environment, not proof against arbitrary disk faults, every process schedule or a true mid-commit kill. The recovery check explicitly distinguishes a precommit kill from loss of a response after commit.
