# Simulation and methods

FORK models one fictional four-hour food-bank mission. Its outputs describe this synthetic model and its declared assumptions.

## Scenario and units

| Quantity | Convention |
| --- | --- |
| Time | Integer elapsed seconds after 09:00; horizon 14,400 (13:00) |
| Inventory / orders | Integer meals; atomic whole orders |
| Roads | Directed edges; distance in metres, duration in seconds |
| Cost / emissions | Integer cents / grams CO2e, rounded once per vehicle |
| Stock | 192 ambient + 48 chilled = 240 meals |
| Demand | 216 ambient + 48 chilled = 264 meals, 12 destinations |
| Vehicle A | 100 capacity, ambient only; shift ends 12:00 |
| Vehicle B | 60 capacity, ambient only; shift ends 11:30 |
| Vehicle C | 80 capacity, chilled compatible; shift ends 12:20 |

Volunteers have fixed vehicle assignments and corresponding shifts. Service must complete within hard receiving windows. The preferred due time is a separate on-time objective; a late delivery can remain physically valid if it still satisfies its hard window. Healthy vehicles must return to the depot within their shifts.

Seed 26 is the default illustrative fixture. It is not a sample of real food-bank operations. Other seeds vary generated service durations on the same road geometry; they do not constitute independently collected scenarios.

## Policies and baselines

All named policies use the same routing algorithm and bounded budget. Current defaults:

| Policy | Priority exponent | Tardiness coefficient | Minimum ambient reserve |
| --- | ---: | ---: | ---: |
| Velocity | 0 | 12 | 0 |
| Resilience | 1 | 4 | 32 |
| Equity | 3 | 16 | 0 |

Omission penalty is `meals × 1800 × priority^exponent`; travel distance contributes metres × 1. Tardiness is seconds after preferred service-start deadline × coefficient × priority^exponent. The deadline accounts for service duration. Resilience's reserve may exceed 32 because orders are indivisible. These are transparent policy settings, not learned policies or a calibrated robustness model.

OR-Tools uses parallel cheapest insertion with one constructive solution per candidate and a three-second watchdog. NetworkX supplies directed shortest travel-time paths. Recovery evaluates at most four reload/no-reload patterns for healthy vehicles. Feasible incumbents are not certified globally optimal; machine-load-dependent watchdog behavior can affect a fresh solve. Saved plans and event replay preserve exactly what was computed.

Diagnostic comparators use the same simulator and referee: fixed vehicle-order nearest-feasible greedy, and a neutral solver objective without priority, lateness or reserve preference. Initial reported meal totals are greedy **224**, neutral solver **216**, Velocity **216**, Resilience **192**, Equity **216**. The named policies do not beat greedy on aggregate initial meals. A good physical receipt does not establish a good optimizer.

## Custody and events

For each commodity at every physical event boundary:

`initial stock = depot + usable onboard + stranded + delivered`

Loading takes 120 seconds and transfers stock atomically at completion. Service transfers an indivisible order at completion. A vehicle in motion follows actual directed road edges and consumes their time. The event ledger records physical operation starts/completions, movements, breakdown, plan acceptance and horizon. Reservations do not create another copy of stock.

At a breakdown timestamp, already scheduled completion events execute first. The failed vehicle then becomes unavailable; a new departure cannot evade that failure. An interrupted load leaves untransferred stock at the depot. Interrupted service completes no delivery. Actual onboard cargo becomes stranded. A partial road leg ends at its actual failure position and elapsed time; travelled integer metres are floored once. No vehicle or cargo teleports.

Healthy ongoing roads, services and loads remain locked until their real ready time. Recovery distinguishes actual custody at the shock from projected ready-state custody. It excludes committed services from remaining orders and jointly constrains future depot grants so multiple vehicles cannot spend the same stock. Old unused cargo still consumes capacity.

Initial routes make one trip. Each healthy vehicle may perform at most one explicitly timed recovery depot reload, requiring real return travel and a 120-second load. There is no failed-cargo rescue, vehicle-to-vehicle transfer, driver reassignment, towing or spoilage model.

## Comparison definitions

- **Coverage:** all delivered meals / all requested meals.
- **On-time coverage:** meals completed by preferred due time / all requested meals.
- **Priority coverage:** on-time priority-3 meals / all priority-3 demand.
- **Priority-weighted coverage:** on-time meals × literal priority / all demanded meals × literal priority.
- **Distance:** all actual travel, including healthy returns and partial failed travel.
- **Cost / emissions:** per-vehicle distance × declared synthetic cents/km or grams/km; no fixed, service or externality costs.

Only referee-valid worlds are eligible for recommendation. Preferences normalize to sum 1. The score is weighted on-time coverage + weighted priority coverage + weighted `(1 − min(1, cost_cents / 20000))`. A tie produces no unique recommendation. Pareto membership uses the same three axes: maximize on-time coverage and priority coverage, minimize cost. Emissions are displayed but not a recommendation axis.

**Recovery gain** is adapted meals minus unadapted meals under the same initial plan and exact same shock. The unshocked baseline delta measures overall damage/recovery relative to a different, undisturbed run. These comparisons must not be conflated. Gains may be zero or unfavorable; no policy is required to win.

## What verification establishes

The independent referee reconstructs custody, capacity, cold compatibility, directed movement, timing, shifts, returns, atomic orders and metrics from evidence. Invalid results are ineligible even if their claimed totals look attractive. It does not certify real inputs, optimality, real-world safety or generalization. Its finite regression sweep exercises many boundaries; it is not an exhaustive proof. See [TESTING.md](TESTING.md) and [the referee report](docs/VERIFIER_REPORT.md).
