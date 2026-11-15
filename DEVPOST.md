# FORK — Devpost draft

Draft fields for owner review; this file is not a submission receipt. The earlier judge-readiness release is documented in [publication evidence](docs/PUBLICATION.md). The newer guided tour and submission media require their own release/publication evidence.

## Copy-ready entry fields

**Project name:** FORK

**Tagline:** Rehearse food-bank delivery disruptions, compare recovery with a fixed plan, and choose using independently checked evidence.

**Main track:** Business and Enterprise (select only this main track)

**Best Overall Hack:** automatic consideration upon submission, not another main-track selection.

**Category / use case:** Operations planning → Food-bank delivery resilience

**Source:** https://github.com/ahmedhxssam/fork-ai

**Prepared video:** [submission MP4](artifacts/FORK-submission-demo.mp4) · [captions](artifacts/FORK-submission-demo.srt) · [transcript](artifacts/FORK-submission-demo-transcript.txt). Check the [presentation release report](docs/PRESENTATION_RELEASE.md) for measured duration and inspection. The supplied packet caps the optional video at two minutes. A Devpost-compatible video-host upload/link remains a separate action.

**Local demo:** http://127.0.0.1:8000/?view=logistics&tour=1&pace=120 — two-minute guided judging cut; startup instructions in README.md. The [three-minute guide](http://127.0.0.1:8000/?view=logistics&tour=1) is for rehearsal. This is a local application, not a hosted demo URL.

## Inspiration

A food-bank delivery plan can look good until a vehicle breaks down. The useful question is then concrete: which meals can still arrive, what can replanning recover, and what evidence should the coordinator trust?

We built FORK to rehearse that decision before its consequences become real. Food-bank delivery makes capacity, deadlines and stranded cargo visible. It is a synthetic planning example, not a claim of an operational deployment.

## What it does

An operations coordinator launches the same mission into three isolated worlds. Velocity, Resilience and Equity use different published priorities and reserve settings. Apply one vehicle breakdown at the same time in every world, then compare adaptation with each world's original plan executed under the same shock without replanning.

The comparison does not promise a preferred winner. In the seed-26 initial mission, ordinary greedy routing delivers **224 meals**, versus **216 / 192 / 216** for Velocity / Resilience / Equity. With **vehicle A failing at 1,500 seconds**, adaptive execution delivers **168 / 168 / 168**, while the paired fixed-plan controls deliver **144 / 120 / 144**: gains of **24 / 48 / 24**. The three adaptive outcomes tie on delivered meals; the larger recovery gain starts from a weaker control. Other shocks can produce different results or zero gains.

An eight-chapter guide makes the story easy to follow, with Back, Next and Restart controls. A separate referee reconstructs movement, cargo, timing and metrics from the evidence. The coordinator inspects that receipt, chooses preferences, approves the current revision and downloads a simulated-plan packet. Exports do not dispatch vehicles or contact volunteers.

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

- Select **Business and Enterprise** as the single main track. Operations planning and food-bank delivery resilience describe the use case. Best Overall consideration is automatic upon submission; the packet lists a PS5 Disc Edition per winning member and says main-track winners cannot also win Best Overall. No award outcome is promised.
- Use the two-minute logistics journey and final inspected recording. The three-minute guide is rehearsal only: both video and required in-person demo have a two-minute cap. Older 92-second/silent clips document earlier versions.
- Confirm the submitted source/video match the actual release. Publication, video upload, track selection and entry submission require their own evidence.
- No live-model, deepagents, CoStar or other sponsor integration is claimed. Keep synthetic inputs, greedy's initial win, ties and human approval explicit.

- Supplied source checks: *F26 Onsite Hacker Packet*, pp. 4–5 (deliverables, duration limits, judging rubric), pp. 10–12 (main tracks, prizes, automatic Overall); *F26 Main Track.docx* agrees. The deadline is November 15, 2026 at 8:00 AM event-local time (Princeton/Eastern); the packet itself prints “8 am.” Add the required Discord usernames and verify the entry confirmation.
- Do not claim sponsor-track eligibility from the food-bank theme alone. CoStar requires combined sponsor-data layers and agentic behavior; LangChain requires deepagents; Peri requires an evidenced consultation with a real business. Current FORK establishes none of those. [Track guidance](SUBMISSION_READY.md) covers the remaining special tracks.
