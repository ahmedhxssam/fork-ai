# FORK truth engine implementation

The engine generates the declared synthetic Riverton fixture, plans actual directed-road routes with OR-Tools Routing and NetworkX, and executes explicit physical operations. Each world is independently copied. No policy inspects a future shock or has a predetermined outcome.

## Model and policies

There are 12 indivisible orders requesting 216 ambient plus 48 chilled meals; inventory is 192 ambient plus 48 chilled. Vehicle capacities are 100, 60 and 80; only C carries chilled stock. Initial plans permit one load/trip. All service completions and required returns honor hard windows and vehicle/volunteer shifts.

The solver uses deterministic input ordering and parallel cheapest insertion with one constructive solution per candidate; a three-second watchdog prevents an unbounded solve. The incumbent is feasible, not certified optimal. Policies share the same algorithm and budget. Default integer objective coefficients are published in `planner.POLICIES`: omission cost is meals × 1800 × priority^power; distance is metres × 1; tardiness is seconds after preferred service-start deadline × lateness coefficient × priority^power. Velocity uses priority power 0 and lateness 12, Equity power 3 and lateness 16, Resilience power 1 and lateness 4 with a 32-unit minimum ambient depot reserve. Atomic order sizes can make actual reserves larger. One declared setting is used per policy; this is a bounded policy comparison, not exhaustive policy optimization or a calibrated robustness study.

Per-vehicle nonnegative commodity grant variables are coupled to routing assignment variables. Their sums cannot exceed shared depot stock; onboard inventory plus all grants cannot exceed capacity; delivery assignments cannot exceed onboard plus grants. This enforces compatibility, supply and unused-cargo occupancy without independently promising the same stock to multiple vehicles. Selected manifests are the minimum grants necessary for the actual assignment.

## Physical recovery

Loads take 120 seconds and transfer inventory atomically on completion. Service is also atomic. Completion events at the shock time execute first; the breakdown then prevents new failed-vehicle actions. Failure moves actual onboard cargo to stranded custody. A failed partial road edge ends at its actual time and geometric position; integer travelled metres are rounded downward once. No rescue or cross-vehicle transfer is modeled.

Healthy current edges, loads and services finish at their real future time. Actual custody at the shock is retained separately from projected readiness. A locked service is removed from residual orders and subtracted only from projected cargo. A locked load reserves future stock without advancing the actual ledger. The recovery plan stores the actual input snapshot, explicit locked commitments and their joint SHA-256 hash.

Recovery enumerates the at-most-four reload/no-reload patterns for the healthy vehicles. A reload requires real return travel plus 120 seconds; existing cargo remains onboard. All assignments and shared grants are solved jointly. The candidate proxy includes depot detour distance. Empty solver outcomes remain empty/return-only, visibly labeled. Planning wall time does not advance the fictional mission clock.

The event log contains physical load-start/load, per-edge departure/arrival, service-start/delivery, return markers, breakdown, replanning, accepted plan and horizon events. Trajectories follow actual directed edges. Final custody and metrics derive from the emitted ledger. Independent validity remains the referee's responsibility; `metrics.violations=0` is not an independent certificate.

## Metric definitions

Coverage and on-time coverage divide by all requested meals. On-time means service completion no later than the preferred due time. Priority coverage is on-time delivered priority-3 demand divided by all priority-3 demand (clarified by the integration lead to match the product comparison). Priority-weighted coverage uses **on-time** delivered meals × literal priority divided by all requested meals × literal priority. Hard windows concern completion. Distance includes returns and partial failure travel. Cost and emissions use the published synthetic per-km coefficients, rounded once per vehicle; fixed/service costs are not modeled.

## Verification evidence

Initial TDD run: all 28 original behavior tests failed on missing scenario implementation. After implementation they passed. The snapshot-binding test was separately observed failing before its implementation. The current engine suite adds healthy service locking, joint reload/capacity custody replay and exact-time completion-prefix checks.

Fresh test and integration counts are reported by the implementation agent after the final run. Earlier integration exposed the referee counting both arrival and informational return as duplicate completion evidence, and requiring fractional rather than integer partial metres. Those were coordinated and corrected in the separate referee module. OR-Tools 9.15's Python `SetAllowedVehiclesForIndex` rejected a normal list through its SWIG binding; restricting `VehicleVar` to `[-1] + eligible vehicles` enforces the same allowed-vehicle rule successfully. Upstream SWIG deprecation warnings remain.

## Material boundaries

- No global optimality certificate and no measured real-world performance claim.
- No general multi-trip routing, towing, driver rescue, transfer, spoilage model or live dispatch.
- Fresh plans repeat on the tested fixture and fixed budget; persisted event replay is exact. A watchdog hit can change which fallback is returned under different machine load, and its fallback status is explicit.
- Diagnostic comparators are available through `plan_baseline`: fixed vehicle-order nearest-feasible greedy and neutral OR-Tools meal/distance objective. Both run through the identical simulator and independent referee; the default three panels remain named policies.
- Policy configuration overrides are bounded integer coefficients, not arbitrary code or external agent execution.

## Completed engine validation

- Engine suite: **35 passed**, including actual routing, mutation isolation, all three vehicle shocks at seven representative times, hand-calculated 1 km travel and partial failure, interrupted loading/service, exact completion precedence, hard-window and cold-compatibility omission, snapshot hashes, healthy service locking, joint stock/capacity replay, on-time priority metrics, and both genuine diagnostic comparators.
- Independent event-boundary sweep: **1,080 adapted worlds, zero invalid receipts**, covering every baseline event timestamp minus one second, exactly at the event, and plus one second, for each policy and every failed vehicle. This is a synthetic fixture boundary audit, not a calibrated operational failure-rate estimate.
- Greedy baseline independently verified: **224 delivered, 200 on-time, 48,047 m**. Neutral solver baseline independently verified: **216 delivered, 192 on-time, 51,281 m**. The conventional greedy baseline exceeds the named-policy baselines on aggregate meals; diagnostics must retain that outcome.
- The complete Python suite was also run during parallel integration. The latest observed unrelated transient failure was `test_unknown_experiment_and_invalid_shock_return_useful_errors` (missing-experiment approval returned 404 while its actively edited test expected 422); 76 tests passed. The root worker was notified and owns final integrated rerun.
