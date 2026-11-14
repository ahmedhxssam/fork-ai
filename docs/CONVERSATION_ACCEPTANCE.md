# Conversational intake acceptance

This document records independent acceptance cases for the bounded deterministic interview in `docs/superpowers/specs/2026-11-14-conversational-intake.md`. A natural phrase may be understood directly or resolved through a focused follow-up. These cases do not require unrestricted language understanding. They do require an ordinary-language route to an executable, source-backed model, without requiring the user to learn the retained compiler grammar.

## Evidence status

Prepared and checked on 2026-11-14. The independent backend suite in `tests/test_conversation_acceptance.py` passes **14 checks**. The combined command `.venv/bin/python -m pytest -q tests/test_conversation_acceptance.py tests/test_studio_intake.py` passes **32 checks**. This records that targeted run, not a full application or browser result.

Verified conversational journeys cover staffing contradictions, unknown timings, ordinary combined staffing/work sentences, a separate laptop operation, both window claims in a conflict, changed-original and changed-earlier-answer replay protection, source-safe handling of numeric nouns, and explicit exclusion of travel, medication and physical safety requests. Staff and duration answers produce different actual engine outcomes with valid independent receipts. Cases in the table remain a broader acceptance catalog; not every phrasing and browser journey below has been exercised end to end.

The hand-derived scheduling expectations below were checked directly with `.venv/bin/python`, `backend.studio.engine.simulate` and `backend.studio.referee.verify`: two people/45 minutes completed four jobs; three people/45 minutes completed six in 90 minutes; two people/15 minutes completed six in 45 minutes. All three independent receipts were valid. This verifies the acceptance oracle, not the new conversational extraction.

Initial probes found false worker pools from “six neighbors” and “three quarters of an hour”, staff counts being reused as job counts in combined sentences, a missing repair stage in a partly understood sentence, an unquoted room/work-window conflict, and a hidden physical safety request. These were reported to the intake owner and fixed; the independent regression checks now pass. “Six neighbors brought bikes” does not establish how many bikes exist and now stays unresolved rather than inventing that quantity. Paired inspection/repair work is allowed to reach explicit scope review with the unsupported repair clause quoted; this check does not claim that per-bike dependency pairing is implemented.

## Essential journeys

| Case | User's opening description | Required behavior |
| --- | --- | --- |
| A. Unknown timings | “Six bikes need repairing. Two volunteers can work on them this afternoon, and the workshop is open for two hours. I do not know how long the repairs take.” | Keep six jobs, two available people, and a 120 minute window. Ask how long a repair takes. Do not make the model executable before that answer and explicit acceptance of any simplifying assumptions. Accept a phrase such as “About 45 minutes per bike.” |
| B. Staff contradiction | “We have six bikes waiting for repair. Two volunteers can help; actually three people said they would be there. Each bike takes 45 minutes and we have two hours.” | Quote both staffing claims and ask which count is available for the modeled work. Do not silently choose the last count. Choosing two versus three changes the resource capacity and model hash. |
| C. Ordinary paraphrase | “There are six bicycles in the queue. A pair of volunteers can tackle them for the next couple of hours. Allow three quarters of an hour for each one.” | Extract supported facts or ask narrowly about ambiguous expressions. Let the user confirm two people, 120 minutes and 45 minutes each without rewriting the entire issue into declarations. |
| D. Work unspecified | “I am organizing a repair afternoon and I am worried we will run out of time. Two volunteers are available for two hours.” | Ask what work is waiting. Accept an ordinary follow-up such as “Six bike repairs, around 20 minutes each.” Do not substitute a preselected example queue. |
| E. Separate operation | “Three technicians need to prepare eight laptops for an event. Each setup takes twenty minutes. We have ninety minutes before the doors open.” | Build the same generic scheduling schema with the actual laptop quantities and timings, or ask specific missing questions. Labels and work must describe this scenario rather than a repair template. |
| F. Explicit sequence | “Two volunteers are here for two hours. We need to inspect six bikes, taking ten minutes per inspection, and then repair each one for thirty minutes. Each bike must be inspected before it is repaired.” | Model the paired dependencies or explain the supported limitation and obtain agreement on an explicit simplification. Never silently schedule the inspection and corresponding repair concurrently. |
| G. Time conflict | “We have two people and six repairs, twenty minutes each. We can work for two hours, but the room is only available for ninety minutes.” | Ask which planning window is actually usable, showing the conflicting statements. Never overwrite one with the other while presenting the result as settled. |
| H. Partial availability | “Three volunteers can do six repairs, forty minutes each, during the next two hours. One volunteer has to leave after the first hour.” | Preserve the availability change through a supported event or ask for an explicit supported simplification. Never flatten it to three people for the whole window without acknowledgment. |

