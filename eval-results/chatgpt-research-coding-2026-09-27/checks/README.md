# Frozen coding acceptance checks

Run from the repository root with a directory containing only the verbatim extracted `inventory.py` and `test_inventory.py`:

```sh
python3 eval-results/chatgpt-research-coding-2026-09-27/checks/run.py /path/to/extracted
python3 eval-results/chatgpt-research-coding-2026-09-27/checks/run.py /path/to/extracted --author-tests
```

Both runs use Bubblewrap with a new network/PID/user namespace, no inherited environment, no repository/home/browser mounts, read-only candidate/check/runtime/library mounts and disposable scratch storage. CPU, address-space, process-count, descriptor and output/file-size limits apply; an external 180-second deadline kills the process group, and the PID namespace removes remaining descendants. Exit 124 is an execution timeout, not a passing test. The runtime is CPython 3.12.14. Only the two named candidate files are copied into the sandbox; no answer repairs or additional dependencies are supplied.

The nine independent unittest methods cover C1–C6 using the public API; no table names or SQL layout are assumed. Workers use the `spawn` start method, separate connections, readiness events, simultaneous start gates, pipes carrying failures and bounded cleanup. Recovery checks distinguish termination while paused before commit from termination after commit without delivering the function result. They do not test arbitrary mid-commit crashes, disk failure or power loss.

C6 snapshot stress checks the inventory conservation invariant while another process alternates committed reservations and cancellations. If the writer finishes before any sample, the final state is still checked and the concurrency observation is skipped with `SNAPSHOT_OVERLAP_UNVERIFIED`; scheduling alone is not a candidate failure. Passing finite stress does not prove coherence: inspect the transaction encompassing all snapshot reads. Also inspect author-test coverage, connection cleanup, transaction/replay ordering and the explanation separately. A passing author suite is not independent evidence. The external lock test observes an OperationalError for up to 12 seconds, then releases the lock; if no error appeared, it emits `LOCK_TIMEOUT_UNVERIFIED`. A longer legitimate timeout is not automatically wrong, but a finite retry/timeout bound must then be checked in source. The specification does not prescribe a numeric timeout.

Before collecting candidate answers, the suite was exercised against a private minimal SQLite reference and three independent mutations: dropped failure replay, commit instead of rollback on exception, and double-decrement on ship. The reference passes; each mutation fails the corresponding acceptance checks. `validation.json` records outcomes and code hashes. The private reference is validation scaffolding, not a required candidate design or part of either tested prompt. These checks are bounded contract evidence, not an exhaustive correctness proof or a defense against deliberate evaluator tampering.
