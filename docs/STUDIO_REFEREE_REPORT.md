# Scenario Studio independent referee

`backend/studio/referee.py` implements `verify(model, result, events=None)` using only Python's standard library. It imports no compiler, schema, engine, simulation, or shared validation helper. `tests/test_studio_referee.py` constructs its primary model and receipt by hand, without invoking the scheduler or schema.

## Replay and accounting

The referee independently validates the bounded model, IDs, integer types, resource skills/capacity, material references, dependency graph, releases/due times, event types and outage bounds. It reconstructs every worked minute from segments, counts requested simultaneous capacity units, sums overlapping losses with a zero floor, checks retained resource pools, and rejects overlapping or unmerged task segments. Completions derive from exact required elapsed work; completion markers cannot create work. Dependencies must physically finish before dependent work begins. First start debits materials once, including unfinished tasks. Actual resource-unit minutes determine cost and budget use. All twelve supplied metrics must exactly match recomputation; bools are not accepted as integer metrics.

Configured `model.events` remains part of the canonical model hash. An explicit effective event list, including the empty list, is checked separately and included in the evidence digest. The evidence digest includes the configured model, effective schedule, required result fields, and recomputed metrics. API annotations such as `verification` and `compute_seconds` do not change it. Nonfinite or nonserializable physical evidence cannot receive a valid receipt. Early rejection marks unfinished replay checks as not passed, with an explanatory detail.

## Hand calculation and adversarial coverage

The primary case has a two-unit bench costing 7 cents per unit-minute. Task A needs three elapsed minutes at two units, pauses through a two-minute partial outage, and finishes at minute 5. Task B depends on A, needs two minutes at one unit, and finishes at minute 7. Expected cost is `(3*2 + 2*1)*7 = 56`, work is 5 elapsed task minutes, one task is on time, and the priority task is late. Repeated canonical evidence gives the same digest.

Tests tamper with phantom task/resource IDs, units, outage work, same-task and pool overlaps, dependencies/releases, completion times/missing/duplicate markers, overwork, metrics/costs/model hash, booleans, stock/budget, unsupported outages, loss bounds, cycles/dangling references, incompatible skills, duplicate IDs, horizon/schema bounds, malformed top-level values, nonfinite evidence, and API metadata. Additional cases cover overlapping outages, counterfactual `events=[]`, resumed work consuming materials once, partial unfinished work consuming materials, and release at the hard horizon leaving legitimate unserved demand.

## Observed validation

- Initial test run failed collection because the referee module did not exist; implementation followed that observed RED.
- A metadata-stability regression failed before the digest was restricted to the shared required result fields, then passed.
- Boundary tests exposed release-at-horizon rejection and missing duration/title bounds before their fixes.
- A nonfinite playback metadata test failed before canonical serialization failures became invalid receipts.
- An early-rejection test failed before unexecuted checks stopped reporting success.
- Final owned run: `.venv/bin/python -m pytest tests/test_studio_referee.py -q` — **48 passed**.
- Full Python run: `.venv/bin/python -m pytest -q` — **174 passed**, with four dependency deprecation warnings (Starlette/httpx and SWIG types).
- Direct integration sweep: all three compiler templates × three policies × two adaptation flags × configured/empty event schedules — **36 valid receipts**.

## Rulings and limits

`makespan` is the latest actual segment end, including unfinished work; an empty trace has makespan zero. Release exactly at the horizon is allowed as unserved demand. Outage/model hash behavior and API metadata hashing were coordinated with the engine/API owners.

Physical validity is independent of policy quality. The referee does not duplicate the scheduler's tie-breaking, prove optimality, or audit whether a heuristic could have chosen better work. Same-resource retention and physical constraints are checked, while narrative playback summaries are typed annotations rather than authoritative physical events. This is a finite synthetic-model validation suite, not proof of real-world safety or exhaustive verification. Browser use, publication, event eligibility and submission were not verified by this task.
