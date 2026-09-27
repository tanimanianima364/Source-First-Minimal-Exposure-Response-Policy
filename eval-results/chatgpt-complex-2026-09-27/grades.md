## Rollout A

Content 1–5: pass. Rejects October 5/v3 dependency, calculates at least 2/3 v2 chunks for 18/24 MB, contrasts 20 hours with the 12-hour limit and leaves only 4 for omitted work on the 8-hour local path. Identifies retry and log-before-publication failures. Uses date+input hash, scheduling/locking, staged outputs, durable audit information, output-hash reconciliation after publication-before-log interruption, and rejects automatic overwrite on mismatched output. Shared publication behavior is a pre-release condition rather than inferred from local NTFS.

Content 6: fail. Section 7 enumerates stop/retry/publication/hash/access tests but not concrete input-to-department total reconciliation, duplicate/missing input-row tests, or overlapping-start tests. Section 5 proposes exclusion but does not test it; listing audit counts is not an acceptance check. Section 9 makes backup restoration testing conditional on choosing backup-based rollback, whereas the frozen criterion requires it. Roles and stop/restore/restart directions are present, so the failure is the incomplete acceptance set, not total absence of rollback planning.

Evidence: pass. The fact table and closing source list identify the requirements, v2/v3 manuals, tenant readiness, and options/measurements with versions and sections. Precise source pointers satisfy the rubric; lack of URLs alone is not a failure for this task. Claims about runtime measurements and untested shared storage are qualified.

Format: pass. Japanese decision memo, one recommended local path, no full code. It is repetitive and opens with a preamble, but the frozen rubric has no strict length ceiling; do not convert that style preference into a gate failure.

Overall: provisional fail (content 6). Do not rank its brevity against B unless both pass.

## Rollout B

Content 1: fail. It rejects the October 5/v3 dependency, identifies October 8, states v2 10 MB and correctly computes 18/24 MB chunk counts, but never states v3's 25 MB limit. The frozen criterion explicitly requires that version/capacity comparison. This is an omitted comparison fact, not an incorrect recommendation to use v3.

Content 2–5: pass. It recommends the existing local unattended path, uses 20>12 and 12−8=4, preserves test-budget uncertainty, identifies retry/day-log hazards, and proposes locking, input-set hash/date identity, staging, verification and success-after-publication. It handles publication-before-log failure and does not infer shared-folder properties from local NTFS. The arrival manifest and earlier readiness deadline are proposed prerequisites, not claims that the fixture already supplied them. Its distinction between processing omissions and undefined business record keys is appropriate.

Content 6: fail. It includes known-answer correctness, missing/duplicate department-file checks, explicit two-start testing, stop/restart, shared-reader/power checks, ACL checks and a rehearsed rollback path. However, backup restoration testing is conditional: “現行バックアップを監査記録保全に依存するなら”. The frozen gate requires backup restore/recovery verification before release. Calling untested restore an uncertainty does not satisfy that acceptance criterion. No additional failure is inferred solely from missing business duplicate keys that the fixture never provided.

Evidence: pass. Table entries tie decision facts to unique fixture identifiers T, V2, R, M and P, with full document/version names in its final source list. These pointers let the supplied facts be traced; the gate does not require URLs for this memo. v3's missing capacity is counted under content 1, not double-counted as invented evidence.

Format: pass. Japanese memo, one recommended implementation, no full code. Extra repetition is a style observation, not a newly introduced failure criterion.

Overall: provisional fail (content 1 and 6). No brevity winner is reported for the failed pair.

## Incident B

Content 1–2: pass. Rejects v2.5-header-on-v2.4 assumptions, immediate zero-result retry, pre-send success and count-only recovery. Computes the ext-731 observed total as 24,000 yen and excess as 12,000 yen, while keeping the other 99 records and batch actual total unknown.

Content 3: fail. It maintains the sending stop, orders full read-only reconciliation, records s101/s102, escalates cancellation to finance-owner and reports by 09:10. However, it never instructs preservation of the original request/timeout logs and batch input as incident evidence. Fetching/reconciling data and recording duplicate IDs does not explicitly preserve those original artifacts. This is a narrow missing immediate-action item under the frozen criterion, not an unsafe instruction to cancel records.

Content 4–5: pass. READY/IN_FLIGHT/CONFIRMED/UNKNOWN-HOLD and durable pre-send intent separate work from success; the known atomicity gap is acknowledged. Unknown states cannot automatically resend and require reconciliation/human release. It does not claim zero results after 60 seconds create a server guarantee. Tests cover timeout, restarted in-flight/unknown state, delayed visibility, and concurrent send exclusion; reconciliation and finance approval gate resumption. Restarting in-flight state covers the ambiguous send/commit-to-ledger interval without requiring exact state names.

Evidence: pass. All six supplied documents have their proper names/versions and exact URLs in sources. No invented cancellation endpoint or completed action.

Format: pass (JSON parse, exact seven keys and value types verified separately).

Overall: provisional fail (content 3).

## Incident A

Content 1–2: pass. Rejects the hotfix's version and visibility assumptions, states two committed 12,000-yen records and one excess record/12,000 yen, and leaves the other 99 and actual batch total unknown. It does not print “24,000” separately, but its explicit two-times-12,000 description uniquely identifies that observed total; semantic arithmetic equivalence is accepted, not a requirement for an exact numeral string.

Content 3: fail. Like B, it maintains the stop, orders read-only full reconciliation, records duplicate IDs, escalates to finance-owner and reports by 09:10, but does not explicitly preserve the original batch input and request/timeout logs. This is the same narrow omission and is graded identically.

Content 4–5: pass. Durable intent, in-flight/unknown state, exclusion and human resolution replace blind retries. It acknowledges both local/external transaction separation and absence of server exactly-once. The tests cover delay, interrupted in-flight recovery, overlapping senders and duplicate query results; batch-level ID/amount reconciliation and approved duplicate disposition gate restart. The interrupted in-flight recovery covers the ambiguous commit-to-ledger interval; the rubric does not require one exact test-list phrasing.

Evidence: pass. All required document names, versions/revisions and URLs appear correctly in sources; no executed refund/cancellation or invented API is claimed.

Format: pass (complete JSON parse, exact seven keys/types).

Overall: provisional fail (content 3).

## Grading limits

These grades enforce the predeclared checklist, including evaluator-selected requirements such as unconditional backup restore verification and explicit forensic preservation. A failed gate is not proof that every recommendation is wrong or that a conditional restore policy is unsafe in every deployment. Rollout B's omitted v3 capacity does not invalidate its main decision to avoid v3. Both incident answers reach the correct primary decision and excess amount. Preserve the failures without promoting them into an overall policy ranking. No all-pass pair exists, so no brevity winner is calculated.
