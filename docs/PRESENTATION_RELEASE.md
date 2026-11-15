# FORK guided presentation release

November 15, 2026. This report records the local source, application, evidence and media checks before publication. The repository is a submission pack. During this release, the existing [FORK.ai Devpost entry](https://devpost.com/software/fork-ai-pmeja0) was observed in Dia as **SUBMITTED — 5/5 steps done** before agent edits. Updating that existing entry is separately authorized; no hosted application is claimed.

## What is delivered

A shared minimal identity now spans Scenario Studio, the food-bank lab, the judging guide and the film: warm paper, ink, restrained greens, the same original fork mark, calm editorial type and the line **Rehearse before you commit.** [Brand guide](BRAND.md)

[Judging mode](JUDGING_MODE.md) guides eight chapters through real seed-26 computation: mission, three plans, conventional controls, common failure, paired recovery, priorities, independent receipt and explicit human approval. The guide has Back/Next, Restart, Exit, keyboard arrows/Escape, a pauseable timer and 180/120-second pacing. Navigation is manual; the time budget does not force a step or decision. A restart creates a fresh experiment when the presenter continues; saved experiment pointers and database history are preserved. Back does not apply another breakdown. Evidence tabs remain usable.

The ordinary workspace remains available. A tutorial button starts the guide from either workspace. The opening guide uses its own Next action rather than showing a second disabled launch button. The guide's final step never automatically approves or dispatches anything.

## Executed application checks

- `make test`: **252 Python tests**, **4 frontend model tests**, TypeScript and production Vite build passed. Four existing third-party deprecation warnings remain.
- Final complete browser suite: **44/44 passed** (reported 1.0 minute), using Node 24.18.0 and the installed official Playwright Chromium against localhost 8767 with a separate temporary SQLite database.
- Six added guide cases cover real launch/shock/approval, saved-pointer preservation, Back without duplicate failure, launch/disruption errors and retry, restart, keyboard controls, pause across inspector remount, mobile approval, tablet target geometry and deferred stylesheet loading.
- An initial full browser run exposed four narrow-layout failures. Actual overflowing header controls were measured; responsive layout was corrected without document clipping. The final complete run passed. Focused Chrome checks also passed the four previously failing cases.
- Independent review reproduced and resolved a missing receipt highlight on Back, a collapsed tablet spotlight and inspector tabs that appeared enabled but were inert. Its final targeted recheck reported no open P0–P2 findings. This is finite review, not a guarantee of absence of defects.
- Desktop 1440px, mobile 390px and tablet 1024px guide captures were opened and inspected. Their document widths equal their viewports. At tablet size the guide has an internal scrollbar; a 25px panel scroll exposes Restart fully, and that action was tested.
- The native in-app browser separately exercised the desktop guide through actual shared failure, receipt and human approval. Its attempted viewport override did not change the native viewport; mobile/tablet evidence comes from actual automated Chrome/Chromium viewports and saved screenshots.
- Historical version-specific screenshots and exports were backed up before tests and restored afterward. New evidence has distinct `presentation/` and `FORK-submission-*` names. User-saved data was not deleted.

These checks establish observed behavior inside the declared synthetic model. They do not establish real-world impact, operational safety, optimality, exhaustive accessibility, a clean-machine installation or event eligibility.

## Video and provenance

The measured final film is **115.021333 seconds** (1:55), **1920×1080**, **30 fps / 3,450 frames**, H.264/yuv420p with 48kHz AAC audio. File size: **14,121,445 bytes**. SHA-256: `ddb9b8d1767da14e0cc78ec64a2474cb68ee309f51b13e9a5f5342ee4750da49`.

Full-stream decoding passed. All eight chapter frames, opening, logo close and ending were inspected; the root reviewer separately opened all eight chapters and the outro, then checked the color-corrected proof and contact sheet. Audio measured −16.2 dB mean / −1.4 dB peak; no human listening check is claimed. Captions were checked against the exact narration text. The retained raw browser take is 2880×1600 VP8 at 25 fps and 14,593,579 bytes; the CSS viewport remained 1440×800.

The media pipeline corrects the browser capture's YUV/RGB conversion and explicitly encodes BT.709. Neutral paper patches are within three RGB levels of the intended palette. This is documented color-format calibration; UI layout, labels, computed outcomes and actions are unchanged. The actual application, served index and `/assets/fork-mark.svg` also returned HTTP 200 from the user's running localhost 8000 server; index and icon bytes matched the final build.

The film uses the actual browser workflow with a separate numbered editorial margin, titles, a short numbered list per chapter, exact-word captions and offline macOS Samantha narration. The voice is a system voice, not the owner's voice. The last three seconds are a restrained fade/settle of the original FORK logo, then logo alone. No external voice, music or model service was used.

The final recorded run confirms greedy **224** versus initial named policies **216 / 192 / 216**. With vehicle A failing at 09:25, all adapted policies deliver **168**; same-shock fixed plans deliver **144 / 120 / 144**. The gains **+24 / +48 / +24** refer to different fixed-plan controls and do not make Resilience the best final meal total. All recorded adaptive and fixed-plan receipts are valid. A preference write advances the experiment from revision 2 to revision 3; the actual approved JSON and CSV belong to revision 3. The JSON explicitly has `synthetic=true` and `external_dispatch=false`.

Recording assertions initially used an incorrect baseline vector and a stale pre-preference revision. They were corrected against actual API outputs before the final take. Failed takes were not used as evidence. The final recorder required successful real actions, zero page errors and zero external browser requests.

[MP4](../artifacts/FORK-submission-demo.mp4) · [captions](../artifacts/FORK-submission-demo.srt) · [transcript](../artifacts/FORK-submission-demo-transcript.txt) · [storyboard](../artifacts/FORK-submission-demo-storyboard.json) · [run/encoding evidence](../artifacts/FORK-submission-demo-evidence.json) · [raw source take](../artifacts/FORK-submission-source.webm) · [approved JSON](../artifacts/FORK-submission-approved.json) · [CSV](../artifacts/FORK-submission-approved.csv).

The reproducible local pipeline and downloaded skill provenance are in [scripts/media](../scripts/media/README.md). The user-requested product-demo topic was consulted; MIT-licensed Product Demo Director guidance was downloaded at its pinned commit and reviewed. Its remote scripts, dependencies and API integrations were not run. No implementation code was copied. OpenAI Codex substantially assisted this build and media production; the application runtime remains deterministic.

## Present and submit

Use [the three-minute guide](http://127.0.0.1:8000/?view=logistics&tour=1) to learn and rehearse. Use [the two-minute pace](http://127.0.0.1:8000/?view=logistics&tour=1&pace=120) and the shorter spoken script with judges. The supplied packet caps both the optional submitted video and mandatory in-person presentation at two minutes.

Choose **Business and Enterprise** as the single main track. Best Overall consideration is automatic upon submission; the supplied packet associates its PS5 prize with that award. Current FORK implements no sponsor integration that establishes a special-track entry. Source citations, entry text, timing and remaining owner actions are indexed in [SUBMISSION_READY.md](../SUBMISSION_READY.md).

The existing Devpost submission is preserved. After source publication, its name, tagline, thumbnail, story and gallery were updated in Dia. The public page was checked, and the management interface still showed **SUBMITTED — 5/5 steps done**. The same submission ID and public URL remain; no project or gallery image was deleted. See [publication evidence](PUBLICATION.md). A compatible hosted-video embed, participant facts and organizer eligibility remain distinct from repository publication. The final handoff must report the observed Devpost status rather than infer it from GitHub.
