# FORK — rehearse a decision before its consequences become real

**Submission draft, not a submission receipt.** The original logistics source is public at [ahmedhxssam/fork-ai](https://github.com/ahmedhxssam/fork-ai). The Scenario Studio enhancement is locally implemented and must complete its current review before publication. Competition submission, final entry media and track selection are not claimed completed.

## Inspiration

A plan can look convincing while hiding assumptions about capacity, deadlines, stock and recovery. We wanted people to see those assumptions, rehearse disruptions and inspect the evidence before choosing a course of action. The first food-bank model made physical constraints concrete; the next step was to let different operations use a shared model instead of coding each domain from scratch.

## What it does

Scenario Studio starts with an ordinary problem description, including incomplete or conflicting details. A bounded deterministic interview asks one focused question at a time, quotes contradictions, and preserves source-backed answers. Users review the resulting plan and agreed assumptions in plain language; structured data remains an optional inspector. Different operations use the same resource/task scheduling engine.

FORK computes three scheduling choices from the same model. Users add resource outages, compare actual processing timelines and inspect the same shocked schedule with and without adaptation. Zero gains, losses and ties remain visible. A separate referee recomputes capacity, work, materials, dependencies, cost and completion metrics before a human can approve current evidence for export. Nothing is dispatched.

The retained logistics lab models roads, vehicles, cargo and one breakdown using its own validated physical semantics. Generic workflow jobs do not impersonate vehicle routes.

## How we built it

Python/FastAPI coordinates strict Pydantic model validation, bounded deterministic scheduling, independent standard-library replay and transactional SQLite snapshots. React, TypeScript and Vite provide editable briefs, traceable model review, synchronized processing timelines, disruption controls and human approval. The logistics lab additionally uses OR-Tools and NetworkX.

No runtime language-model calls, deepagents orchestration or model API key is present. A future OpenAI adapter can propose the same JSON schema from freer language, but must pass human model review, schema validation, simulation and independent verification. It will not author authoritative outcomes.

Development received substantial OpenAI Codex assistance across architecture, implementation, tests, debugging, review and documentation. No human-authorship percentage or independent organizer eligibility ruling is asserted.

## Challenges

A general-looking interface is easy; a model that actually changes behavior is harder. We separated domain data from executable primitives and made unsupported requests block compilation. Work checkpoints, resource commitments, stock consumption and overlapping outages have explicit semantics. The no-adaptation control preserves original resource assignments and unit-slot order so it cannot quietly choose easier replacement work.

We also separated physical validity from policy quality. The heuristics can lose or tie. In the retained logistics fixture, ordinary greedy routing delivers more initial meals than the named policies; that result remains visible. Independent verification establishes modeled consistency, not superiority or real-world truth.

## Evidence and boundaries

Compiler, scheduler, independent-referee and real API tests cover three distinct templates, unsupported requests, canonical hashes, capacity/dependency/stock/budget rules, outages, stale revisions, tampered evidence and current approval/export gates. The retained seeded workflow regression checks 600 nominal/control physical comparisons and 1,200 independently valid outage receipts. Current integrated commands and actual browser results are recorded in [TESTING.md](TESTING.md) and the studio reports.

All examples are synthetic. Workflow jobs are checkpointable, retain one resource pool, and spend only actual worked resource-unit minutes. The compiler accepts documented patterns, not arbitrary prose. It does not infer routing, physical dynamics, stochastic arrivals or human behavior. The app is a local single-backend-process planning tool, with no production dispatch, sponsor API integration, global optimality guarantee or field-validation claim.

## What we learned

The useful question is not only which plan looks best. It is which assumptions made that result possible, what changed after disruption, and whether a person can inspect enough evidence to own the decision.

## What's next

Connect a bounded OpenAI authoring adapter after explicit API setup, preserving the same typed proposal and verification gates. Validate model assumptions with actual operators before operational use. Add new semantics only when a real problem and independent checks justify them.

## Submission notes

Intended main-track fit: **Best Business and Enterprise**. Final category selection remains an entry action. Do not claim a live-model/deepagents/sponsor integration or guaranteed award outcome. The genuine [58.360-second conversational walkthrough](artifacts/FORK-conversation-demo-silent.webm) is recorded and verified; older clips document earlier interfaces. Use [the two-minute pitch](docs/PITCH.md) for live narration.
