# Scenario Studio UI implementation and verification

Implemented Task 4 in `frontend/src/studio/`, selected by the default `main.tsx` entry. The unchanged logistics application remains at `?view=logistics`; existing logistics browser tests now navigate there explicitly.

## Implemented behavior

- Editorial light workbench with teal/violet/ochre computed futures, responsive single-column mobile layout, readable form typography, keyboard controls, visible deterministic mode and synthetic/no-dispatch scope.
- Prefilled repair brief and three examples loaded from the actual templates API. Empty new scenario, editable bounded brief, unsupported-line compiler issues, parsed facts-to-model targets, explicit defaults, resource/task/dependency review and copyable typed JSON.
- Launches the actual three-policy experiment API. Cards use independently recomputed referee metrics; work traces use returned actual work segments. Minute playback progressively reveals processing/completions rather than fabricated telemetry. Independent receipt checks and current experiment model/hash remain inspectable separately from the original compiled brief blueprint.
- Multiple editable resource outages, full counterfactual reruns, exact zero/negative recovery differences and no-outage controls; no optimality claim. Event and preference draft categories cannot both be edited concurrently, preventing successful saves from dropping unrelated drafts.
- Explicit preference saves, positive-weight validation, selected-future approval and revision-bound JSON/CSV exports. Brief/event/preference edits and uncertain failed writes disable approval/export. Choosing a different future after approval requires approving that selected future.
- Serialized mutations with stable idempotency keys on retry. Retry or saved-revision reload errors remain visible; a transient resume failure preserves the saved pointer. Draft brief/outages/preferences and experiment pointer survive reload; new scenario preserves prior experiment pointer/history rather than deleting it.

## Checks actually executed

- `npm --prefix frontend run typecheck`: passed.
- `npm --prefix frontend run build`: passed (TypeScript plus production Vite build).
- `npm --prefix frontend run test:model`: 4 passed.
- `FORK_BROWSER_CHANNEL=chrome npm --prefix frontend run test:e2e -- studio.spec.ts --workers 1 --timeout 30000`: 10 passed in 12.5 seconds, including selected-future reapproval and all three adversarial regressions.
- Browser coverage includes cross-domain compilation, invalidation/blocking, a horizon-length capacity outage changing actual segments, verified rerun receipts, approval and actual JSON download, saved draft restore, transient-resume pointer retention, empty reset, phone document width, keyboard timeline, multiple drafts, stable lost-response retry, compile uncertainty, and delayed template protection.
- Initial browser attempts before implementation were blocked first by unavailable bundled Chromium, then Chrome sandbox launch, then absent Vite5173. These were environment failures, not observed UI red results. Tests subsequently ran in installed Chrome with approved local process access.

## Adversarial findings and fixes

The independent reviewer reproduced three defects in the first implementation:

1. A response lost after successful event commit, followed by editing the retained draft and retrying an old closure, could discard the newer draft. Any user draft edit now cancels that closure; saved-state reload remains explicit.
2. Successful compilation could clear saved-state uncertainty despite an unacknowledged preference revision. Only accepting a full experiment snapshot now reconciles that uncertainty; compilation cannot enable approval.
3. Delayed initial templates could replace text typed before the response. The new browser test failed with the custom draft replaced by the repair example, then passed after updating the initial draft guard synchronously with typing.

Regression browser tests cover all three. Independent reviewer also reran its own reproductions successfully and documented the review in `docs/STUDIO_FINAL_REVIEW.md`.

## Limits and remaining boundaries

This UI consumes the bounded deterministic compiler; it does not implement arbitrary natural-language interpretation, LLM activity, provider calls, external dispatch or real systems access. Simulation and approval/export are local modeled outcomes. The UI does not archive every experiment revision; each counterfactual updates the latest saved snapshot of that experiment. Previous experiment IDs are retained by storage. Browser localStorage may be unavailable in restrictive browser contexts; network errors preserve in-memory drafts, but durable browser recovery then cannot be guaranteed. Final production screenshots and the complete old/new regression suite are integration-owner checks and should be reported from their actual outcomes.
