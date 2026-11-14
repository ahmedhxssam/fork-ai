# Independent conversational intake review

Review date: 2026-11-14. Base: `94f1824`. The reviewed working tree was changing while owners completed fixes; status below distinguishes observed failures from retested fixes. No production code was changed by this reviewer.

## Final verdict

**No unresolved confirmed findings in the reviewed scope after fixes and independent retest.** All six findings below, including the subsequent close variants, were addressed by the implementation owners. Independently executed final intake/API/acceptance suite: **70 passed**. Actual Chrome independently confirmed the pending-answer fix and readable 390px mobile input without horizontal overflow.

This is a bounded implementation review, not a claim of universal natural-language understanding. The broader browser suite, build and unchanged-engine checks remain separately reported by their owners. Historical reproductions below are retained so the fixes and regression intent remain inspectable.

## Verdict at first adversarial pass

Request changes for false extracted facts and lost material qualifications. The deterministic interview/replay architecture and API evidence boundaries are appropriate, but ordinary prose must be rejected or clarified when extraction cannot preserve its meaning. Generic scope acceptance is not a substitute for showing a material exclusion.

## Confirmed findings

### R1 — P1: Unavailable or required staff becomes available capacity

Initial locations: `backend/studio/intake.py`, `Interview.extract`, staffing claim extraction (approximately lines 160–172).

Reproduction: `Two technicians are unavailable. Six repairs take twenty minutes each. We have two hours.`

Observed: next question is scope confirmation; known facts include `staff-1 = 2 people / units`. Answering `accept` returns `ready=true` with capacity 2 and `excluded_details=[]`. Replacing the first sentence with `We need two technicians.` has the same result. These statements do not establish available capacity. Require confirmation instead of reporting available staff.

### R2 — P1: Compound job duration is truncated

Initial locations: `Interview.extract`, work duration extraction (approximately lines 191–202).

Reproduction: `Two volunteers are available. Six repairs take one hour and thirty minutes each. We have two hours.`

Observed: immediate scope question; duration fact is `60 minutes`, not 90; no quoted excluded detail. This changes the actual executable task duration. The compound-time guard existed for horizon, but did not protect job durations. Ask for a single duration or parse the complete amount.

### R3 — P1: One group's deadline is assigned to another

Initial locations: `Interview.extract`, deadline matching (approximately lines 225–236).

Reproduction: `Two volunteers are available. Two inspections take ten minutes each. Six repairs take twenty minutes each. Repairs are due within 30 minutes, inspections are due within 60 minutes. We have two hours.`

Observed: both `due-1` and `due-2` become 30 minutes. The second deadline should be 60. The loop searches each mentioned group's entire sentence for the first deadline. Bind each time to its actual group, or ask instead.

### R4 — P1: Alternative windows and conditional work can disappear

Initial locations: `Interview.extract`, horizon matching and sentence-level `recognized`/`unmodeled` handling.

Reproductions using otherwise complete staffing/work/window details:

- `We have two hours or three hours to finish.` becomes a definite 120-minute horizon, followed by a scope question with empty evidence.
- `Six repairs take twenty minutes each unless they need inspection.` becomes unconditional 20-minute jobs, followed by scope confirmation with empty evidence.
- `Six repairs take twenty minutes each, provided inspections finish first.` likewise loses the stated prerequisite without quoting it as excluded.

A sentence-level recognized flag can hide unmatched material spans. Alternative essential values need clarification. Unmodeled qualifications must be visibly quoted for scope acceptance.

### R5 — P2: Numeric answers ignore incompatible units

Initial locations: `Interview.apply`, numeric answer extraction (approximately lines 336–350).

Reproduction brief: `Two volunteers are available. Six repairs are waiting. We have two hours.` At the missing duration question, answer `twenty seconds`.

Observed: accepted answer history contains the exact seconds answer, while known duration becomes `20 minutes`. Answer `20 bikes` is also accepted as 20 minutes. Reject explicitly incompatible units rather than relabeling them; a bare number remains valid because the question supplies the unit.

### R6 — P2: Editing an answer during its request silently loses the edit

Initial locations: `frontend/src/studio/Conversation.tsx` answer textarea; `Studio.tsx` `interview` response handler and `onAnswer`.

Actual Chrome reproduction with response interception:

1. Submit the R5 brief and reach the duration question.
2. Delay `/api/studio/intake` response after sending `20`.
3. The textarea remains enabled; replace its text with `30` while request is pending.
4. Release the response.

Observed console: `while_pending 30`, `after_response [empty]`; transcript records `20`. The late response erases the newer draft. Disable answer editing during submission, or preserve/cancel pending response effects when the draft changes. This is separate from the already implemented original-brief epoch guard.

## Positive findings and checks executed

