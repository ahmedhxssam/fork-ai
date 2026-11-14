# Scenario Studio compiler and engine report

Task 1 implementation, 2026-11-14. Owned production files: `backend/studio/__init__.py`, `schema.py`, `compiler.py`, `engine.py`. Tests: `tests/test_studio_compiler.py`, `tests/test_studio_engine.py`. Existing logistics engine unchanged.

## Implemented behavior

The strict Pydantic schema rejects unknown fields, booleans/numeric coercion, unsafe/duplicate IDs, invalid bounds, dangling references, dependency cycles, incompatible skills/capacity, undefined materials and invalid resource outages. Insufficient stock and budget are valid modeled shortages. It exposes `Model`, `model_schema()`, `validate_model()` and canonical SHA256 `model_hash()`.

One deterministic minute-discrete list scheduler serves all three domain templates. Tasks use simultaneous units from one compatible resource pool. Once started, a task retains that pool. Each minute preserves healthy running work, attempts paused work in original start order, then considers new work by policy. Overlapping outage losses sum and cap at resource capacity. Materials are consumed once at first start; checkpointed work survives pauses. Actual resource-unit work alone spends budget. Horizon is hard, deadlines measure on-time completion rather than hard physical feasibility, and makespan includes the last partial work segment.

Policies are transparent heuristics, with no optimality claim:

- Throughput: shortest remaining work, earliest due time, highest value, task ID.
- Resilience: least remaining deadline slack, shortest remaining work, highest priority, task ID. This is a time-buffer heuristic, not a robustness guarantee or outage forecast.
- Priority: highest declared priority, earliest deadline, shortest remaining work, task ID.

Compatible available resources prefer lowest per-unit cost, then fewer skills, then resource ID. No policy inspects future outage timing. The nominal schedule is computed with no outages. Adapted execution responds to current available capacity while preserving healthy commitments and checkpointed work.

The paired no-adaptation control fixes nominal resource assignments, earliest starts, per-resource start order and unit-slot predecessor commitments. A delayed multi-unit job therefore cannot be bypassed by smaller later work assigned to its slots. Nominal scheduled work limits prevent a control from inventing work absent from its original plan. Only outage/dependency/budget delays alter replay. With no outages the control reproduces nominal segments, completions and metrics; narrative pause entries can differ for budget-truncated nominal work because the control explicitly stops at the original work limit.

## Supported brief grammar

One statement per line; blank lines and `#` comment lines are ignored. `Title:` and `Note:` explicitly mark narrative; other arbitrary prose is not silently accepted. Resource/task IDs are safe short slugs and references use those IDs. Briefs are bounded to 50,000 characters. Unknown lines, clauses, attributes and duplicate declarations/attributes block compilation. Every inferred optional field is reported in assumptions, alongside explicit checkpoint and actual-work cost assumptions. Accepted lines retain line-numbered facts-to-model targets.

Readable examples:

```text
Title: Repair clinic
Note: Synthetic inputs; work is checkpointable.
Horizon: 60 minutes
Budget: 1000 cents
Stock: parts=4 batteries=2
Resource bench: Repair bench has capacity 2, skills repair,test, and costs 3 cents per minute.
Task inspect: Inspect the radio takes 5 minutes using skill repair; needs 1 unit; available at 0; due by 10; priority 2; value 3; after none; consumes none.
Task fix: Fix the radio takes 10 minutes using skill repair; needs 1 unit; available at 0; due by 40; priority 3; value 10; after inspect; consumes 1 parts, 1 batteries.
Outage break resource=bench at=10 duration=5 lost=1 label="Bench outage"
```

Task semicolon clauses are optional, reorderable and unique. A resource/task sentence may omit its `: Readable label`. Natural task clauses are exactly `needs N unit(s)`, `available at N`, `due by N`, `priority N`, `value N`, `after ID,ID|none` and `consumes N MATERIAL, N MATERIAL|none`. Sentences end with a period. Labels, skills and dependencies are explicit, not inferred from task names.

An equivalent explicit syntax remains available:

```text
Resource bench label="Repair bench" capacity=2 skills=repair,test cost=3
Task fix label="Fix the radio" duration=10 skill=repair units=1 release=0 due=40 priority=3 value=10 after=inspect materials=parts:1,batteries:1
```

Defaults: title `Untitled workflow`, horizon 120, unlimited budget (`null`), no stock/outages; resource capacity 1/cost 0/label ID; task units 1/release 0/due horizon/priority 1/value 1/no dependencies/no material use/label ID. Resources still require skills; tasks still require skill and duration. Missing resources/tasks block compilation. Three prefilled readable templates model repair, event production and IT service response, each with contention and dependency/deadline structure. Templates start without outages.

## Executed checks and findings

1. Initial test-first run failed collection because the new compiler/engine modules did not exist. This was the expected missing-feature failure before implementation.
2. Initial implementation passed 32 tests; one test incorrectly compared the intentional `adapt` metadata difference and was corrected to compare the same metadata value.
3. Added richer natural-sentence test first; observed failure on unsupported labeled sentences, then implemented the bounded clause grammar and observed green.
4. Added a hand-derived fixed-control regression first; observed a later 1-unit job starting at minute 3 while the original 2-unit job remained paused until completion at minute 7. Added nominal unit-slot predecessor commitments; regression now passes.
5. Seeded physical sweep: 200 bounded random models with differing capacities, task units, dependencies, releases, priorities, materials, budgets and overlapping outages. Across three policies, **600 nominal/control physical-equality comparisons** and **1,200 independently valid outage receipts** passed. The sweep is retained as a regression test. Its first exploratory version compared narrative events too; it revealed the documented budget-stop narrative distinction, not a physical discrepancy.
6. `.venv/bin/python -m pytest tests/test_studio_compiler.py tests/test_studio_engine.py -q`: **36 passed**.
7. `.venv/bin/python -m pytest -q`: **175 passed, 4 existing dependency deprecation warnings** in 1.86 seconds at this integration snapshot. An earlier concurrent full run saw the referee worker's intentionally red noncanonical-evidence test; that worker fixed it and the later full run passed.

Hand-derived checks cover unit capacity, precedence, exact completion time/cost, one-time materials through interruptions, changing unstarted assignments under adaptation, pool retention, healthy commitments, partial/overlapping losses, hard horizon, scarce stock, partial budgets/free work, meaningful policy differences, determinism, unknown policies/events and unchanged inputs. Compiler checks cover three domains, defaults, traceability, unsupported prose/attributes and schema rejection cases.

## Scope and remaining limits

No API credentials, provider calls, generated code execution, autonomous LLM runtime or actual dispatch is implemented. Natural language support is intentionally the documented bounded grammar. This engine does not infer travel, stochastic arrivals, shifts, human behavior or physical repair details. Timing/capacity/stock/budget abstractions are synthetic modeling assumptions. Future typed proposals must pass the same schema and independent referee.

Decisions recorded: fixed control uses nominal unit-slot predecessor commitments to make “no alternate selection” concrete; makespan includes partial work; no-outage equality is physical evidence equality rather than narrative-event identity. These choices were communicated during integration. The independent referee verifies physical feasibility and metric integrity, not heuristic optimality.

No browser inspection, publication, competition eligibility determination or submission was performed by this worker. No git commit or unrelated source edit was made.
