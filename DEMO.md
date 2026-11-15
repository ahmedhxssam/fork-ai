# FORK: guided food-bank demo

**Business and Enterprise → Operations planning → Food-bank delivery resilience**

Tell one story: a food-bank delivery vehicle breaks down; the coordinator compares recovery with a fixed plan under the same shock, checks the evidence, and approves a simulated result.

Start the server, then use the [three-minute guided rehearsal](http://127.0.0.1:8000/?view=logistics&tour=1) to learn the flow. Use the [two-minute judging cut](http://127.0.0.1:8000/?view=logistics&tour=1&pace=120) with judges. The ordinary workspace is [the logistics view](http://127.0.0.1:8000/?view=logistics). Scenario Studio remains the root page and links to the food-bank demo.

**Both the optional submitted video and required in-person presentation are capped at two minutes** in the supplied onsite packet, p. 4. The three-minute mode is for rehearsal. [Guided mode instructions](docs/JUDGING_MODE.md) · [spoken scripts and FAQ](docs/PITCH.md) · [submission video](artifacts/FORK-submission-demo.mp4) · [captions](artifacts/FORK-submission-demo.srt).

## Before presenting

```sh
make setup
make test
make demo
```

In another terminal, run `make test-browser` against the running server. Record actual results in release evidence; an unavailable browser is not a pass. Install dependencies and browser binaries before relying on an offline demonstration. Keep the server terminal running and use one backend worker.

Start from the guided briefing. Use **Next** and **Back** for chapters; the explicit **Apply shared breakdown** action runs A at elapsed 1,500 seconds. **Restart tour** returns to the briefing and creates a new experiment when you continue into the comparison; it preserves saved history. **Exit** leaves the guide. A persisted experiment is a saved replay, not fresh computation. Close unrelated tabs/notifications and confirm synthetic-data and deterministic-mode labels.

## Rehearse in three minutes; present in two

| Chapter / action | Rehearsal | Contest cut |
|---|---|---|
| Mission: 240 meals available, 264 requested, three vehicles | 0:00–0:25 | 0:00–0:15 |
| Compute three plans with equal starting resources | 0:25–0:50 | 0:15–0:30 |
| Read the honest greedy benchmark and explain the control | 0:50–1:15 | 0:30–0:45 |
| Apply the shared A-at-1,500 breakdown | 1:15–1:40 | 0:45–1:00 |
| Compare adaptive outcomes, fixed plans and recovery gains | 1:40–2:10 | 1:00–1:20 |
| Review preferences; a large gain is not automatically best | 2:10–2:25 | 1:20–1:30 |
| Inspect a referee receipt and one physical detail | 2:25–2:45 | 1:30–1:45 |
| Human approval and simulated JSON/CSV export | 2:45–3:00 | 1:45–2:00 |

Allow computation to finish. If it takes longer, shorten narration and keep the contest cutoff. The guide's time budget is a rehearsal aid, not a promise that every computer will complete the flow in that time.

## Reference results, never a promised winner

| Strategy | Initial meals | A-at-1,500 adaptive | Same-shock fixed plan | Recovery gain |
|---|---:|---:|---:|---:|
| Velocity | 216 | 168 | 144 | +24 |
| Resilience | 192 | 168 | 120 | +48 |
| Equity | 216 | 168 | 144 | +24 |

Initial greedy delivers **224** and the neutral solver **216**. The named policies all lose to greedy initially and tie on adaptive meals here. Resilience's larger gain starts from its weaker fixed-plan control. The unshocked reference answers a different question.

A judge may choose another supported vehicle/time in the workspace. Read those computed results and abandon the reference-number narration. A late shock can have no effect; chilled demand can remain unrecoverable. Say zero when gain is zero, show ties and unmet demand, and never promise one policy wins.

## Recording and release checks

- Verify launch, guided Back/Next/Restart, common shock, comparison, receipt, approval and download on the actual judging laptop.
- Record fresh actions and genuine computed changes; label any saved replay or fallback video honestly.
- Keep the mission, strategy worlds, chosen shock, paired control and independent receipt readable.
- Preserve the initial greedy win, ties, unmet demand and any zero/negative gain.
- Change a preference, approve the current revision and inspect the actual downloaded artifact.
- Keep private notifications, credentials and unrelated personal material off-screen.
- Check narration, captions, legibility, playback and measured output duration **at most 2:00**.
- Record the exact source/release and media used. Local checks do not establish publication, submission or eligibility.

If the browser fails, refresh and resume the persisted experiment. Diagnose a command error before retrying. Use an inspected recording only with explicit labeling. The earlier [92-second recording](artifacts/FORK-judge-demo.mp4) and [its evidence](docs/JUDGE_READINESS.md) remain historical fallback material; they do not show the newer guided tour.

Runtime is **Deterministic Planner Mode**, all data is synthetic, and OpenAI Codex substantially assisted development. No runtime LLM, deepagents or model API key is implemented. Export does not dispatch. The referee checks modeled consistency, not real-world safety or optimality. Scenario Studio is secondary; show its bounded clarification flow only if asked after the main story.
