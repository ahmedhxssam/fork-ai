# Conversational intake release verification

Local verification completed November 14, 2026. Base source: `94f1824`. Environment: macOS arm64, Python3.13.12, Node24.18.0, existing dependency locks and the project's official Playwright Chromium. Runtime remains deterministic, local and credential-free.

## Delivered user flow

The default input is a person's issue description, not compiler declarations or instructions. Examples cover missing details, conflicting staffing/time claims and an IT work queue. FORK shows understood facts and asks one targeted question at a time. Users answer with plain phrases or choices, edit their original issue or earlier answers, review a plain-language model and then run the existing verified simulation.

Conflicts are quoted and resolved explicitly. Required facts are not invented; uncertain/unavailable/required staffing remains unconfirmed. Ambiguous times and incompatible units prompt correction. Unknown qualifications remain visible for explicit scope agreement. A declined scope choice returns directly to the original editor with its text preserved and focused. Advanced schema/JSON stays optional.

Versioned drafts preserve earlier structured drafts, unfinished interviews replay their question history, and legacy experiments display readable summaries while retaining original source. Edits and replay fingerprint changes stale-gate old outcomes, approval and exports. Pending answer controls cannot discard text typed into an outgoing request. The API independently replays source/answers before launch and again before approved export; applied outage schedules stay separate from original authoring provenance.

## Fresh final checks

| Check | Actual outcome |
| --- | --- |
| `make test` | 252 Python tests, 4 frontend model tests, TypeScript and Vite build passed |
| Final UI scope-revision build | Passed; `index-fVQZ_Z_u.js`, Studio CSS `index-qXEY-3ZL.css` |
| Full production-browser suite | 36 passed in46.8s,14 logistics+22 Studio/conversation |
| Independent intake/API/acceptance review | 70 passed; no unresolved confirmed findings after fixes |
| Independent final scope-revision Chrome review | 1 passed against production8000 |
| Native in-app browser | Ordinary input, quoted2vs3staff and60vs90window conflicts, selected3/90 model, real6/6 results, new empty scenario, mobile follow-up |
| Native390px layout | Input16px; document width390px, no horizontal overflow; temporary viewport reset |
| Current recording |58.360s,1440×1000,VP8,25fps,noaudio; fullffmpegdecode and12sampleframes inspected |
| Actual downloaded evidence | Replayed natural authoring+model hash, exact independent receipt, current approval/revision,13CSVsegments checked |
| `git diff --check` | Passed before local commit |

Four existing Python dependency deprecations remain (Starlette/httpx and OR-Tools SWIG metadata). Browser output contains a terminal color warning. No failing final checks remain. Initial dependency/browser installation requires network access; a fresh three-domain conversational journey, two outages and downloads were exercised with external origins blocked, with no external requests.

## Findings corrected

Independent acceptance and final review exposed false resource/job counts, lost partial clauses, unavailable/required staff misclassified as available, compound times truncated, deadlines bound to the wrong group, alternative windows silently selected, unsupported units relabeled, and leading/trailing qualifications omitted. These were reproduced, corrected with behavioral regressions and independently retested. See `CONVERSATION_FINAL_REVIEW.md` and `CONVERSATION_ENGINE_REPORT.md` for exact cases and scope.

UI fixes cover pending-answer text loss, in-flight original edits, unfinished interview restoration, old-source migration, changed authoring fingerprints and explicit scope-change navigation. The first full browser run also had three assertions using an obsolete duration-question phrase after copy was improved; semantic assertions were corrected and the whole suite rerun successfully. One early command used a doubled frontend-relative test path; it ran no tests and was corrected before the observed scope-navigation RED→GREEN.

## Actual current media and evidence

- `docs/assets/conversation-01-prompt.png`: ordinary incomplete issue in the input.
- `conversation-02-conflict.png`: quoted contradictory staff counts, focused question and clear choices.
- `conversation-03-mobile.png`:390px natural issue and missing-count follow-up, inspected natively.
- `conversation-04-review.png`, `conversation-05-futures.png`, `conversation-06-receipt.png`: actual browser model review, schedules and independent evidence.
- `artifacts/conversation-approved.json` and `.csv`: actual approved natural-scenario downloads under two outages.
- `artifacts/conversation-domain-evidence.json`: real distinct conversational models/results from the three-example journey.
- `artifacts/FORK-conversation-demo-silent.webm`: genuine current-interface walkthrough; provenance and reproduction script in `CONVERSATION_RECORDING_REPORT.md`.

Earlier Studio/logistics images and downloads regenerated by regression runs were restored to their previously reviewed bytes. Current evidence is saved under separate names. Older videos and their source-version reports remain historical artifacts.

## Limits

The interview is bounded deterministic phrase recognition plus clarification, not a live language model or universal natural-language understanding. Its agreed simplified scope uses checkpointable work, one resource unit per job, equal importance, available-at-start jobs and explicit group ordering. Costs/materials/travel and arbitrary physical/clinical behavior are not inferred; excluded operative details require scope agreement. The richer existing typed engine remains available behind validated advanced inputs.

Independent receipts establish modeled consistency, not optimality, real-world truth or safety. Examples are synthetic. Supported hosting remains one localhost backend process; no new clean-machine install, formal accessibility certification, all-browser validation, public push, hosted deployment or competition submission is claimed. OpenAI setup remains deferred by user choice. The future adapter must use the same typed proposal, clarification, review and independent evidence gates.
