# Scenario Studio final independent review

Reviewed 2026-11-14 against the locked `docs/superpowers/specs/2026-11-13-scenario-studio.md`. Scope: whole-change specification compliance, React state and persisted drafts, lost-response recovery, approvals/exports, compiler claims, input boundaries, and retained logistics routing. Read the independent backend review and current compiler/schema/API implementation as well as the Studio UI, browser tests and source documentation. This reviewer made no production-source edits and no commits; the UI owner fixed the findings below.

## Verdict

**Specification compliance: PASS within the declared deterministic local workflow scope. Code quality/correctness: PASS after fixes. No unresolved actionable blocking findings.** Three P2 state/data-loss findings were independently reproduced, reported, fixed, and reverified. Backend review findings and their corrections are documented separately in `STUDIO_BACKEND_REVIEW.md`; the full Python suite was independently rerun here.

The compiler is a bounded documented grammar, the three policies are deterministic heuristics, and the schema is a future authoring boundary. Current product and source documentation preserve those distinctions, synthetic-input assumptions, real computed work, independent metrics, honest ties/zero gains, and the absence of live AI, real dispatch or optimality claims. The retained engine remains separate at `?view=logistics`.

## Resolved findings

### P2 — Retry discarded edits made after a lost successful response

Location: `frontend/src/studio/Studio.tsx`, `perform`, `accept`, and draft edit handlers (approximately lines 76–104).

Reproduction: launch a scenario, add a duration-20 outage; intercept its events POST with Playwright `await route.fetch(); await route.abort('failed')` so the server commits revision 2 while the browser sees failure. Change the retained outage draft to 35, then click Retry operation. Originally the cached response applied through `accept` replaced 35 with 20, silently losing the newer input.

Resolution: editing any draft invalidates the failed operation's retry closure. The newer value remains visible, approval remains blocked, and an explicit saved-revision reload remains available. An unchanged failed operation still retries with the original idempotency key. Independent rereview observed duration **35**, **zero** stale Retry buttons, and an explicit reload restoring committed revision 2/duration 20. Browser regressions cover both edited-draft preservation and unchanged-command idempotency.

### P2 — Compilation cleared unresolved server revision uncertainty

Location: `Studio.tsx`, `perform`/`accept` (approximately lines 76–85).

Reproduction: save a changed preference using the same commit-then-abort interception; move the slider back to its previous displayed value so ordinary draft equality is restored, then compile the unchanged brief. Originally any successful `perform` cleared `uncertain`; approval became enabled on browser revision 2 while the server was revision 3. The server's revision checks prevented a stale write, but the UI falsely treated its evidence as current.

Resolution: uncertainty clears when a full experiment is accepted, not when compilation succeeds. Independent rereview observed approval disabled both before and after compilation, with the deliberately unreconciled browser revision 2/server revision 3. The regression verifies explicit reload restores the current revision and enables approval only then.

### P2 — Initial template response overwrote a user's new brief

Location: `Studio.tsx`, `loadTemplates` and scenario textarea `onChange` (approximately lines 71 and 122).

Reproduction: delay `/api/studio/templates` behind a Promise gate on first load; type `Title: My custom brief` and a resource/task into the enabled editor; release the template response. Originally `initial.current` remained null and the default repair template replaced the entered text.

Resolution: typing synchronously marks the initial draft as user-owned before the asynchronous template initialization can run. The identical independent reproduction changed from **custom draft retained: false** to **true**. The retained browser test also passed.

## Checks actually executed

- `.venv/bin/python -m pytest -q`: **182 passed**, four dependency deprecation warnings, 2.65 seconds.
- `npm run build`: passed before and after the frontend corrections; TypeScript and Vite production build succeeded.
- `npm run test:model`: **4 passed**.
- `FORK_BROWSER_CHANNEL=chrome npx playwright test --workers=1`: **22 passed**, 21.8 seconds, at the suite snapshot containing 14 logistics tests and 8 Studio tests. This covered the actual logistics journey, evidence/downloads, vehicle choices, narrow layout, external-origin blocking, preference failures, serialization, resume and late responses, plus Studio state flows.
- After the late-template fix, `FORK_BROWSER_CHANNEL=chrome npx playwright test e2e/studio.spec.ts --workers=1`: **9 passed**, 10.8 seconds. This includes cross-domain compilation, unsupported prose, stale brief gates, actual outage execution changes, approval/export, resume after 503, empty new scenario, mobile keyboard/playback/width, event draft persistence, lost responses and all three findings.
- Additional independent temporary Chrome reproductions in `/tmp/studio-final-review.cjs`, `/tmp/studio-final-rereview.cjs`, and `/tmp/studio-template-race.cjs` exercised actual localhost requests, not mocked result payloads. Initial range-input `fill` attempts were corrected to real ArrowRight/ArrowLeft keyboard events; the final repros completed successfully. Browser launch required the authorized local sandbox escalation.
- Read-reviewed server strict model bounds, reference validation, digest/revision gates, idempotency payload matching, workflow/logistics ID separation, React's escaped text rendering, safe CSV task/resource identifiers, and data-only compiler semantics. These complement, rather than replace, the deeper backend adversarial review.
- Visually inspected the saved `studio-03-futures.png` desktop comparison and `studio-05-mobile.png` full-page capture. No layout blocker was visible. The mobile capture includes a focused skip-link overlay from keyboard testing; blur focus before using that particular screenshot as presentation media.

The existing full browser presentation suite regenerates `artifacts/approved-resilience.json` and six logistics PNGs in `docs/assets/`; the root was notified so those generated changes can be retained or reverted deliberately.

## Limits

This is finite review evidence, not an exhaustive proof. The UI uses a sizeable single React component and explicit state/ref gates; future asynchronous flows should keep adversarial browser coverage. Tests used local Chrome, one backend process, and the current local environment; they do not establish clean-machine installation, all browsers, multi-process concurrency, formal accessibility compliance, or offline Studio operation. The logistics external-origin-blocking test is specific to that retained flow. Screenshot inspection does not replace assistive-technology testing. No public deployment, push, competition eligibility ruling, real-world domain validation, or submission was performed by this review. The independent referee verifies declared modeled feasibility and metrics, not heuristic optimality or the truth of arbitrary input facts.
