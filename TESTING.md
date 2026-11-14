# Testing and evidence

The engine, referee and API are tested independently of the visual replay. Always separate a reported earlier run from a fresh verification of the current checkout.

## Run checks

```sh
make setup
make test
make demo
```

In a second terminal:

```sh
make test-browser
```

The browser journey uses the actual API and computed worlds. The browser target installs official Playwright Chromium if absent; that initial download needs network access. For an installed Chrome fallback, use `FORK_BROWSER_CHANNEL=chrome`. Set `FORK_URL` if the server is not at `http://127.0.0.1:8000`.

Individual checks:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest tests/test_engine.py -q
.venv/bin/python -m pytest tests/test_verifier.py -q
npm --prefix frontend run typecheck
npm --prefix frontend run build
npm --prefix frontend run test:e2e
```

## Recorded results

| Check | Recorded evidence | Boundary |
| --- | --- | --- |
| Full Python suite | 84 passed; four third-party deprecation warnings | Engine, independent referee, comparison, persistence and real API |
| Engine suite | 35 passed | Directed routes, shock boundaries, custody, locking, recovery and baselines |
| Independent referee suite | 40 passed | Hand-derived fixtures, malformed evidence, deliberate tampering and recovery-load limit |
| Full-world sweep | 6,780 worlds; zero invalid receipts, zero recomputed-metric differences | Finite synthetic audit, not exhaustive proof |
| Frontend model tests | 4 passed | Baseline wins, ties, zero weights and grounded shock evidence |
| Frontend typecheck / build | Passed | Checked with the final source and documented Make target |
| Browser acceptance | 14 passed | Real API, all vehicles, artifacts, preference faults/order, resume, stale approval and layout |
| External network blocked | Passed | Fresh experiment and shock against localhost, then refresh/resume; initial install remains online |
| Public source | Published and anonymous access verified | [ahmedhxssam/fork-ai](https://github.com/ahmedhxssam/fork-ai), created November 13 at 11:13 PM Eastern |
| Competition entry / hosting | Not submitted / not hosted | Local application and submission draft are delivered; no submission receipt claimed |

Detailed source evidence: [engine report](docs/ENGINE_REPORT.md), [referee report](docs/VERIFIER_REPORT.md), [frontend handoff](frontend/IMPLEMENTATION_REPORT.md). Counts describe those reports' snapshot, not a promise that unexecuted checks passed.

Final integration evidence and genuine output paths are in [RELEASE_VERIFICATION.md](docs/RELEASE_VERIFICATION.md). The three independent review findings were fixed with observed failing regressions before implementation: preference save/approval consistency, transient resume recovery, and separate recovery-load counting. A subsequent delayed-approval regression prevents an old response overwriting a newer acknowledged revision.

The 6,780-world sweep covers seeds 1, 26 and 73; all three policies; each failed vehicle; adaptation enabled and disabled; representative times plus load, arrival and delivery completion boundaries at minus one second, exactly, and plus one. The earlier 1,080-world engine boundary audit overlaps this broader evidence and should not be added as an independent sample count. Seeds and timing combinations are generated synthetic cases, not field trials.

## What the tests target

- Inventory conservation, integer custody, capacity including unused cargo, commodity compatibility and unique whole-order completion.
- Directed movement, continuous positions, partial failed legs, operation duration, hard windows, volunteer/vehicle shifts and required returns.
- Atomic interrupted loads/services, completion-before-shock precedence, locked healthy commitments, single reload and shared depot grants.
- Referee rejection of fabricated deliveries, malformed evidence, double-spent stock, wrong geometry/timing and tampered claimed metrics.
- API validation, missing resources, persistence, command idempotency, comparison weights/ties, stale approvals and export gates.

The referee independently computes expected metrics; it does not trust `result.metrics` or `result.final_state`. A six-meal literal fixture establishes a 120-second load, 100-second outbound edge, 20-second service and 100-second return: 2,000 metres, 100 cents, 400 grams. Rounding regression coverage addresses an observed one-gram discrepancy; the final sweep reports no remaining metric discrepancies.

## Benchmark interpretation

| Initial seed-26 method | Meals delivered | On-time meals | Distance |
| --- | ---: | ---: | ---: |
| Nearest-feasible greedy | 224 | 200 | 48,047 m |
| Neutral solver | 216 | 192 | 51,281 m |
| Velocity | 216 | Inspect current receipt | Inspect current receipt |
| Resilience | 192 | Inspect current receipt | Inspect current receipt |
| Equity | 216 | Inspect current receipt | Inspect current receipt |

All comparators use the same simulator and independent verifier. Greedy's higher aggregate initial delivery count must remain visible. No claim is made that named policies outperform it, that a reserve guarantees recovery, or that any policy is optimal. Only use a recovery number obtained from the actual selected shock.

## Manual release checks

Before recording or publishing, exercise launch, common shock, both baseline comparisons, preference changes, inspector checks/hashes, approval, JSON/CSV parsing, refresh/resume and reset in a real browser. Inspect laptop and narrow layouts, native dialogs, keyboard focus, reduced motion and visible errors. Disconnect external network access after installation and repeat a fresh experiment and shock against localhost; cached replay alone is insufficient evidence of offline replanning.

Record commands, actual outcomes, environment and remaining failures in the integration ledger. A prepared test, an unavailable browser, or a sandbox launch failure is not a passing browser result. No latency or accessibility-conformance benchmark is asserted here.
