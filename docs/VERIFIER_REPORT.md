# Independent referee implementation and evidence

Implemented `backend/fork_engine/verifier.py` and `tests/test_verifier.py` without importing planner, simulation, route-validation or metric helpers. Production imports are Python standard library only. No engine/shared configuration files were edited by the referee worker.

`verify_world(scenario, result)` returns the agreed receipt, including `valid`, stable violation codes with relevant event IDs, recomputed metrics, seven inspectable check groups, `scenario_hash`, `event_hash`, and version `fork-referee-1.0`. The event hash covers the canonical combination of actual events, trajectories, and completed deliveries. Claimed `result.metrics` and `result.final_state` never supply verification values.

## Independently reconstructed rules

- Replay depot stock and per-vehicle, per-commodity cargo; move failed cargo into stranded custody; enforce integer quantities, global conservation, capacity including unused cargo, cold compatibility, and no transfer/rescue/unload.
- Require atomic whole-order deliveries, unique order and completion identities, matching physical completion and service-start evidence, and no manufactured delivery records.
- Check directed road identity, edge duration, actual integer metres, continuous locations, collinear monotonic path geometry, nonoverlapping movement, and physical departure/arrival evidence. A final `arrive` followed by an informational `return` represents one physical road completion.
- Validate loading duration/start manifest, service duration, hard completion windows, vehicle and volunteer shifts, return to depot, integer elapsed seconds, and horizon limits.
- Keep started loading/service locked through actual completion or failure. Interrupted atomic operations cannot complete. Exact-time completions before a breakdown remain valid. Truncated movement must end at actual breakdown position/time, and its partial metres use the contract's integer-floor convention.
- Enforce at most one recovery reload, following an actual disruption, and no work after the vehicle fails. Healthy vehicles must return; only failed vehicles receive the return waiver.
- Independently calculate delivered/on-time meals, all-demand coverage, priority-3 on-time coverage, priority-weighted on-time coverage, served destinations, late orders, unserved meals, actual distance, and per-vehicle rounded cost/emissions. Multiplication precedes kilometre division to retain exact half-unit rounding.
- Fail closed on malformed/non-JSON evidence; incomplete schema replay cannot display passed physical checks.

## Test evidence

Each new constraint was introduced with a failing real fixture assertion before implementation. Initial implementation had 14 failing assertions; subsequent RED/GREEN cycles added timed-load, one-way road, full-order atomic transfer, partial-road, breakdown-position, orphan-operation, ledger-tamper, integer-time, late-high-priority, rounding, and malformed-evidence regressions.

The hand-derived six-meal fixture has a 120-second load, 100-second outbound edge, 20-second service, and 100-second return: six meals, 2,000 metres, 100 cents and 400 grams. Claimed output metrics are deliberately false and final state is empty. Independent expectations are literals, not engine helper results.

Commands and final observed evidence:

- `.venv/bin/python -m pytest tests/test_verifier.py -q`: 37 referee tests.
- `.venv/bin/python -m pytest -q`: **81 passed, 4 third-party deprecation warnings**, 0.83 seconds. Warnings are Starlette's httpx TestClient path and ORTools SWIG metadata; no test failures.
- Independent full-world sweep: **6,780 worlds, zero physically invalid receipts, zero recomputed-metric differences**. The sweep uses seeds 1, 26 and 73; all three policies; all three failed vehicles; adaptation both enabled and disabled; times 0, 1, 60, 119, 120, 121, 500, 1500, 2200, 3500, 7000 and 13000; and each baseline load, arrival and delivery completion time minus one, exact, and plus one, deduplicated within the horizon.

An earlier sweep found twelve one-gram disagreements caused by the referee's floating arithmetic order (`4100 / 1000 * 95` is below 389.5 in binary). A hand-derived RED/GREEN regression corrected this to product-first rounding; the final sweep had zero disagreements. No engine residual-stock-grant or projected-healthy-commitment defect surfaced in the sampled worlds. Dedicated adversarial fixtures nevertheless reject double-spending depot stock and reload capacity that ignores old unused cargo.

## Scope and limits

Physical validity is separate from demand satisfaction or optimizer quality. An honestly replayed world can remain valid with unserved meals. Invalid-world metrics are diagnostic; eligibility must use the receipt's `valid` flag.

The independent referee trusts the supplied initial scenario as the authoritative synthetic input, comparing the world's initial hash to its declared scenario hash. It does not certify the authenticity of that scenario or prove planner optimality. The finite sweep exercises many boundaries but is not an exhaustive proof over every seed or disruption time. No external publication, deployment, or physical-world behavior was verified by this worker.

## Review fix R3 — distinguish recovery loads from lifetime loads

The independent review correctly identified a gap in the earlier recovery-load check: two lifetime loads could both begin after a disruption when a healthy vehicle had no initial load. The earlier generated-world sweep did not contain that nonconforming history, so its passing results did not establish this restriction exhaustively.

Added a separate per-vehicle count of completed loads whose `started_at` is at or after the first actual breakdown timestamp. More than one such load now produces `LOAD_LIMIT` on the extra completion event. The existing limit on extra pre-disruption loads remains enforced. An original load begun before the shock and completed afterward does not consume the recovery allowance.

The hand-derived reviewer reproduction is now a regression: idle B fails at 0; A loads 6 meals from 10 to 130, completes its delivery at 250, returns at 350, and loads the remaining 4 meals from 350 to 470. Stock, capacity and timing remain otherwise valid. The new test initially failed because the referee returned `valid=True`; after the fix it returns only `LOAD_LIMIT` on `recovery-end`. A second negative case places the shock exactly at 10 to cover inclusive start classification. A positive case places the shock at 60, while A's original load is underway, and preserves its one later recovery load.

Fresh executed checks after this targeted change:

- `.venv/bin/python -m pytest tests/test_verifier.py -q -k 'initially_unloaded or preserves_one_recovery'` before implementation: **2 failed, 1 passed**, with both negative cases failing for the expected erroneous `valid=True` result.
- `.venv/bin/python -m pytest tests/test_verifier.py -q`: **40 passed**, 0.02 seconds.
- `.venv/bin/python -m pytest -q`: **84 passed, 4 existing third-party deprecation warnings**, 0.92 seconds.
- Hand-derived boundary sweep across every shock from 0 through 470: **471 expected classifications passed**. Only shocks `10 < shock <=350` allow these two loads, distinguishing locked original loading from recovery loading and preserving the ban on a second pre-shock load.
- Affected engine load-boundary sweep: seeds 1/26/73, all three policies and failure vehicles, shocks 0/1/119/120/121, adaptation enabled and disabled: **270 valid worlds, zero recomputed-metric differences**.

Only the referee implementation, its tests, and this appended report were changed for R3. No engine helper imports, engine interface changes, commits, or publication actions were introduced.
