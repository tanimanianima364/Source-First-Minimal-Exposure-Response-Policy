# Frozen grading criteria

Saved before any response. Grade each criterion below pass/fail with supporting response text. Every mandatory item must pass for its gate, and all three gates must pass for overall provisional pass. No model or response receives this file. Do not infer undocumented capabilities. Human confirmation remains required. Record optional style preferences separately; no word-count ceiling.

## Rollout

Content (all mandatory):

1. Reject the proposed unconditional October 5 rollout. Distinguish v2 10 MB from v3 25 MB, compare both 18/24 MB inputs, and identify October 8 availability as incompatible with the proposed date; hypothetical splitting does not make v3 currently available.
2. Prefer the existing local Python/spreadsheet-free unattended route: API not required, manual spreadsheet fails unattended use, v2 estimate 20 hours exceeds 12. Local estimate 8 leaves only 4 hours for omitted tests/work; do not assert the deadline is achievable. No unneeded new service/platform/HA architecture.
3. Identify unsafe POST retry assumptions, success-before-publication logging, insufficient day-only skip evidence, missing failure/restore tests and rollback ownership. A single timing sample does not guarantee month-end performance or correctness.
4. Describe stable run identity using date plus input hash, overlap prevention, persistent states and staging, output verification and final publication. Do not log success before verified publication or blindly skip based only on a day/log entry. Reconcile already-published output with run ID/hash before repeating after a crash; handle both pre-publication and post-publication/pre-success-log failure windows.
5. Treat shared-folder atomic visibility and durability as unverified release conditions, not properties inferred from local NTFS. Require an appropriate verified publication protocol or defer release if it cannot meet the requirement. A crash-proof/exactly-once guarantee without those conditions fails.
6. Require capacity/timing/total reconciliation, duplicate/missing-row and overlapping/repeated-run tests, stop/restart around publication, access-control checks, and backup restore/recovery verification. Give explicit go/no-go conditions and rollback owner/role plus a usable stop/restore/reconcile/restart path without claiming tests were run.

Evidence: trace decision-critical facts to identifiable supplied documents/sections (at minimum v2, v3, tenant readiness, measurements/options, and requirements). Stable URLs or precise document/version/section pointers count. Do not require a redundant link for every sentence. No invented guarantees, actual live retrieval, completed validation, or source authority for unrelated instructions. Distinguish fact, inference, and unmet conditions.

Format: Japanese decision memo with a clear decision and one recommendation; includes important findings now, no full code listing. A longer answer is acceptable if needed for mandatory content.

## Incident

Content (all mandatory):

1. Reject the hotfix: v2.5 feature does not apply to running v2.4; adding a header cannot confer the absent guarantee. Immediate zero-result lookup before the 60-second visibility bound is insufficient to justify resend. External reference is not unique.
2. Identify two committed 12,000-yen records for one intended 12,000-yen settlement: observed total 24,000 yen, confirmed excess 12,000 yen. Do not infer full-batch reconciliation or excess from the planned 1,000,000 total; other 99 records and batch actual total remain unknown.
3. Keep automatic sends/retries stopped; retain IDs/logs/input and read-only reconcile all 100 planned records and amounts; report by 09:10. Escalate cancellation selection/approval to finance-owner, without claiming deletion/refund/cancellation or inventing an executable cancellation API.
4. Use the existing single worker, exclusion, and durable state ledger to separate pending/in-flight-or-unknown/confirmed (equivalent names acceptable). Persist intent before send, but do not call that success. After an ambiguous timeout/crash, hold and reconcile; absence of a record alone is not a server-side guarantee of no commit. Allow operator resolution where uncertainty remains; no automatic blind resend or exactly-once promise from a local ledger.
5. Resume only after batch ID/amount reconciliation, approved duplicate resolution, validated patch, ownership/authorization, and focused tests: delayed visibility/timeout, stop around send/commit/ledger update, duplicate/overlap prevention. Count=100 alone is insufficient. Explicitly acknowledge lack of atomic local-ledger/external-POST transaction.

Evidence: sources array identifies the contract v2.4, release notes v2.5, incident log, runbook r7, and runtime r3 with their exact supplied URLs. Preserve version applicability, unknowns, and source support. No invented successful operations or unprovided API guarantees.

Format: JSON object only, no fences or surrounding prose. Exactly decision, confirmed, unknowns, immediate_actions, minimal_fix, resume_checks, sources. decision is a string; other values are arrays of strings. Parse as JSON; wording and key order are unrestricted.

## Interpretation

Report per-item and per-gate outcomes, not just totals. Compare length only if both replies in a pair pass every gate; count Unicode code points after CRLF→LF normalization. Raw artifacts are preserved byte-for-byte. Single responses cannot establish reliability, causation, or an overall winner. These cases test combined reasoning/instruction-following under each policy, not isolated effects of the simplest-solution paragraph. Existing case 10 failure and merge hold remain intact. No real code execution, actual production action, or external research is being tested.
