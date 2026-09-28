# PR5 versus Japanese A: formats and task diversity

All 22 replies collected; human grading confirmed for both 3a replies (2026-09-28);
the remaining 20 replies retain provisional grades.
[Human grading worksheet and resumed cross-check](HUMAN-REVIEW.md) links each
response, criterion summary and execution evidence; 3a is confirmed and the other human checks remain pending.
Nine pairs follow the planned order; two are reference observations excluded
from comparison because their order was reversed. The
[preregistered plan](../../eval-tasks/format-and-diversity-2026-09-28/plan.json)
was committed as `baf7f86` before the first submission. It contains 11 task types
and 22 planned responses, adapted from Ponytail's categories for chat evaluation.
The canonical policy is unchanged. This is a cumulative policy-and-language
comparison, not a language-only experiment or Ponytail replication.

## Observed outcomes

| Task | PR5 | Japanese A |
|---|---|---|
| Summary | Pass | Pass |
| JSON only | Pass | Pass |
| Top two findings only | Pass | Pass |
| Native date input | Pass | Pass |
| CSV exact aggregation | Frozen checks pass; large-number diagnostic fails | Same |
| Duration parser | Pass | Pass |
| Safe SQL | Frozen checks pass; row-factory diagnostic fails | Pass, including row-factory diagnostic |
| Shared parser repair | Pass; supplied pytest 42/42 | Pass; supplied pytest 38/38 |
| Detailed explanation | Pass | Pass |
| Calibration (reference only) | Per-response pass | Per-response pass |
| Distributed design (reference only) | Content fail: equal-timestamp test missing | Same |

All three gates pass where the table says Pass. No observed format failure in
these three original cases supports the concern about PR5's rigid blocks here;
this does not establish reliability across repetitions or other tasks. The
shared CSV defect prevents a full correctness claim despite fixed tests passing.
The distributed answers propose plausible central atomic sliding-window designs,
but concurrent requests need not have identical timestamps. Neither test plan
explicitly ensures equal insertion scores, so neither satisfies that fixed gate.
Redis was not deployed or load-tested.

### Protocol deviations and cleanup

The [timestamp audit](order-deviations.json) found calibration was submitted
PR5→A-ja instead of A-ja→PR5, and distributed A-ja→PR5 instead of PR5→A-ja.
This was an evaluator ordering error discovered after collection. The prospective
plan remains unchanged. **Both pairs are order-deviation reference observations**,
excluded from brevity comparisons and improvement/regression judgments. Their
per-response grades remain recorded; no replacements were generated.

Original eight switches and the original empty custom instructions were restored
and read back ([restoration](restoration.json)); all 23 owned windows were closed
([closure](closed-windows.json)). Unrelated windows were preserved. Restoring the
controls does not claim restoration of memory contents. Pro was not used.

## Conditions and evidence

PR5 is `682f08ad68a1ec03a57ecec4e0ed8ee5b2893472:PROMPT.md`;
A-ja is `29ad511c447a5cb15c30cde7cb2d0a6b9aeb8218:PROMPT.md`.
Both are saved in the same custom-instructions field, with exactly one terminal
LF removed by the UI, and read back after reload. ChatGPT at chatgpt.com,
GPT-5.6 Sol / Extra High (4/5), Personalized temporary conversations; no Pro.
Eight recorded memory/history/tool switches are OFF before and after each answer.
Existing style settings are unchanged. Account tier was not independently rechecked in this run. Hidden model snapshot, sampling controls,
and server-side instruction delivery are unavailable for independent inspection.