- Read the complete conversational intake spec, intake implementation, changed API, UI conversation/state code, types, relevant styles and test coverage.
- Independently ran `.venv/bin/python -m pytest tests/test_studio_intake_api.py tests/test_conversation_acceptance.py -q`: **21 passed** (one pre-existing Starlette/httpx deprecation warning). This is the exact subset executed here, not a claim about the entire suite.
- API launch recomputes intake and checks ready state, original brief hash, validated model/hash, and exact model equality before simulation. Saved authoring preserves original answers and source; approval/export independently replay source and allow only current experiment outages to differ.
- Existing event and preference mutations preserve authoring. The executed API checks cover original authoring vs applied outage model, source retention, tampering, malformed saved provenance and export replay.
- Replay IDs bind both brief digest and accepted prefix. Invalid answer application uses a copied candidate, preserving accepted state. API and intake bound brief length, answer count and answer length; schema validation bounds the eventual model. No generated code or provider is executed.
- UI has three natural prose starters, a single follow-up, explicit scope review and separate model consent. Original brief/prior answer edits clear readiness and stale-gate results. The versioned draft key leaves legacy drafts intact; legacy display prose preserves original stored source.
- Actual Chrome rendered and visually inspected desktop 1440×1000 and mobile 390×844 screenshots at `/tmp/conversation-review-desktop.png` and `/tmp/conversation-review-mobile.png`. Scope question, evidence cards and primary action fit without visible horizontal overflow. Mobile input text was visibly readable. Screenshots are review-time evidence, not a complete browser regression claim.
- A small prose defect was visible: `Six repairs are waiting` yields label `repairs are`, producing `Time per repairs are job`. This is lower severity than incorrect facts and should be cleaned up when feasible.

## Evidence limits

Engine/referee unchanged verification and broad browser regression were assigned to the root/other owner; not independently rerun in this initial pass. Runtime remains an explicitly bounded deterministic parser, not universal NLP or a connected AI provider. No publication, competition eligibility or submission claim is made.

## Fix retest status

Independent retest after the first owner fixes:

- **R1 original reproductions resolved:** unavailable/required staffing now yields a staffing clarification with no confirmed capacity fact.
- **R2 original reproduction resolved:** combined work-duration sentence asks for a total rather than confirming 60 minutes. A follow-up review found the same pattern still unguarded in separate `Each repair takes…` and deadline branches; sent back for consistent handling before final verdict.
- **R3 resolved:** inspections due 60 and repairs due 30 are preserved in their own model tasks.
- **R4 original reproductions resolved:** alternative windows produce a conflict question; `unless`/`provided` constraints remain quoted. A close variant, `We have two hours left, including lunch`, now exposes `left, including lunch` at scope review. Unrecognized trailing prose is retained structurally rather than only through a keyword list.
- **R5 resolved:** `twenty seconds` and `20 bikes` are rejected with the accepted prefix unchanged.
- **R6 resolved in actual Chrome:** input disabled while pending, enabled for the next question. Mobile computed input font 16px; document horizontal overflow false. Updated screenshot: `/tmp/conversation-review-mobile-fixed.png`.
- Queue label cleanup also verified: `Six repairs are waiting` now uses `repairs`, without the stray `are`.
- Independently reran `.venv/bin/python -m pytest tests/test_studio_intake.py tests/test_studio_intake_api.py tests/test_conversation_acceptance.py -q`: **61 passed**, one Starlette/httpx deprecation warning.
- Reviewed the added UI replay gate: saved natural experiments remain stale unless a ready replay's model hash matches the saved **original authoring** model hash; outage-adjusted run hashes remain separate.

Second independent retest: **65 targeted tests passed**. Separate-duration and deadline compound-time variants now request clarification without asserting a truncated time. `Two technicians are sick` now requests capacity confirmation rather than claiming availability.

Two close variants of existing findings were then sent for final correction:

- R4: a leading qualifier (`If the manager approves, six repairs take twenty minutes each`; also `Subject to inspections finishing` and `After safety approval`) was still omitted because residual tracking only preserved tails.
- R5: inverse unit mismatch remained: staffing answer `two hours` became 2 people; job-count answer `six minutes` became 6 jobs. Explicit time units must be rejected for counts too.

Final independent retest completed after the owner freeze:

- All three leading-condition variants now appear verbatim in scope evidence: `If the manager approves`, `Subject to inspections finishing`, `After safety approval`.
- Staffing answer `two hours` and job-count answer `six minutes` now return a helpful invalid-answer issue, retain the original next question and accept no answer.
- `.venv/bin/python -m pytest tests/test_studio_intake.py tests/test_studio_intake_api.py tests/test_conversation_acceptance.py -q`: **70 passed in 0.33s**, with the same single deprecation warning.
- The final suite includes every original parser finding and its added regression variants. The delayed-answer fix was independently exercised in actual Chrome, rather than inferred solely from source.

No unresolved confirmed finding remains from this review. No production or test files were edited by this reviewer; only this report was authored.

## Scoped follow-up: revise-scope action

Reviewed the post-review change limited to `Studio.tsx`, `Conversation.tsx` and its browser regression. **No actionable finding.** The `revise` choice on the current scope question now invokes the same `editOriginal()` action used by the original-issue Edit button. This advances the authoring epoch, cancels stale retries, clears dependent answers/model readiness/consent and preserves the original brief. It returns before sending a rejected answer to the intake API. The original textarea autofocus is limited to the editing state. Existing uncertain-write handling remains intact.

The updated duration-question assertions match the current readable copy; they do not change application behavior. The added scope regression checks a visible, focused, nonempty original editor, no remaining question or error and a disabled Run button.

Independently executed against the local production build at `http://127.0.0.1:8000` with actual Chrome:

`FORK_URL=http://127.0.0.1:8000 FORK_BROWSER_CHANNEL=chrome node frontend/node_modules/playwright/cli.js test --config frontend/playwright.config.ts --grep 'choosing to revise scope'`

Result: **1 passed (2.6s)**. An initial attempt at the retired Vite URL on port 5173 returned connection refused; it was retried at the root-provided production URL. This follow-up did not reopen the broader audit or claim the root's separate full-browser result.
