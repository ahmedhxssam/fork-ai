# FORK frontend implementation

## Scope

React 19.2 / TypeScript 5.9 / Vite 7.2 single-page workspace. All implementation lives in `frontend/`; API and shared configuration remain owned by integration. Exact dependency versions and npm lockfile are included. There are no remote fonts, imagery, map tiles, analytics, or runtime network dependencies beyond the same-origin `/api`.

## Product

- Original dark, typographic mission briefing with the actual scenario's stock, fleet, destinations, and SVG road network.
- Three synchronized worlds with actual route traces, interpolated vehicle positions, completed destination states, meal counts, and stock custody projected from persisted events.
- Common playback clock, run/pause, timeline, speed, and initial/accepted/shock/outcome anchors. Before a breakdown, saved playback displays the unshocked original plan rather than revealing future recovery routes.
- Actual vehicle/time breakdown API call, explicit stranded-cargo semantics, pending planning state, and visible no-replanning counterfactual, recovery gain, and unshocked-reference deltas. A zero gain remains zero.
- Actual preference updates, fresh revision retrieval, backend recommendation, Pareto labels, and verified comparison metrics. Metric displays use independent verification receipts.
- Native modal route/driver/transfer/custody inspector, actual planner and manifest JSON, all referee checks/violations/hashes, and expandable individual event ledger values.
- Revision-bound simulated-plan approval and actual JSON/CSV artifact links. Preference changes refresh approval/revision state.
- Reset and persisted-experiment resume. A resumed run is visibly labeled Saved replay alongside the actual planning mode.
- Responsive focus-world tabs below 900 px; keyboard-accessible controls, native dialogs, focus styles, and reduced-motion support.

## Commands

```sh
npm ci --prefix frontend
npm --prefix frontend run dev
npm --prefix frontend run typecheck
npm --prefix frontend run build
npm --prefix frontend run test:e2e
```

Development proxies `/api` to `127.0.0.1:8000`. Backend integration can serve `frontend/dist` in production. The Playwright journey uses a real API; no metrics or fixtures are mocked. Set `FORK_URL` to change its base URL. `FORK_BROWSER_CHANNEL=chrome` uses an installed Google Chrome instead of downloading Playwright Chromium.

## Verification at handoff

- TypeScript typecheck: passed.
- Production build: passed; 31 transformed modules, approximately 227 kB JS / 71 kB gzip and 35 kB CSS / 8 kB gzip.
- Journey test was authored before application source. Its first attempted execution could not launch default Chromium because the browser binary is absent. A subsequent installed-Chrome attempt aborted under filesystem/process sandbox restrictions. Neither attempt exercised application behavior, so no browser pass is claimed here.
- Vite development listen was denied by sandbox (`EPERM 127.0.0.1:5173`); integration root owns escalated server/browser QA and screenshot inspection.

## Known limits

This is synchronized playback of computed event histories, not live vehicle telemetry. Only the scenario and disruption capabilities exposed by the API are implemented: one common breakdown per experiment, no roadside transfer/rescue. Route inspection distinguishes initial routes from actual executed transfers; the full accepted recovery plans remain inspectable in persisted events and planner evidence. No external dispatch or communication occurs.

## Final presentation diagnostics

- Added actual independently verified conventional controls (nearest-feasible greedy and neutral solver), including meals delivered, on-time meals against total demand, exact modeled cost, and physical validity. A control that beats every verified named world is explicitly called out; it is not hidden by the preference ranking.
- Added post-shock exposure evidence: configured initial reserve, stranded cargo from the exact selected breakdown event, and adaptive recovery minus the same-shock fixed-route control. The presentation explicitly states that these observations do not isolate causality.
- Corrected ranking copy and comparison table to on-time coverage. Preference ties display `Preference tie`. All-zero weights display an inline prompt and never issue an invalid API update.
- Four meaningful diagnostic regression tests were written first. Initial execution failed because the implementation module was missing; after implementation, all four pass. Tests cover a control beating named worlds, tie/no-eligible distinction, zero-weight validation, and exact event/vehicle extraction.
- Fresh final typecheck and production build pass (32 modules; 232.07 kB JS / 72.29 kB gzip; 39.58 kB CSS / 8.82 kB gzip).

