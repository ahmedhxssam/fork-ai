# FORK guided judging mode

One food-bank morning, one shared breakdown, one decision a coordinator can inspect.

Start `make demo`, then open the [three-minute walkthrough](http://127.0.0.1:8000/?view=logistics&tour=1). For the actual contest presentation, open the [two-minute cut](http://127.0.0.1:8000/?view=logistics&tour=1&pace=120). Both guide the same working logistics app; the pace changes the rehearsal budget, not the simulator's results.

**The three-minute walkthrough is a rehearsal aid.** The supplied *F26 Onsite Hacker Packet*, p. 4, limits both the optional submitted video and the required in-person demo to **two minutes**. Use the short cut with judges. The [submission video](../artifacts/FORK-submission-demo.mp4), [captions](../artifacts/FORK-submission-demo.srt), [transcript](../artifacts/FORK-submission-demo-transcript.txt) and [storyboard](../artifacts/FORK-submission-demo-storyboard.json) follow the same story. See the [presentation release report](PRESENTATION_RELEASE.md) for the final recording's measured duration and checks.

## Eight chapters, at your pace

Use **Back** and **Next** to move between chapters. Navigation is manual: read the prompt, use the highlighted app action when required, then continue. **Restart tour** returns to the opening briefing; continuing into the comparison creates a new experiment. Saved experiments remain available. **Exit** returns to the ordinary workspace. Restarting the guide does not erase experiment history.

| Chapter | What to do | What the judge should understand |
|---|---|---|
| 1. One morning. Meals at stake. | Read the food-bank mission. | 240 available meals, 264 requested, 12 orders, three vehicles; every input is synthetic. |
| 2. Three plans. Equal starting conditions. | Compute the comparison and inspect the three worlds. | Velocity, Resilience and Equity are deterministic policy configurations with identical starting resources. |
| 3. A fair test needs a control. | Read the initial greedy and neutral-solver benchmark. | Greedy initially wins with 224 meals. Recovery is measured against the same initial plan under the same shock. |
| 4. Break the same vehicle. | Choose **Apply shared breakdown** for A at elapsed 1,500 seconds (09:25). | The shock is common; completed history stays fixed and failed cargo stays stranded. |
| 5. What did recovery actually save? | Compare adaptive and fixed-plan results. | All three adaptive totals are 168. Controls are 144 / 120 / 144; gains are +24 / +48 / +24. A larger gain need not mean a better final result. |
| 6. Better depends on your priorities. | Review the preference controls and comparison. | A preference score helps a person compare valid results; it cannot establish universal superiority. |
| 7. Trust the receipt, not the pitch. | Open a referee receipt and inspect one physical detail. | A separate implementation reconstructs modeled movement, custody, timing and metrics. |
| 8. The decision stays human. | Review, approve the current revision and download the packet. | Approval belongs to current evidence and preferences. Export is simulated planning evidence; no dispatch occurs. |

For an exact timed narration, use the [three-minute and two-minute scripts](PITCH.md). For launch checks and an unassisted click sequence, use [DEMO.md](../DEMO.md).

## Keep the story honest

The standard rehearsal uses seed 26 and vehicle A at elapsed 1,500 seconds. A judge can explore other supported failures in the workspace; then narrate the actual computed values. Preserve ties, unmet demand, zero gains and initial baseline losses. An unshocked plan is a reference, not the fixed-plan control used to isolate recovery.

FORK runs locally in **Deterministic Planner Mode**. There is no runtime LLM, model provider, deepagents execution or required model API key. OpenAI Codex substantially assisted development. The separate referee checks consistency within declared synthetic physics; it does not establish optimality, field impact or real-world safety.

Scenario Studio is secondary. If asked, show its bounded interview for missing/conflicting facts and reviewed resource/task model. It is not unrestricted natural-language understanding and does not infer arbitrary routing or domain physics. Keep it out of the short food-bank presentation unless a judge requests it.

## Contest fit

Choose **Business and Enterprise** as the single main track: the coordinator uses an operations dashboard to compare plans, handle disruption and review a decision. Best Overall Hack consideration is automatic upon submission; it is not a second main-track selection. The supplied packet lists a **PlayStation 5 Disc Edition per winning member** for Best Overall and says a main-track winner cannot also win Best Overall. This is an award description, not a forecast or guarantee.

The current app has no implemented sponsor integration. Do not select a special track by relabeling deterministic policies as agents or development assistance as a runtime AI feature. See the [submission pack](../SUBMISSION_READY.md) for source-based track advice and remaining entry actions.
