# FORK: two-minute food-bank pitch

**Track:** Business & Enterprise. **Use case:** Operations planning → Food-bank delivery resilience.

Open `http://127.0.0.1:8000/?view=logistics`. Use real computed outcomes. The rehearsal below uses seed 26, vehicle A and elapsed 1,500 seconds (09:25). If a judge changes the shock, read the actual result instead. See [the demo guide](../DEMO.md) for reference numbers and the release checklist.

**0:00–0:15 — Show the mission; choose Fork the mission.**

“A food bank has 240 meals, 264 requested, and three delivery vehicles. What happens when one vehicle breaks down? FORK lets the coordinator rehearse that decision before dispatch.”

**0:15–0:35 — Show the three plans and initial benchmark.**

“Three strategies start with identical resources and different priorities. This runs deterministically with a routing solver and simulator. We show the conventional greedy baseline too: it initially delivers 224 meals and beats all three named policies.”

**0:35–1:00 — Apply vehicle A's breakdown at 1,500 seconds.**

“Now the same vehicle fails at the same time in every world. Completed work stays completed, failed cargo stays stranded, and recovery can change only the remaining plan. The question is how much replanning helps under this exact disruption.”

**1:00–1:25 — Show adaptive versus fixed-plan outcomes.**

“Here, all three adapted plans deliver 168 meals. Their fixed-plan controls deliver 144, 120 and 144 under the same shock. The larger recovery gain does not mean a better final outcome. Different shocks can produce ties or no gain.”

**1:25–1:40 — Open one cargo/event detail and referee receipt.**

“A separate referee reconstructs movement, cargo and timing, then recomputes the results. This checks consistency inside our synthetic model. It does not prove real-world safety or an optimal route.”

**1:40–2:00 — Change preferences, approve and download.**

“The coordinator reviews priorities, approves the current evidence and exports a simulated-plan packet. Nothing is dispatched. FORK is operations planning with a fair comparison, inspectable evidence and a person making the final decision.”

## Short answers for judges

**What is the product?** A local decision-rehearsal tool for an operations coordinator. The primary example is food-bank delivery resilience; Scenario Studio is an existing secondary way to clarify and author bounded resource/task scenarios.

**What is technically distinctive?** The same disruption across isolated worlds, an adaptive-versus-fixed-plan control, independent evidence reconstruction and approval/export tied to current evidence. Routing, scheduling and simulation themselves already exist.

**Are these AI agents?** No. Runtime uses deterministic policy configurations, a simulator, a separate referee and fixed preference comparison. OpenAI Codex substantially assisted development. No runtime LLM, deepagents, model API key or sponsor integration is implemented.

**Why does greedy initially win?** The named strategies encode different priorities and reserve settings, not proven superiority. The initial totals are greedy **224**, Velocity **216**, Resilience **192**, Equity **216**. Under A at 1,500 seconds, adapted totals are **168 / 168 / 168**, controls **144 / 120 / 144**, gains **+24 / +48 / +24**. Read each comparison for what it measures.

**How general is it?** Logistics has declared vehicle/cargo/road rules. Scenario Studio separately supports a bounded resource/task model and asks about missing or conflicting inputs; it does not infer arbitrary domain physics or unrestricted prose.

**What do checks establish?** The tested behavior and consistency of declared models. Current release/browser evidence belongs in [TESTING.md](../TESTING.md); it does not establish field impact, operational safety or competition eligibility.
