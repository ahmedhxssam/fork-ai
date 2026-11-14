# Deterministic roles and contributor guidance

FORK currently runs only in **Deterministic Planner Mode**. Strategy names and activity labels are roles in a deterministic workflow. They are not evidence of autonomous LLM reasoning.

## Runtime roles

Scenario Studio additionally uses a deterministic bounded brief compiler, a shared resource/task scheduling engine, and a separate standard-library workflow referee. It accepts typed model inputs; it never executes generated code. Source facts, defaults and unsupported statements remain inspectable. Its schema is a future AI authoring boundary; no model provider is currently connected. See [Scenario Studio](docs/SCENARIO_STUDIO.md). The roles below describe the retained logistics lab.

| Role | Implemented mechanism | Authority |
| --- | --- | --- |
| Velocity strategist | Published OR-Tools objective configuration | Propose routes and manifests for its own copied world |
| Resilience strategist | Same algorithm, reserve and objective settings | Same world-local proposal authority |
| Equity strategist | Same algorithm, stronger synthetic priority weighting | Same world-local proposal authority |
| Recovery planner | Residual routing with locked physical commitments | Propose bounded recovery, never rewrite completed history |
| Simulator | Discrete-event physical execution | Produce modeled events and custody |
| Independent referee | Separate standard-library replay and checks | Decide evidence validity and recompute metrics |
| Preference comparison | Fixed normalized scoring over valid receipts | Recommend or report ties, never approve |
| Human reviewer | Explicit current-revision approval | Select a simulated plan for export |

The API's activity records expose actual deterministic operations such as `optimize_routes` and `replan_remaining_routes`, with measured wall-clock durations. No model prompts, token streams, agent debate, provider calls, deepagents orchestration or LLM tool execution are implemented. No API credential is needed.

## Development assistance and credits

OpenAI Codex substantially assisted architecture, code, tests, debugging, review and documentation. Runtime determinism does not erase that development assistance. Disclose it in public descriptions; do not invent human contribution percentages or claim that disclosure itself proves event eligibility. The user reported having checked AI-assistance guidance; the repository does not independently establish an organizer ruling.

Frameworks and libraries are credited in [README.md](README.md). Proposed sponsor integrations are conditional future work until the actual brief is read and a genuine integration is implemented and tested.

## Rules for future changes

- Preserve synthetic-data and planning-mode labels. Do not narrate computed playback as live telemetry or label deterministic activity as LLM output.
- Preserve scenario parity, isolated worlds, integer units, fixed physical semantics and independently verified metrics. Read [SIMULATION.md](SIMULATION.md) and [docs/CONTRACT.md](docs/CONTRACT.md) before changing engine interfaces.
- Keep the referee independent from planner/simulation validation helpers. Add meaningful adversarial or hand-derived checks for consequential physical changes.
- Preserve honest baselines, ties, zero recovery gains and unmet demand. Do not tune a fixture to conceal a preferred policy's loss.
- Bind approvals and exports to current evidence and preferences. Never turn approval/export into real dispatch or outbound messaging implicitly.
- Keep credentials out of source, browser bundles, event logs and exports. Any future model integration needs explicit provider/budget configuration, bounded typed proposals, visible provenance, and a tested deterministic fallback.
- Report only checks actually executed. Publication, browser QA, offline use, eligibility and submission require their own evidence; local unit tests do not establish them.
- Preserve unrelated edits and stored experiments. Reset means create a new experiment, not erase history.

Any future live strategist may choose bounded policy parameters or propose candidate routes; it must never author authoritative metrics, bypass the referee, mutate another world, fabricate physical events or approve its own result.
