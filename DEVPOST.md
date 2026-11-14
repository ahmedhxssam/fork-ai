# FORK — Devpost draft

Draft fields for owner review; this file is not a submission receipt. The source repository has a published earlier snapshot; the latest local polish must be checked separately before an entry is submitted.

## Copy-ready entry fields

**Project name:** FORK

**Tagline:** Rehearse food-bank delivery disruptions, compare recovery with a fixed plan, and choose using independently checked evidence.

**Main track:** Business & Enterprise

**Category / use case:** Operations planning → Food-bank delivery resilience

**Source:** https://github.com/ahmedhxssam/fork-ai

**Prepared video:** [92-second narrated MP4](artifacts/FORK-judge-demo.mp4) · [captions](artifacts/FORK-judge-demo.srt). Upload/link after review; no public video-host URL is claimed.

**Local demo:** http://127.0.0.1:8000/?view=logistics — startup instructions in README.md. This is a local application, not a hosted demo URL.

## Inspiration

A food-bank delivery plan can look good until a vehicle breaks down. The useful question is then concrete: which meals can still arrive, what can replanning recover, and what evidence should the coordinator trust?

We built FORK to rehearse that decision before its consequences become real. Food-bank delivery makes capacity, deadlines and stranded cargo visible. It is a synthetic planning example, not a claim of an operational deployment.

## What it does

An operations coordinator launches the same mission into three isolated worlds. Velocity, Resilience and Equity use different published priorities and reserve settings. Apply one vehicle breakdown at the same time in every world, then compare adaptation with each world's original plan executed under the same shock without replanning.

The comparison does not promise a preferred winner. In the seed-26 initial mission, ordinary greedy routing delivers **224 meals**, versus **216 / 192 / 216** for Velocity / Resilience / Equity. With **vehicle A failing at 1,500 seconds**, adaptive execution delivers **168 / 168 / 168**, while the paired fixed-plan controls deliver **144 / 120 / 144**: gains of **24 / 48 / 24**. The three adaptive outcomes tie on delivered meals; the larger recovery gain starts from a weaker control. Other shocks can produce different results or zero gains.

A separate referee reconstructs movement, cargo, timing and metrics from the evidence. The coordinator inspects that receipt, chooses preferences, approves the current revision and downloads a simulated-plan packet. Exports do not dispatch vehicles or contact volunteers.

Scenario Studio is a secondary authoring capability: a bounded interview asks for missing facts, exposes contradictions and compiles reviewed answers into a resource/task model. It shares the same decision-rehearsal approach, but generic workflow jobs do not impersonate vehicle routes.

## How we built it

Python and FastAPI coordinate strict Pydantic validation, transactional SQLite snapshots and idempotent commands. OR-Tools and NetworkX support logistics planning; a discrete-event simulator applies explicit physical rules. An independent standard-library referee replays the evidence without importing planner/simulator validation helpers. React, TypeScript and Vite provide synchronized maps, timelines, disruption controls, receipts and revision-bound approval/export.

Runtime is entirely deterministic. The strategy names are policy roles; no language-model calls, deepagents orchestration, model API key or sponsor integration is implemented.

**OpenAI Codex substantially assisted architecture, implementation, tests, debugging, review and documentation.** That assistance is distinct from runtime behavior. We do not claim a human-authorship percentage or an organizer eligibility ruling.

## Challenges

The hard part was preserving the comparison when plans diverge. Every world must start with the same resources and receive the same disruption. Recovery cannot rewrite completed deliveries, recover failed cargo or ignore existing commitments. The fixed-plan control must keep the original plan rather than quietly selecting easier replacement work.

We also separated physical validity from policy quality. A valid plan can lose, and a resilience policy can reserve too much. Greedy's initial win, unmet demand, ties and zero recovery gains remain visible. Independent verification establishes consistency inside the model; it does not establish optimality or real-world safety.

## Accomplishments

A complete local loop connects a scenario, three computed plans, a common shock, paired controls, independently checked evidence and explicit human approval. Stored experiments survive refresh, commands are idempotent, and changing evidence or preferences invalidates old approval.

Executed test and browser evidence is recorded with its release boundaries in TESTING.md. All roads, orders, identities, priorities, costs and emissions are synthetic. The logistics model deliberately limits depot trips, recovery reloads, breakdowns and cargo handling; there is no live dispatch or field-impact claim.

## What we learned

A persuasive plan needs a fair comparison and inspectable assumptions. A large recovery number is not automatically the best final outcome. Showing a baseline loss or a tie makes the human decision clearer.

## What's next

Validate the planning assumptions and workflow with actual operators. Add new semantics only when a real use case and independent checks justify them. A future bounded model adapter could clarify a brief and propose typed inputs; it would not author authoritative metrics, bypass verification or approve its own result.

## Built with

Python, FastAPI, Pydantic, Uvicorn, SQLite, OR-Tools, NetworkX, React, TypeScript, Vite, pytest, HTTPX, Playwright; OpenAI Codex for development assistance.

## Entry preparation notes — do not paste as product claims

- Select the exact main track **Business & Enterprise**. Operations planning and food-bank delivery resilience describe the use case; they are not additional official tracks.
- Use the primary logistics journey and the final inspected recording. Existing silent clips document earlier versions; do not describe them as a newly narrated release.
- Confirm the submitted source/video match the actual release. Publication, video upload, track selection and entry submission require their own evidence.
- No live-model, deepagents, CoStar or other sponsor integration is claimed. Keep synthetic inputs, greedy's initial win, ties and human approval explicit.