Diagnostic tests require Node 24 (available in this workspace):

```sh
node --experimental-strip-types --test frontend/test/comparison-model.test.ts
```

## Review fixes R1 / R2 — acknowledged preferences and resumability

The previous preference implementation allowed independent POSTs and left approval/export actionable after failed or invalid local edits. It has been replaced by `src/usePreferences.ts`, a single writer that coalesces queued desired snapshots. A second POST starts only after the previous POST and its confirming GET finish. Desired slider values are distinct from acknowledged server preferences; approval and existing approved-export links are blocked while values are dirty, invalid, pending, failed, or different from the acknowledgment. Successful acknowledgment displays the server's normalized weights exactly (`step="any"` avoids native range quantization). A failed save offers explicit retry or a revert that first re-fetches server state, including the case where a successful POST response was lost.

The API helper now preserves HTTP status with `ApiError`. A transient resume network/5xx failure retains both the Resume control and localStorage experiment ID. Only a confirmed 404 or an explicit reset clears the saved pointer. A successful retry restores the saved experiment.

Positive unshocked-reference deltas now disclose the model's opportunity difference next to the result: initial plans have one trip; recovery permits one additional depot reload per healthy vehicle. The copy explicitly avoids interpreting breakdown itself as beneficial.

### Executed regression evidence

`e2e/reliability.spec.ts` exercises the real UI and backend. Fault injection occurs only at the browser fetch boundary; computed experiments and server revisions remain genuine.

Before implementation, the focused browser tests reproduced prior approved JSON export remaining visible after a failed POST, concurrent preference writes (two active requests under reversed network delays), and deletion of the Resume pointer after a 503. The corrected zero-weight assertion also reproduced the stale approved export. These were observed RED before rebuilding the fix.

After implementation, six focused tests pass:

1. Failed save hides prior exports, blocks approval, and can be retried.
2. All-zero priorities block a previously approved plan.
3. Delayed writes remain serialized, and latest server weights exactly match slider values.
4. Resume survives a transient 503 and succeeds on retry.
5. Revert re-fetches actual server values after a lost response to a committed POST.
6. Confirmed 404 clears the obsolete saved pointer.

Fresh verification against the final production build:

- Full Playwright suite: **13 passed in 4.5 seconds**, including real export downloads, A/B/C shocks, every external origin blocked, narrow-screen overflow, and all six reliability tests. Parent-owned `presentation.spec.ts` was not edited.
- Diagnostic model tests: **4 passed**.
- `npm --prefix frontend run typecheck`: passed.
- `npm --prefix frontend run build`: passed; 33 modules, 234.83 kB JS / 73.26 kB gzip; 40.31 kB CSS / 8.99 kB gzip.

```sh
cd frontend
PLAYWRIGHT_BROWSERS_PATH='../.cache/ms-playwright' FORK_URL=http://127.0.0.1:8000 npm run test:e2e
```

Browser execution required the authorized escalated local environment. Build first and keep `dist` stable while browser checks navigate between pages.

### Follow-up: delayed approval response

A further real-browser regression reproduced an approval response arriving after a newer preference acknowledgment. Before the fix, the displayed experiment rolled back from revision 2 to the older approved revision 1. The approval handler now uses a functional state update and attaches a decision only when its experiment ID and revision match the current state. It never replaces a newer experiment snapshot with a captured older one.

The new test commits approval on the real backend, delays only its browser response, closes the inspector, saves and acknowledges changed cost preferences, then releases the old response. It checks that revision 2 remains displayed, stale export links are absent, and current-revision approval remains available.

Observed RED before the code change; focused GREEN after it. Final full UI suite: **14 passed in 5.0 seconds**. Typecheck and production build pass (234.89 kB JS / 73.29 kB gzip). No presentation-test or browser-configuration changes were made.