OpenAI's [temporary-chat documentation](https://help.openai.com/en/articles/8914046-temporary-chat-in-chatgpt)
and [memory documentation](https://help.openai.com/en/articles/8590148-memory-in-chatgpt),
checked 2026-09-28 JST, support temporary-chat no-memory-update behavior and account
memory controls. Personalized mode preserves custom instructions. Limited service
safety context remains outside these controls. Settings readbacks do not prove
absence of every hidden personalization influence.

Raw clipboard replies, saved policies, input readbacks, model/mode screenshots,
control values and timestamps accompany the [manifest](manifest.json).
[Grades](grades.json) use the fixed gates. Characters count decoded Unicode with
CRLF normalized to LF, including Markdown; compare only passing eligible pairs.

The initial setup encountered unsaved-setting/reload dialogs; no input was sent
until persistence was verified. New-chat model defaults are explicitly selected
and checked. Preflight reload/model/composer availability failures were resolved without sending
or replacing answers. Before calibration/A-ja, a noncanonical saved value was
detected and reinstalled; exact readback was required before submission. The
unexpected text is kept private; no answer was collected under it. A transient
SQL/PR5 readback mismatch also resolved before submission. No retries based on answer quality are permitted.

## Limits

One reply per condition per purpose-selected, known task. Finite checks do not
prove all-input correctness, production safety, or causal policy effects. Previous
research/source-attribution failures retain their original records. These results
do not establish a full-suite pass or an overall winner. Remaining human grade confirmation
and policy adoption remain separate decisions.

## Execution notes

All code execution used the existing [offline namespace runner](../chatgpt-research-coding-2026-09-27/checks/run.py),
with extracted code read-only, network isolation and bounded resources. Python
3.12.14; rootcause's pytest examples use the already installed pytest 9.0.2 with
plugin autoload disabled. No dependency was added to the policy or its runtime.
[check_artifacts.py](check_artifacts.py) records the extraction and runs; run from
the repository root with a case and condition, e.g. `python3 eval-results/chatgpt-task-diversity-2026-09-28/check_artifacts.py duration PR5`.
Its runtime/dependency paths are specific to the recorded Linux installation.

Top-level Python code text is preserved with CRLF normalized to LF; indented explanatory
fragments are not programs. PR5 rootcause explicitly imports `amounts`, so its
implementation and test blocks are laid out as separate modules. Initial missing
pytest/module-layout logs are preserved as evaluator environment errors, not
model failures. The initial CSV/PR5 unittest-discovery attempt found no unittest
classes; its ordinary assert example was subsequently executed as a script.

CSV's [large-number diagnostic](decimal-diagnostic.py) was introduced **after**
the answers, applied identically to both, and kept separate from the frozen
checks. Both return `1.234567890123456789012345679E+29` where the exact result is
`123456789012345678901234567890.02`. Default Decimal arithmetic rounds at its
context precision. This violates the existing exact-sum requirement despite the
fixed checks passing. Originals were not repaired; no policy causation is claimed.

SQL's [row-factory diagnostic](sql-row-factory-diagnostic.py) was added after
review of `c1ad726`, applied identically to both unchanged extracted answers,
and run using the same offline runner (Python 3.12.14, SQLite 3.53.1).
With `conn.row_factory = sqlite3.Row`, PR5 returns `Row`, violating the existing
`tuple` contract; Japanese A returns the required tuple. Both return tuples with
the default factory. See [PR5 failure](sql-PR5-row-factory-diagnostic.log) and
[A-ja success](sql-A-ja-row-factory-diagnostic.log). Arbitrary custom factories
were not tested. Original replies, frozen checks and their successful logs are
unchanged. PR5's content grade is corrected to fail; the SQL pair is excluded
from passing-pair brevity comparisons. No causal policy effect is established.
To reproduce, copy the existing offline runner and this diagnostic (named
`test_contract.py`) into the same temporary directory, then run that `run.py`
with `sql-PR5` or `sql-A-ja` from this results directory as the candidate path.

[Calibration checks](calibration-check.py) implement the predeclared manual
criteria after extraction; they were not a preregistered executable test file.
Redis design grading is a paper review, not an executed load/fault test. The
primary references checked by the evaluator are Redis's [Lua atomicity](https://redis.io/docs/latest/develop/programmability/eval-intro/),
[range deletion](https://redis.io/docs/latest/commands/zremrangebyscore/) and
[server clock](https://redis.io/docs/latest/commands/time/) documentation.
The evaluated chats themselves did not browse.

The CSV/PR5 collection delay was a viewport issue: completion controls were below
the visible accessibility content. Scrolling to the bottom recovered the same
answer without regeneration. This is not recorded as model latency or failure.

## Passing-pair output length

Unicode character counts include Markdown and code, with CRLF normalized to LF.
This is output size, not tokens, cost, runtime or code quality. Failed pairs and
order-deviation pairs are excluded.

| Task | PR5 | A-ja |
|---|---:|---:|
| 2a | 164 | 189 |
| 3a | 59 | 59 |
| 1b | 126 | 147 |
| native | 527 | 580 |
| duration | 1866 | 2111 |
| rootcause | 3239 | 2783 |
| explain | 1830 | 2268 |

The smaller answer changes by task; these single observations do not identify an
overall winner or isolate English versus Japanese effects.
