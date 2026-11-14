# FORK — rehearse a decision before its consequences become real

**Submission draft.** Public repository publication, final media, track selection and submission are not completed. Replace required submission fields with verified artifacts before posting; this document is not a submission receipt.

## Inspiration

A route plan can look convincing until a van fails with meals still onboard. We wanted a way to inspect what a decision survives before asking someone to act on it. Food-bank logistics gives that question concrete constraints: limited inventory, receiving windows, volunteer shifts and chilled-vehicle compatibility.

## What it does

FORK creates three isolated strategy worlds from the same synthetic mission. Velocity, Resilience and Equity use published routing preferences. A user applies the same vehicle breakdown at the same time to all three, then compares actual recovery against the **same shocked initial plan without replanning**.

That paired view is the key moment: how much did adaptation change, separately from how much damage the shock caused? The answer can be zero. Users then adjust service/cost preferences, inspect routes, physical cargo events and independent checks, and approve a current verified revision for JSON or CSV export. Nothing is dispatched.

## How we built it

A Python/FastAPI coordinator combines OR-Tools routing, NetworkX directed roads, discrete-event execution and SQLite persistence. A separately implemented standard-library referee reconstructs movement, timing, inventory custody and metrics from evidence. React, TypeScript and Vite display synchronized local SVG maps and inspectable event histories.

This release uses **Deterministic Planner Mode**. It has no runtime LLM calls, deepagents integration, model API dependency or invented model activity. Development received substantial OpenAI Codex assistance across architecture, implementation, test authoring, debugging, review and documentation.

## Challenges

Breakdown recovery must preserve actual custody. An interrupted load cannot create cargo, a failed vehicle cannot donate stranded meals, and healthy in-progress services must remain locked. Joint depot grants must avoid promising the same stock twice. We made those rules explicit and checked them with independent replay and adversarial fixtures.

Separating physical validity from optimizer quality also mattered. The conventional greedy baseline delivers **224** initial meals, compared with **216 / 192 / 216** for Velocity / Resilience / Equity. We retain that result instead of claiming our named policies win. Their value is transparent preference comparison and recovery inspection, not demonstrated superiority over conventional methods.

## Evidence and current boundaries

The final suite has **84 Python tests**, **4 frontend model tests**, and **14 real-browser checks** passing. The independent referee report records **6,780 synthetic worlds**, zero invalid receipts and zero recomputed-metric differences, with additional targeted load-boundary checks after review. Frontend typecheck and production build passed. Browser checks cover every vehicle choice, actual exports, preference failures and ordering, saved-run recovery, narrow layouts, and a fresh simulation with external origins blocked. These results do not establish field performance or global optimality.

All geography, orders, priorities, volunteers, costs and emissions are synthetic. The model has one depot, fixed drivers, atomic orders, one breakdown per experiment and at most one recovery reload per healthy vehicle. There is no failed-cargo rescue, transfer, spoilage certification or production dispatch.

## What we learned

A useful decision tool should make its assumptions and losses easy to inspect. Independent physical evidence, an honest conventional baseline and a paired no-replan comparison tell a more useful story than a preferred policy always winning.

## What's next

Validate the workflow with a food-bank coordinator, evaluate broader declared scenarios against conventional methods, and extend only the constraints that actual operations require. Live AI strategists and sponsor integrations remain conditional future work.

## Credits and submission notes

Built with Python, FastAPI, Pydantic, Uvicorn, SQLite, OR-Tools, NetworkX, React, TypeScript, Vite, pytest, HTTPX and Playwright. Dependency locks record the versions. OpenAI Codex provided substantial AI-assisted development; no human-authorship percentage or organizer eligibility ruling is asserted.

Public repository: **https://github.com/ahmedhxssam/fork-ai** (created November 13, 2026 at 11:13 PM Eastern; public access verified). Actual screenshots and a genuine 37-second silent walkthrough are included in the repository. The live narrated pitch is separate. Check each sponsor's actual brief before selecting categories; there is no current live-model/deepagents/sponsor API claim or guaranteed award outcome. This file is a submission draft; the competition entry has not been submitted.
