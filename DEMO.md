# FORK: two-minute food-bank demo

**Business & Enterprise → Operations planning → Food-bank delivery resilience**

Use **http://127.0.0.1:8000/?view=logistics**. The root page remains Scenario Studio and links to the food-bank demo. Tell one story: a delivery vehicle breaks down; the coordinator compares replanning with a fixed plan under the same shock, checks the evidence, then approves a simulated result.

Runtime is **Deterministic Planner Mode**. The three strategy names describe published priorities, not autonomous LLM agents. All mission data is synthetic. Use [the spoken pitch](docs/PITCH.md).

Current backup: [92-second narrated recording](artifacts/FORK-judge-demo.mp4), [captions](artifacts/FORK-judge-demo.srt) and [verification](docs/JUDGE_READINESS.md). It contains genuine browser actions with a local system voice.

## Before presenting

```sh
make setup
make test
make demo
```

In another terminal, run `make test-browser` against the running server. Record actual results and any failure in the release evidence; an unavailable browser is not a pass. Install dependencies and browser binaries before relying on an offline demonstration. Keep the server terminal running and use one backend worker.

Start a fresh seed-26 experiment using the interface or `make reset`; stored history is preserved. Confirm the category, synthetic-data and deterministic-mode labels. A resumed experiment is a **saved replay**, not fresh computation. Close unrelated tabs and notifications, and use a legible laptop viewport.

## Exactly two minutes

| Time | Visible action | What to explain |
|---|---|---|
| 0:00–0:15 | Show the mission and choose **Fork the mission** | Food-bank planning: 240 meals available, 264 requested, three vehicles. |
| 0:15–0:35 | Show the three worlds and initial benchmark | Same starting resources, different priorities. Greedy initially delivers more than all three named policies. |
| 0:35–1:00 | Select vehicle A at elapsed 1,500 seconds (09:25); apply breakdown | Every isolated world gets the same vehicle/time shock. The engine replans only remaining work. |
| 1:00–1:25 | Open the fixed-plan comparison and recovery gain | Compare adaptive execution with the original plan under the same shock. Read actual results; the unshocked reference is a different comparison. |
| 1:25–1:40 | Inspect one cargo/event detail and referee receipt | The separate referee reconstructs movement, cargo, timing and results. A receipt checks modeled consistency. |
| 1:40–2:00 | Change preferences, approve current evidence and download | The person chooses. Approval belongs to the current revision; exports contain simulated evidence, not dispatch orders. |

For the seed-26 rehearsal, preserve these reference values:

| Strategy | Initial meals | A-at-1,500 adaptive | Same-shock fixed plan | Recovery gain |
|---|---:|---:|---:|---:|
| Velocity | 216 | 168 | 144 | +24 |
| Resilience | 192 | 168 | 120 | +48 |
| Equity | 216 | 168 | 144 | +24 |

Initial greedy delivers **224**; the neutral solver delivers **216**. All three adapted outcomes above tie on delivered meals. Resilience's larger gain is relative to its weaker fixed-plan control. These figures describe this scenario and shock; confirm them on the release being shown.

A judge may choose A, B or C and another supported time. If so, read the computed result and abandon the reference-number narration. A late shock may have no effect; a chilled-vehicle failure may leave chilled demand unrecoverable. Say zero when gain is zero, show ties, and never promise that one named policy wins. If computation takes longer, explain that it is running and shorten narration.

## Recording and release checklist

- [ ] Verify the actual judging-laptop launch, shock, comparison, receipt, approval and download journey.
- [ ] Record fresh actions and genuine computed changes; label saved replay or fallback video honestly.
- [ ] Keep the mission, three worlds, chosen shock and fixed-plan control readable.
- [ ] Preserve greedy's initial win, unmet demand, ties and any zero/negative recovery gain.
- [ ] Inspect one physical detail and one independent receipt.
- [ ] Change a preference, approve the current revision and open the downloaded artifact.
- [ ] Keep credentials, private notifications and unrelated personal content off-screen.
- [ ] Check narration, playback, legibility and exported duration **at most 2:00**.
- [ ] Record the exact source/release and video used. Existing silent clips are historical version evidence until the final recording is captured and inspected.

If the browser fails, refresh and resume the persisted experiment. Diagnose a command error before retrying. If fresh computation cannot run, use a genuine inspected recording or saved experiment with explicit labeling. Do not claim an unobserved browser pass, offline run, publication or submission.

Scenario Studio is secondary: show its bounded clarification/model-authoring flow only if asked or if time remains after the logistics story. It is not needed to explain the main use case. [Simulation semantics](SIMULATION.md), [checks and evidence](TESTING.md), [Devpost draft](DEVPOST.md).
