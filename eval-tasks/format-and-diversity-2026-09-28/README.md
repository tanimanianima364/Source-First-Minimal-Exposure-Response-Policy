# Format and task-diversity comparison

Prospective comparison of PR #5 (`682f08a`) and Japanese A (`29ad511`):
11 task types, one fresh response per condition, 22 planned replies. The first
three reuse EVALS cases 2a, 3a and 1b. Eight new tasks exercise native UI choice,
exact CSV aggregation, parsing, safe SQL, shared-cause repair, requested detailed
explanation, numerical calibration, and distributed rate limiting.

`plan.json` freezes inputs, rubric hashes, order and conditions. Each `.txt` is
the complete submitted message; `cases.json` also contains evaluator-only gates.
Never send the gates. No answer has been collected when this plan is registered.
All synthetic tasks keep external search OFF. Terminal LF removal applies only
to policy installation; submitted task files have no terminal LF.

## Reference and adaptation

Inspected [Ponytail](https://github.com/DietrichGebert/ponytail/tree/e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156)
at `e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156`:

- `benchmarks/promptfooconfig.yaml`: CSV aggregation and rate limiting.
- `benchmarks/behavior.yaml`: hardware calibration, requested explanation,
  and duration parsing with runnable checks.
- `benchmarks/agentic/tasks.py`: native date inputs, SQL safety, shared amount
  parsing, and correctness checks separate from safety checks.

The new Japanese fixtures and explicit contracts are original adaptations of
these task categories, not copied benchmark implementations or a reproduction
of Ponytail's reported results. Unlike its agentic benchmark, this measures
chat answers and generated artifacts, not autonomous repository editing.
Ponytail is a design reference, not a third experimental condition.

## Scoring

Keep content, evidence fidelity, and format separate. Any failed required gate
fails the task. Run Python artifacts in isolation using the repository's existing
runner; report independent checks separately from model-provided checks. Evaluate
HTML and design answers against the explicit rubric. A runnable example is not
proof the model actually ran it. Do not infer measured safety from finite tests.
No source citation is required solely because a synthetic single-source fixture
was supplied; fabricated retrieval or unsupported assertions fail evidence.

Only compare answer length among fully passing, eligible paired responses. Do not
aggregate heterogeneous checks into a universal winner. One response per cell is
a diagnostic, not a success-rate estimate. This comparison changes language and
policy simultaneously. Human grade confirmation remains a separate requirement.
Preserve failed and interrupted replies, no silent retries or replacements.

Known previous research, complex coding and source-attribution results remain
separate; this expansion does not rescore them or replace their failures.
