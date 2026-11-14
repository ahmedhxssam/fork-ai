# Scenario Studio

FORK now has two executable model families. The default **Scenario Studio** turns a bounded, editable brief into a generic resource-and-task workflow. The **logistics lab** at `/?view=logistics` retains the food-bank road, vehicle and cargo simulation. Workflow time is in minutes; logistics time remains seconds. Neither model silently substitutes for the other.

## Brief → model → evidence → human choice

The studio starts with an editable repair-clinic scenario. Switch to event production or IT response to see different jobs, skills, dependencies, materials and deadlines, using the same engine. Compile the brief, review the model and its assumptions, then run three futures. Unsupported statements block compilation and identify the line that needs revision.

The compiler is deterministic, not a language model. It accepts a documented line grammar and bounded natural-style resource/task sentences. This deliberately exposes what it understood. It cannot infer a trustworthy model from arbitrary prose, invent missing domain physics, or validate the real-world truth of a user's assumptions.

Each compilation returns:

- A typed `fork-workflow/1` model and canonical SHA256 fingerprint.
- Source lines linked to model fields.
- Explicit deterministic defaults and engine assumptions.
- Blocking errors for unknown statements, attributes, missing required facts, incompatible skills, impossible unit capacities, unknown references or cyclic dependencies.

The editable examples demonstrate the complete grammar. `GET /api/studio/templates` returns the current examples and capabilities. `GET /api/studio/schema` returns the exact machine-readable model schema; `/docs` exposes the local API.

## Shared model primitives

| Primitive | Meaning |
| --- | --- |
| Resource pool | Capacity units, one or more skills, cost per worked resource-unit minute |
| Job | Processing duration, one skill, simultaneous units, release/deadline, declared priority and value |
| Dependency | All predecessor jobs must complete before work starts |
| Material | Stock consumed once when a job first starts; interruption does not consume it again |
| Work budget | Maximum integer cents spent on actual processing |
| Outage | Resource capacity lost over a half-open minute interval |

A job uses one compatible pool, retains it after first start, and checkpoints completed processing during interruption. This is a declared abstraction. A repair that must restart from scratch, a clinical intervention, a chemical reaction, or a vehicle journey needs different validated semantics. The studio does not infer those semantics from a name.

Limits: 12 resource pools, 80 jobs, 12 stock types, 12 outages, a horizon of 1–720 integer minutes, and capacity of 1–12 units per pool. Inputs are typed data. No generated Python, JavaScript, `eval`, or `exec` runs.

## Three scheduling choices

All policies use bounded, deterministic list scheduling, not a global optimizer. No policy reads future outages. Resource selection prefers lower work cost, then fewer skills, then ID. Healthy running commitments precede paused jobs, which precede unstarted jobs.

- **Throughput:** shortest remaining work, then earlier due time and higher declared value.
- **Resilience:** least remaining deadline slack, then shorter work and higher priority. This seeks time buffer; it is not a guarantee of robustness.
- **Priority:** highest declared priority, then earlier deadline and shorter work.

All remaining ties resolve by task ID. Policy names describe choices; any policy may lose or tie. Priorities are user-supplied values, not a judgment that FORK makes about people.

## Outages and counterfactuals

Add, edit or remove multiple capacity outages and apply them to rerun the experiment. Every policy receives the same model and outage schedule. Changing outages is a new counterfactual run from minute zero, not a retroactive alteration of a real operation.

The comparison includes an unshocked run and a paired **no-adaptation** control. The control freezes the nominal pool assignments, start lower bounds and per-pool job order; outages may pause work and delay successors. Adaptive runs can reconsider unstarted jobs using currently available capacity. Checkpointed work, material use, existing pool assignments and healthy running commitments remain fixed. Overlapping losses add and are capped at the pool's capacity.

The paired difference measures the effect of this scheduling freedom within the declared model. Zero or negative gain is a valid result. An outage after all relevant work completes can have no effect.

## Independent evidence

The workflow referee uses only Python's standard library and does not import compiler, scheduler or schema-validation helpers. It reconstructs per-minute work and checks identities, canonical model hash, pool capacity under outages, skills, units, release times, dependencies, exact processing, completions, materials, budget and metrics.

The API displays referee-computed metrics. Invalid outcomes are excluded from recommendations. A feasibility receipt does not prove heuristic optimality, real-world safety, or faithful domain modeling. Evidence hashes detect internal changes; they are not signed external attestations.

Preference scoring uses on-time jobs / all jobs, on-time priority-3 jobs / all priority-3 jobs (zero when none exist), and actual work cost divided by a model-derived fixed cost bound. Weights normalize to one. Equal top scores remain ties. Preferences rescore existing outcomes; they do not change scheduler behavior.

## Edits, saving and approval

Editing the brief makes the previous compilation and results stale. Event and preference drafts disable approval/export until applied or reverted. Successful model/event/preference changes clear approval. Mutations use the current experiment revision; stale writes return 409. Commands accept idempotency keys so a retry can recover a successful response without applying it twice.

The browser preserves the draft and a saved experiment pointer. A transient resume error preserves the pointer. New scenario creates an empty draft without deleting stored history. The local database is the same transactional SQLite store used by the logistics lab; run one backend process.

Approval records the exact model, evidence, preferences and revision. Export independently rechecks the selected evidence before returning JSON or the actual worked-segment CSV. Nothing is dispatched and no external system is changed.

## AI adapter boundary

There is no runtime AI provider connection in this release. The user explicitly deferred API-key setup. A later OpenAI adapter can propose the same typed model from a freer brief, including source provenance, questions and assumptions. It must pass schema validation, human model review, simulation and the independent referee. The model may propose inputs; it may not author authoritative outcomes, approve itself or bypass validation.

Before enabling that adapter, add explicit provider/budget configuration, bounded structured output, timeouts, cancellation, missing-fact handling, adversarial prompt tests and a tested deterministic fallback. Keep credentials on the backend and out of models, browser bundles, logs and exports. The existing schema endpoint is the integration seam; no API calls or hidden key requirement are present now.

## Suggested two-minute demonstration

1. Show the prefilled repair-clinic brief and deterministic label. Compile and point to a source fact, an explicit assumption and a dependency.
2. Run three futures. Inspect actual processing bars and independently checked results; show a tie if one occurs.
3. Add a judge-selected resource outage. Rerun and compare the same shock with and without adaptation.
4. Switch to IT response or event production, compile and run. Point out that the resources and dependencies changed while the engine did not.
5. Approve the current evidence and download JSON. Say plainly that future AI can author this typed model, while evidence remains independently computed.

This demonstrates creativity through inspectable model authoring, utility through resource tradeoffs, charity through transparent priorities and constraints, and technical execution through real counterfactuals and independent checks. No award outcome is promised.

## Current default: conversational authoring

The original bounded line-grammar authoring described above is retained as an advanced API. The default UI now accepts ordinary prose, asks targeted follow-ups for missing or conflicting facts, and reviews a simplified model in plain language. Structured JSON stays optional. See [conversational intake](CONVERSATIONAL_INTAKE.md) for current user behavior, simplified-scope limits, replay-bound launch and saved-source handling. The original model/engine/referee semantics in this document still apply; natural-language support does not imply that every richer model field can be inferred automatically.
