# Conversation engine implementation report

Implemented `backend/studio/intake.py` with a deterministic, local interview that produces the existing validated workflow model. No credentials, provider calls, generated code, canned scenario substitution, or changes to engine/referee semantics are involved.

## Contract and provenance

- `intake(brief, answers)` replays an accepted answer prefix. Each next-question ID incorporates the brief digest and accepted-history digest. Changing the brief or an earlier answer makes later IDs stale.
- Rejected answers are applied to a detached candidate interview and cannot change facts, pending questions, or accepted answers. Wrong IDs, malformed entries, excess answers, oversized text, uncertain/negative numeric responses, and out-of-range values return helpful issues.
- Exactly one question is exposed at a time. A ready result has a strict-schema-validated model, stable canonical model hash, no pending question, explicit accepted assumptions, extracted source facts, known facts with source text, and accepted answer history.
- Scope review adds the root-approved optional `Question.details: string[]` presentation field. These bullets must be visible before accepting scope; the concise prompt alone does not communicate all assumptions.
- Maximum input sizes: 30,000 brief characters, 100 answers, 2,000 characters per answer. Existing schema limits remain authoritative: 80 tasks, 12 resource pools, capacity 12 per pool, 720 minutes.
- `describe_model` provides a human summary for saved legacy models without turning legacy grammar into natural authoring text.

## Useful supported language

The extractor handles everyday quantities and number words (one through nineteen plus supported tens and combinations), minute/hour windows, named staffing/resource pools, quantified work with per-job duration, queue descriptions with missing values, separate “each repair takes…” claims, deadlines, and before/after relationships between recognizable work groups. Identical jobs expand into individual engine tasks. It asks for missing essential capacity, work count, per-job duration, and planning time rather than inventing those values. A short ordinary prose work answer can introduce a group, for example “Six bike repairs, around twenty minutes each.” Multiple recognized resource pools require explicit assignment when it is unclear who does the work.

Different counts and duration/window claims remain separate candidates and appear as quoted conflicts. “Two or three volunteers,” tentative staff availability, and negated staffing do not become silently certain facts. Staffing needs a bounded affirmative availability frame; unrecognized status such as “are sick” requires confirmation. A benign request to help fit work into an afternoon is kept as context, not misclassified as an excluded operational requirement. An unhandled mixed time such as “one hour and thirty minutes” requires a confirmed total rather than silently becoming one hour. This ambiguity gate is shared by every time slot, including later per-job duration claims and deadlines. Numeric answers may include ordinary units, including a decimal number of hours when its conversion is a whole minute.

The three shipped prompts are ordinary prose: an incomplete repair clinic, genuinely conflicting laptop-repair staffing/time claims, and a separate IT queue with a group dependency and deadline. The conflict example uses 45-minute jobs so staffing/window choices affect actual completion. The model title comes from the extracted work labels.

## Explicit simplifications and limits

This remains bounded deterministic extraction, not general language understanding. Unfamiliar wording can require a follow-up even when a human would infer the answer. Role recognition is deliberately conservative; arbitrary nouns ending in “ers” or “ors” are not treated as people. Counts of neighbors bringing an unknown quantity of objects are not treated as job counts. Unrecognized clauses are retained for scope review, including operational requests appended to otherwise recognized staffing statements.

The mandatory scope decision explicitly approves one resource unit per job, work available at time zero, checkpointable processing, equal priority/completion value, session-end deadlines when unspecified, and no other dependencies beyond those shown. A group dependency means **all** predecessor-group jobs finish before **any** successor-group job starts. Per-item pairing is not implemented; the group-wide interpretation requires explicit scope agreement.

Costs, budgets, stock/materials, travel, messaging, physical safety decisions and other unrecognized details are excluded, with quoted unmodeled clauses and recorded assumptions. Consequently cost comparisons can legitimately tie. Choosing “I need to change the scope” keeps the scenario unready and directs the user to edit the original description. These exclusions are not a claim that the original real-world problem is fully represented.

Absolute clock times, arbitrary pronoun resolution, complex conditional policies, per-item dependency pairing, compound time answers, release-time inference, costs and inventory are not general natural-intake features. Users can clarify supported primitives or explicitly accept the limited scope. Cycles, aggregate task limits and other schema conflicts prevent readiness and display a correction issue; the engine does not silently repair them. Legacy compiler/API behavior remains separate.

## Executed checks

Test-first evidence was observed in this task:

1. Initial nine tests failed collection because the intake module did not exist, then passed after implementation.
2. Added adversarial regressions failed for a staffing quantity captured as a job quantity, ordinary “orders” classified as staffing, and rejected answers mutating state; each was fixed and rerun.
3. Further observed RED cases covered hidden compound operational clauses, real window conflicts, unknown bike quantities, oversized numeric overflow, negative/tentative numeric responses, indefinite articles mistaken for one, required/unavailable staff mistaken for capacity, mixed time truncation, cross-bound deadlines, unsupported duration units, unknown leading/trailing qualifications, and incompatible time units on count questions; fixes passed their targeted suites. Leading and trailing qualification preservation uses consumed-match boundaries rather than a list of domain keywords.
4. The latest targeted run of intake, API integration, and independent acceptance tests passed **70 tests**. The independent acceptance checks exercise actual engine/referee outcomes for changed capacity/duration, not only schema shape.

Final executed full regression: `.venv/bin/python -m pytest -q` → **252 passed, 4 warnings in 2.26s**. Warnings were existing Starlette/httpx and OR-Tools SWIG deprecations. The 49 direct intake cases, API checks and independent acceptance checks are included. Browser interaction, production deployment, event eligibility, and submission are outside this engine report's verification scope. No commit or publication was performed by this worker.
