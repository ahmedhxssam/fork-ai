# Conversational Studio UI report

Task 3 replaces default structured authoring with a human prose issue, natural example chips and a bounded local clarification interview. No model provider, generative typing animation, credential or outbound integration was added.

The conversation displays one focused question, quoted conflicting claims, visible simplified-scope details and optional explanation. Answers use chips or ordinary text; Enter submits and Shift+Enter creates a newline. The outgoing question is disabled while its real request is pending. Validation preserves a rejected answer. New questions receive keyboard focus and scroll only when their controls would otherwise be outside the viewport, respecting reduced motion.

The model review uses people/work labels, work durations and deadlines, readable assumptions and separate excluded statements. Technical assumptions, source targets and JSON remain under advanced disclosure. The simplified natural models show equal job importance and costs as not modeled, with the unused cost/priority preferences disabled; existing legacy model controls remain available. Running requires an explicit model-review checkbox and sends the exact accepted answers and brief digest alongside the model fingerprint.

Editing the issue clears dependent answers and readiness. Editing an earlier answer retains that answer for revision, truncates later answers, and requires subsequent scope confirmation. Existing results remain visible as earlier evidence, with approval/export paused. An epoch guard prevents a late intake response from reviving changed authoring. A resumed natural model is compared with the original authoring fingerprint rather than an outage-adjusted run fingerprint; a changed or unavailable replay pauses approval/export.

Drafts use `fork-studio-conversation-draft-v1`, including accepted history, transcript and pending answer. The previous `fork-studio-draft` key remains untouched. Unfinished interviews replay on reload. Resume restores natural authoring while preserving outage/preference drafts; transient errors preserve the saved pointer. Legacy experiments use the readable server description in the conversation and keep the original source in the saved record and an advanced disclosure.

## Verification evidence

- Test-first initial browser run failed on the absent “Incomplete details” chip before UI implementation. The default Playwright binary was unavailable; the installed Chrome channel runs successfully with the local browser sandbox escalation.
- The unfinished-interview reload regression failed because no next question was reconstructed; stateless replay on mount fixed it.
- The resumed fingerprint-drift regression failed with an existing Export JSON link still visible; comparison with `authoring.model_hash` now stale-gates the evidence.
- A browser invalid-answer test exposed backend acceptance of “not a number” as one through the token “a”. The engine owner fixed number-answer handling; the browser test now passes.
- Existing Studio reliability tests were adapted to complete the intake rather than bypassing it. They retain lost-response idempotency, uncertain preference writes, draft preservation, delayed examples, approval selection and export coverage.
- Full Studio run before the final fingerprint regression: 18/18 browser tests passed. Extended natural-authoring run, including changed conflict answers producing different verified outcomes and legacy-source preservation: 7/7 passed.
- `npm --prefix frontend run typecheck`: passed.
- `npm --prefix frontend run test:model`: 4/4 passed.
- `npm --prefix frontend run build`: passed.

Final combined Studio browser run is recorded below after completion. Root owns the full repository regression, production/native visual inspection and presentation recording. Browser proof tests regenerate the existing local screenshots, download artifacts and domain evidence; those files were not individually visually inspected by this worker. No publishing, external dispatch or competition submission occurred.

## Final task-3 results

- Combined Studio command `FORK_BROWSER_CHANNEL=chrome npm --prefix frontend exec playwright test -- --config frontend/playwright.config.ts studio-conversation.spec.ts studio.spec.ts studio-proof.spec.ts --workers=1 --timeout=45000`: **21/21 passed (45.5 seconds)**, including the new fingerprint and pending-answer regressions.
- Final legacy-draft-marker regression was then observed failing after a second reload. The draft now persists its legacy marker and skips automatic natural replay for a legacy description. The complete conversational file was rerun: **9/9 passed (12.8 seconds)**.
- Final typecheck and production build passed after that marker fix. The preceding model tests remained 4/4; the marker does not touch comparison logic.
- Independent review worker reported an actual Chrome recheck: pending answer disabled, next answer enabled, submitted value retained; 390px input font 16px and no horizontal overflow.

Source is frozen for root integration. No commits were created by this worker. No checks are claimed beyond the commands and independent observations above.
