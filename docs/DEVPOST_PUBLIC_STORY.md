**Rehearse before you commit.**

[Download the 1:55 narrated demo (MP4)](https://github.com/ahmedhxssam/fork-ai/blob/codex/fork/artifacts/FORK-submission-demo.mp4) · [Source and setup](https://github.com/ahmedhxssam/fork-ai) · [Guided presentation](https://github.com/ahmedhxssam/fork-ai/blob/codex/fork/docs/JUDGING_MODE.md)

## Inspiration

What if you could see the consequences of a decision before actually making it?

Doctor Strange exploring possible futures in *Infinity War* inspired the question. FORK cannot predict the future, but it can test different decisions inside an explicit model and show what happens when things go wrong.

A delivery plan might look good until a vehicle breaks down. I wanted to build a way to rehearse that decision before committing scarce resources.

## What it does

FORK helps an operations coordinator compare plans, apply the same disruption and inspect the evidence before choosing a simulated result.

The main demonstration is a synthetic food-bank mission: **240 meals available, 264 requested, 12 destinations and three vehicles**. Velocity favors throughput, Resilience preserves flexibility, and Equity prioritizes high-need destinations. Every world starts with the same resources and constraints.

When vehicle A fails at **09:25**, completed deliveries stay completed and its cargo stays stranded. Healthy vehicles can replan the remaining work. All three adapted plans deliver **168 meals**. Under the same failure with their original routes fixed, they deliver **144, 120 and 144**. Recovery gains are **+24, +48 and +24**; a larger gain does not mean a better final meal total.

The initial conventional greedy baseline delivers **224 meals**, beating all three named strategies (**216 / 192 / 216**). FORK keeps that loss visible. Other failures can produce ties or no gain.

A separate referee reconstructs movement, cargo, capacity and timing, then recomputes the metrics. The coordinator can change priorities, inspect its receipt, explicitly approve the current revision and export JSON or CSV. Nothing is dispatched.

### A guide judges can actually follow

The new **eight-chapter judging mode** highlights the relevant app areas and gives short explanations. Back, Next, Restart, keyboard navigation and a pauseable timer make it easy to rehearse or answer questions. The three-minute mode is for learning; the two-minute pace fits the contest presentation limit. Restarting preserves saved work.

The new **1:55, 1080p demo** follows real browser actions with numbered titles, short step lists, captions, local Kokoro neural narration and a simple animated FORK logo close. The built-in **af_heart** voice is synthetic, not my voice, and requires no API key. This film-production tool is separate from FORK's deterministic runtime. A shared minimal identity connects the app, guide and film.

### Another kind of problem

Scenario Studio is a secondary workflow. Describe a supported operational problem in ordinary words; it asks about missing or conflicting details, then lets you review a bounded resource/task model before simulation. It does not infer arbitrary domain physics or understand unrestricted language.

## How I built it

Python, FastAPI, Pydantic and SQLite handle validation, persisted experiments and revision-bound decisions. Google OR-Tools generates delivery plans; NetworkX represents the directed road network. A custom discrete-event simulator executes the plans, failure and bounded recovery. A separate standard-library referee checks physical evidence independently. React, TypeScript and Vite provide maps, synchronized playback, comparison and human review.

**Runtime uses deterministic optimization and simulation, with no language-model provider or API key connected. OpenAI Codex substantially assisted architecture, implementation, tests, debugging, review and documentation.** The strategy names are policy configurations, not autonomous LLM agents.

## Challenges I ran into

Physical history cannot be rewritten. Failed cargo cannot appear in a healthy vehicle, completed deliveries cannot disappear, and vehicles cannot claim the same stock twice.

Fair comparisons also matter: every strategy must face the same shock, and recovery must be compared with that strategy's original plan under the same failure. A physically valid plan can still leave demand unmet.

The separate referee checks consistency within the declared synthetic model. It does not prove route optimality or real-world safety.

## Accomplishments I'm proud of

FORK connects real planning, simulation, paired controls, independent verification and human approval in one working local loop. The current release passed **252 Python tests, four frontend model tests and all 44 real-browser tests**, including failure/retry, saved work, mobile/tablet layouts, guide navigation, approval and downloadable evidence.

The repository includes the finished film, raw browser take, captions, storyboard, reproducible production scripts, screenshots and actual approved synthetic outputs.

## What I learned

Optimization and decision-making are different. A plan that looks best initially may behave differently after a disruption. A larger recovery gain may only reflect a weaker starting control. Useful recommendations need visible tradeoffs and evidence that can be checked.

## What's next for FORK

The next step is a bounded AI authoring adapter: translate a user's description into the reviewed simulation schema while keeping execution and verification deterministic. Real operational datasets and richer disruptions would need explicit model extensions and validation.

The vision is simple: make testing a decision before acting on it as natural as testing code before deploying it.