## Answers must affect the real model and results

Use A or B to obtain two completed interviews with identical work and a 120 minute horizon. Confirm equal priority, all jobs available at the start, one person per repair, no extra constraints and no disruptions where requested.

1. **Two versus three volunteers, 45 minutes per job:** the actual model has six tasks of 45 minutes. Throughput completes four with two volunteers and six with three. The independent referee must accept both receipts. The intake's own summary is insufficient evidence.
2. **15 versus 45 minutes per job, two volunteers:** the actual model contains the selected duration on every expanded job. All six finish in 45 minutes for the 15 minute answer; four finish by the horizon for the 45 minute answer. Both hashes and real schedules differ.
3. **Different work quantity:** change “six” to “eight” while preserving all other input. Eight actual jobs must appear, not merely a summary change. Old answer IDs cannot silently carry over.

These are hand-derived consequences of the generic engine's capacity and timing rules, not claims of planner optimality. All three deterministic policies may tie; a tie is acceptable.

## Replay, correction and incomplete input

- Repeating the exact brief and answer history produces identical next question IDs and output. Returned questions remain one at a time.
- A wrong question ID, an old ID from another brief, an answer to a future question, or a later answer after an invalid answer must never populate a different field. The accepted prefix remains inspectable.
- An invalid numeric reply such as “some people” or zero keeps the current question pending with a helpful issue. The browser retains the failed text for correction.
- Editing the initial description changes the brief hash and invalidates its old answer IDs, reviewed assumptions and executable results.
- Editing an earlier answer discards or explicitly reconfirms dependent answers. The resulting history must replay to the model actually launched.
- Missing a job quantity, available worker count, duration or planning horizon creates a focused question. Missing optional costs, stock or priorities should lead to a small, explicit scope decision rather than a long questionnaire.
- Number words one through twelve and short answers such as “three”, “45 minutes each” or a displayed choice value are useful supported inputs. Ambiguous ranges such as “two or three volunteers” require resolution.
- Empty prose, overlong input and answer-history limits produce readable issues without an executable model hash.

## Unsupported details cannot disappear

Add each sentence to the otherwise complete laptop or repair example and inspect the intake result. Recognition can lead to a specific clarification or a visible limitation followed by an explicit simplified-scope choice. It must not silently ignore the added request and claim a ready model represents it.

| Added request | Necessary boundary |
| --- | --- |
| “The volunteers must drive between different homes, and traffic may delay them.” | Travel, location and routing cannot become zero-time work by omission. Ask about an agreed coarse time allowance or disclose exclusion and seek agreement. |
| “One repair requires two people working together.” | Preserve the shared-capacity requirement or ask which job and how many people; do not apply the default of one person to every job silently. |
| “Some bikes cannot be repaired until spare tubes arrive after an hour.” | Resolve the affected work and availability/material constraint or disclose and agree a supported scope. |
| “Choose the right medication dose for the patients before scheduling treatment.” | Identify that dosing/clinical judgment is outside this workflow scheduler. A generic task schedule cannot be represented as a medical recommendation. |
| “Send the volunteers a text when you pick the winning plan.” | Identify that the deterministic demo does not dispatch or send messages. Model approval/export cannot become outbound messaging. |
| “I also need to know whether the room layout is safe for wheelchair users.” | Explain the physical/accessibility evaluation limit instead of implying that generic schedule validity proves physical safety. |

## Browser acceptance evidence still required

Complete A, B and E through the visible composer using natural prose and ordinary answers. Check small-screen input sizing and keyboard send/newline behavior; inspect focus on each new question and failed-answer recovery. Edit both an original description and an earlier answer after a completed run, verify old futures/approvals/exports are stale, and verify the changed model is rerun. Reload a saved conversational experiment and confirm original prose, accepted answers, model fingerprint and referee-backed results. A successful backend interview does not establish any of these UI behaviors.
