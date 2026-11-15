# FORK: one story, two presentation lengths

**Business and Enterprise. Operations planning for food-bank delivery resilience.**

Use the [three-minute guide](http://127.0.0.1:8000/?view=logistics&tour=1) to rehearse. Use the [two-minute cut](http://127.0.0.1:8000/?view=logistics&tour=1&pace=120) for judging: the supplied packet caps both the live presentation and optional video at two minutes. [Click guide](../DEMO.md) · [guided mode](JUDGING_MODE.md).

These scripts use seed 26, vehicle A and elapsed 1,500 seconds (09:25). If the judge changes the shock, read the actual computed result. Pause for computation, shorten narration as needed, and keep the two-minute contest limit.

## Three-minute rehearsal

**0:00–0:25 — One morning. Meals at stake.** Show the mission.

“A food bank has 240 meals, 264 requested, and three vehicles. Its coordinator has to make a plan before knowing what will go wrong. FORK rehearses that decision: what if one vehicle breaks down, and which meals can still arrive? This is synthetic planning data.”

**0:25–0:50 — Three plans. Equal starting conditions.** Compute the worlds.

“Velocity, Resilience and Equity start with the same resources. Their priorities and reserves differ, so their routes differ. These are deterministic solver configurations. A simulator executes each plan in its own copied world. No language model or API key is involved.”

**0:50–1:15 — A fair test needs a control.** Point to the baseline.

“We keep the conventional benchmark visible. Greedy initially delivers 224 meals and beats every named strategy. FORK is useful for making the comparison inspectable, even when a policy loses. To measure recovery, we need the original plan under the same breakdown, without replanning.”

**1:15–1:40 — Break the same vehicle.** Apply the shared breakdown.

“Vehicle A now fails at 09:25 in every world. Completed deliveries remain completed. Cargo on the failed vehicle stays stranded. The recovery planner can change only the remaining work within the declared vehicle and cargo rules. It cannot repair history to improve its score.”

**1:40–2:10 — What did recovery actually save?** Read the paired results.

“All three adapted plans deliver 168 meals. Keeping their original plans under this shock would deliver 144, 120 and 144. Recovery therefore adds 24, 48 and 24 meals. Resilience has the largest gain, but starts from the weakest control and ties on the final meal total. Other shocks can yield no gain.”

**2:10–2:25 — Better depends on your priorities.** Review preferences.

“A coordinator may value different outcomes. Preferences help compare valid results; a score cannot decide whose priorities are right. We show the tradeoffs and preserve ties.”

**2:25–2:45 — Trust the receipt, not the pitch.** Open a receipt.

“A separate referee reconstructs movement, cargo, timing and metrics from the evidence. This establishes consistency inside the synthetic model. It does not prove optimality or real-world safety.”

**2:45–3:00 — The decision stays human.** Approve and download.

“The coordinator approves current evidence and exports a simulated-plan packet. Nothing is dispatched. OpenAI Codex substantially assisted development. FORK makes a disruption, a fair comparison and the final human decision visible.”

## Two-minute contest cut

**0:00–0:15 — Mission.**

“A food bank has 240 meals, 264 requested, and three vehicles. What happens when one breaks down? FORK lets the coordinator rehearse the decision before dispatch. Every input here is synthetic.”

**0:15–0:30 — Three worlds.**

“Three deterministic strategies start equally and use different priorities. A routing solver proposes plans; a simulator executes them. No runtime language model or model API key is involved.”

**0:30–0:45 — Honest control.**

“Greedy initially delivers 224 meals, beating every named policy. Recovery must be compared with the original plan under the same shock, without replanning.”

**0:45–1:00 — Shared breakdown.**

“Vehicle A fails at 09:25 in every world. Completed deliveries stay completed and failed cargo stays stranded. Recovery can change only the remaining work.”

**1:00–1:20 — Recovery.**

“All three adapted plans deliver 168 meals. Fixed plans deliver 144, 120 and 144: gains of 24, 48 and 24. The largest gain starts from the weakest control. Final meal totals tie.”

**1:20–1:30 — Priorities.**

“Preferences help the coordinator compare valid results. They do not make one strategy universally best. Other shocks can produce no gain.”

**1:30–1:45 — Receipt.**

“A separate referee reconstructs movement, cargo, timing and metrics. It checks our model's consistency, not real-world safety or optimality.”

**1:45–2:00 — Human decision.**

“The person approves current evidence and downloads a simulated packet. Nothing is dispatched. OpenAI Codex substantially assisted development. FORK makes the decision inspectable before its consequences become real.”

## Questions judges may ask

**Who is it for?** An operations coordinator rehearsing disruption decisions. The food-bank morning is a concrete synthetic example; no food-bank deployment or operator consultation is claimed.

**Why does this belong in Business and Enterprise?** It improves an operations-management workflow: compare plans, handle a disruption, review evidence and approve a decision. The supplied main-track description includes streamlining business management, dashboards and analytics. Food-bank context also has social value, but that does not require a second main-track entry.

**What is technically distinctive?** Shared disruption across isolated worlds, paired adaptive-versus-fixed-plan controls, independent evidence reconstruction and revision-bound approval/export. Routing, scheduling and simulation are established techniques; the project combines them into an inspectable decision workflow.

**Are these AI agents?** The runtime roles are deterministic policies, a simulator, a separate referee and fixed preference comparison. There are no runtime LLM calls, deepagents orchestration or model credentials. OpenAI Codex substantially assisted architecture, implementation, tests, debugging, review and documentation; that is development assistance, not a runtime feature.

**Why does greedy win?** The strategies encode priorities and reserve choices, not proven superiority. Initial meals are greedy **224**, neutral solver **216**, Velocity **216**, Resilience **192**, Equity **216**. Under A at 1,500 seconds, adaptive totals are **168 / 168 / 168**, paired controls **144 / 120 / 144**, gains **+24 / +48 / +24**. A large gain can start from a weak plan.

**Does the referee prove it is correct?** It independently reconstructs declared physical events and metrics without importing planner/simulator validation helpers. A valid receipt establishes consistency with those rules. It does not establish that the assumptions fit real operations, the route is globally optimal or deployment is safe.

**Can it handle any scenario?** Logistics has explicit road, vehicle and cargo rules. Secondary Scenario Studio uses a bounded prose interview, clarification and reviewed typed inputs for resource/task scheduling. It detects missing/conflicting facts within supported patterns; it is not unrestricted language understanding and cannot infer arbitrary domain physics or vehicle routes.

**What does approval do?** It binds a person's selection to current evidence and preferences. Changing them invalidates approval. JSON/CSV exports contain simulated evidence and completed-delivery results; no volunteer is contacted and no vehicle is dispatched.

**What is next?** Validate assumptions with actual operators and add semantics only with meaningful independent checks. A future model adapter could propose bounded typed inputs; it could not author authoritative metrics, bypass the referee or approve its own work.

**What is verified?** Use the [presentation release report](PRESENTATION_RELEASE.md) and [test history](../TESTING.md) for executed checks. Publication, video hosting, eligibility and competition submission need their own evidence. None follows from local tests or from a polished presentation.
