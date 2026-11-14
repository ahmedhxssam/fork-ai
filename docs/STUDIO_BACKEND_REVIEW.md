# Scenario Studio backend independent review

Reviewed 2026-11-14 against `docs/superpowers/specs/2026-11-13-scenario-studio.md`. Scope: `backend/studio/{schema,compiler,engine,referee,api}.py`, Studio tests, SQLite persistence, and the workflow/logistics route separation in `backend/main.py`. Reviewer changed no production code and made no commits.

## Verdict

The bounded compiler, schema, scheduler and independent physical referee passed the targeted review and fresh adversarial scheduling checks described below. Two P2 API issues were reproduced, fixed by the root, and independently reverified. **Final verdict: pass within this backend scope; no unresolved actionable findings.** No optimality, universal natural-language understanding, deployment, browser, or competition-eligibility conclusion follows from this review.

## Findings

### Resolved P2: Approval/export trusted mutable saved receipt metadata

Location: `backend/studio/api.py`, `fresh_evidence` (around lines 158–170).

Originally this function checked fresh physical evidence but compared only `valid` and `evidence_hash` against the stored receipt. Changing `worlds[0].verification.metrics.completed` to `999` while preserving the result's top-level metrics and receipt hash allowed both approval and JSON export (HTTP 200). The exported receipt presented 999 completed tasks. This matters because the UI and comparison consume `verification.metrics`.

Exact reproduction, run from the repository with `.venv/bin/python`:

```python
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
from backend.main import create_app

with TemporaryDirectory() as d, TestClient(create_app(d + '/review.sqlite')) as c:
    compiled = c.post('/api/studio/compile', json={
        'brief': 'Resource a skills=work\nTask a duration=1 skill=work'
    }).json()
    exp = c.post('/api/studio/experiments', json={
        'brief': 'Review', 'model': compiled['model'],
        'model_hash': compiled['model_hash']
    }).json()
    exp['worlds'][0]['verification']['metrics']['completed'] = 999
    c.app.state.store.save(exp)
    base = '/api/studio/experiments/' + exp['id']
    print(c.post(base + '/approve', json={
        'revision': 1, 'world_id': 'throughput'
    }).status_code)
    print(c.get(base + '/export').status_code)
```

The root implemented a full receipt equality check. Scoped rereview confirmed the `999` mutation now returns HTTP 409. However, ordinary Python dictionary equality still treats `True == 1 == 1.0`. Replacing the mutation above with `True` still produced approval/export HTTP 200 in the intermediate fix. Use canonical JSON equality/digests or type-aware equality; test both numeric corruption and boolean-for-integer receipt corruption. **Final scoped verification:** the final fix compares canonical receipt digests. Changing completed to `999`, `True`, or `1.0` now independently returns HTTP 409 for both approval and post-approval export; the original untampered receipt still approves and exports with HTTP 200. Direct database alteration is the attack setup, not an exposed HTTP write capability. This is defense against persisted evidence corruption, consistent with the existing tamper tests.

### Resolved P2: Cost normalization could reverse the locked specification's preference result

Location: `backend/studio/api.py`, `comparison` (around lines 82–85).

The locked spec describes cost divided by the supplied budget, with a fixed scenario maximum as the alternative. The implementation instead chooses the smaller of supplied budget and full-capacity work cost. A budget greater than physical maximum therefore changes the intended cost scale and can reverse the recommendation.

Exact reproduction:

```python
from backend.studio.compiler import compile_brief
from backend.studio.api import compute_experiment, comparison

model = compile_brief('''Horizon: 5
Budget: 1000
Stock: p=1
Resource a skills=work cost=1
Task short duration=2 skill=work materials=p:1
Task important duration=5 skill=work priority=3 materials=p:1''')['model']
worlds, _, _ = compute_experiment(model)
print(comparison(worlds, model, {'completion': 0, 'priority': .15, 'cost': .85}))
```

Observed: throughput wins with score −0.34; resilience/priority each score −0.7. Using the explicit 1000-cent budget gives throughput −0.0017 and resilience/priority 0.14575, an honest tie between those two. Honor an explicit budget (guard zero with a denominator of one), and use the fixed capacity maximum only when the budget is absent; add this ranking regression. **Final scoped verification:** the root implemented the specified explicit-budget denominator. The reproduction now returns the correct resilience/priority tie at 0.14575; regression tests cover the ranking change.

## Checks actually executed

- Initial Studio-only suite: **91 passed**, one Starlette/httpx deprecation warning.
- Full Python suite after the first receipt fix: **179 passed**. Final full Python suite after both fixes and new regressions: **182 passed**, four dependency deprecation warnings, 2.22 seconds. Command: `.venv/bin/python -m pytest -q`.
- Fresh deterministic random sweep, seed **991827**, **1,000** distinct models: 8–40-minute horizons; 1–4 resource pools with different skill subsets and 1–5 units; 1–15 tasks with DAG dependencies, varying release/deadline/priority/value/materials; scarce/free/zero budgets; and 0–7 overlapping outages. Reproducible script retained at `scripts/studio_backend_review_sweep.py`; executed before and after the fixes with `PYTHONPATH=. .venv/bin/python scripts/studio_backend_review_sweep.py`. Both sweeps passed.
  - **6,000** actual adaptive/control runs passed the independent referee and additional direct occupancy, budget, material, pool-retention, release/dependency, exact-work and completion assertions.
  - **3,000** nominal/no-outage-control pairs had equal segments, completions and metrics.
  - **3,000** nominal/actual pairs had identical work before the first outage (no future-outage peek).
  - **3,000** reversed-outage-order pairs had equal segments, completions and metrics.
- **160** result-field mutations using `None`, booleans, integers, floats, empty text, arrays, objects and NaN: no referee exceptions. Four accepted variants were legitimate unchanged values or allowed boolean adaptation/empty playback ledger values. Physical evidence remained authoritative.
- Safe-slug newline attacks (`a\n`, `a\r`, `a\r\n`) were rejected by schema validation.
- Receipt tamper reproduction above, scoped numeric/boolean retest against the intermediate fix, and final numeric/boolean/float approval and export attacks against the canonical-digest fix.
- Read-reviewed compiler unknown-line/attribute rejection and explicit narrative syntax; mandatory/default provenance; strict schema bounds/references; overlap loss summation; first-start stock consumption; cost-by-work; retained pool assignments; paused work; fixed-control predecessor slots; canonical hashes; current-revision mutation checks; idempotent request replay/conflicting-key rejection; and cross-kind route rejection. The executed suites cover these boundaries, including persistence and approval/export lifecycle.

## Limits

The independent referee proves physical feasibility and recomputed metrics for the declared model. It does not prove that an arbitrary feasible trace was generated by a named heuristic, that a schedule is optimal, or that playback narration is true; narration is not physical evidence. Random and hand-derived checks provide finite evidence, not exhaustive proof. The mutation lock protects the single application process; no multi-process race test was performed. Browser behavior, screenshots, reload recovery, public publication, and submission are outside this backend review.
