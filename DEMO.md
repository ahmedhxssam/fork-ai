# Demo and recording

The default demo is **Scenario Studio**: natural issue description → missing/conflicting-detail questions → plain model review → three computed futures → common outages → independent evidence → human approval. Use [the conversational guide](docs/CONVERSATIONAL_INTAKE.md) and [two-minute pitch](docs/PITCH.md). Runtime remains deterministic and credential-free; the interview has bounded language/model support.

For the incomplete repair example, answer “Six bikes”, “About 45 minutes each”, and “We have two hours”. Review its simplified scope and run: two volunteers complete four of six modeled repairs. Then show the conflicting-details example and explicitly resolve available staff and the room window. Choose three technicians and 90 minutes: all six 45-minute jobs finish in that model. Read actual results; do not promise different policies or a preferred strategy must win. The demonstration is that clarified facts change executable inputs and consequences.

The retained logistics walkthrough below runs at `http://127.0.0.1:8000/?view=logistics`. Its measured recovery story has no predetermined winning policy. The earlier silent video documents that logistics version.

## Before presenting

```sh
make setup
make demo
```

Open `http://127.0.0.1:8000` for Studio or add `?view=logistics` for the food-bank lab. Use a legible laptop viewport and close unrelated tabs/notifications. Complete `make test` and the real-browser journey before relying on the demo. Keep the server terminal running. Install dependencies and browser binaries before disconnecting the network.

Start a fresh seed-26 experiment using the interface's reset/new-experiment action, or `make reset`. Reset preserves stored history. Confirm the mode and synthetic-data labels. If resuming, say **saved replay**; do not present it as freshly computed execution. A backup recording is useful only after it has actually been captured and checked.

## Exactly two minutes

| Time | Visible action | Narrative purpose |
| --- | --- | --- |
| 0:00–0:15 | Show mission stock/demand and synthetic label | Establish 240 available meals for 264 requested |
| 0:15–0:35 | Launch three worlds, point to different routes/settings | Identical resources, three declared preferences; deterministic mode |
| 0:35–0:55 | Play synchronized clock, pause near a useful event | Physical custody and completed work are facts of the simulation |
| 0:55–1:20 | Ask judge to choose vehicle; confirm time; inject breakdown | Same actual resource/time shock, genuine residual planning |
| 1:20–1:45 | Show no-replan counterfactual and recovery gain; change weights | Isolate adaptation, then reveal preference-dependent tradeoffs |
| 1:45–2:00 | Open a referee receipt, approve and download | Inspectable evidence and explicit human selection |

Use the timed verbatim [pitch script](docs/PITCH.md). If computation takes longer than the rehearsal budget, explain that it is running and shorten commentary; do not substitute fabricated results or hide a saved replay. If gains are zero, say zero. If policies tie, show the tie. Mention the greedy benchmark honestly when discussing quality.

A common rehearsal choice is A at elapsed 1,500 seconds (09:25), but the judge may choose A, B or C and any supported time. The outcome is computed, not scripted. A late shock may have no effect; loss of the chilled vehicle can leave chilled demand unrecoverable.

## Recording checklist

- [ ] Run the exact local setup and current checks; note any unresolved failure.
- [ ] Reset to seed 26 and confirm the visible mode, scenario and synthetic assumptions.
- [ ] Record genuine browser actions and actual computed changes; show saved replay labels when applicable.
- [ ] Keep all three worlds, clock, shock choice and counterfactual readable.
- [ ] Show actual recovery gain, including zero or negative values; do not promise a winner.
- [ ] Show one physical detail: stranded cargo, locked service, depot stock or remaining shift.
- [ ] Briefly open the independent receipt and show its validity/checks/hash.
- [ ] Change a preference, approve the current revision, and verify the downloaded artifact opens.
- [ ] Keep credentials, private notifications and unrelated personal content off-screen.
- [ ] Check audio, legibility and final duration **at most 2:00** in the actual exported video.
- [ ] Verify the video file and its playback before describing it as delivered.

## Recovery during a presentation

If the browser fails, refresh and resume the persisted experiment. If a command fails, show its actual error and retry only after understanding it. If fresh computation cannot run, use a genuinely recorded backup or saved experiment with explicit labeling. Do not claim an unrecorded video, browser pass, publication or live integration.

The JSON export is full approved simulated evidence. The CSV lists completed simulated deliveries with fixed volunteers; it is not an outbound dispatch integration. All costs/emissions, priorities and geography are synthetic. See [SIMULATION.md](SIMULATION.md) for the precise model boundaries.
