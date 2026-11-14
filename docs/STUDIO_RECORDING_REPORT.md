# Scenario Studio recording evidence

Recorded 2026-11-14T05:18:53.734Z from `http://127.0.0.1:8000` with the repository's Playwright Chromium.

- Video: [FORK-studio-demo-silent.webm](../artifacts/FORK-studio-demo-silent.webm)
- Duration: **46.520 seconds**.
- Size: **5,363,093 bytes**.
- Frame: **1440 × 1000**, vp8, 25/1 fps.
- Audio streams: **0**. This is the requested silent visual walkthrough, not a narrated two-minute pitch. Use [PITCH.md](PITCH.md) for the longer spoken presentation.
- SHA256: `e6a04bd8790bbde6f416bfac11b695f44b3949aae9f279a43eb7890a2a5b9658`.

## Recorded journey

- 0.56s: Prefilled repair-clinic brief.
- 4.62s: Compiled resources and dependency map.
- 9.00s: Explicit defaults and checkpointable-work assumption.
- 11.95s: Three real repair-clinic futures.
- 18.48s: A real resource outage draft: starts 5m, lasts 25m, capacity lost 1.
- 21.78s: Rerun: common outage, actual metrics and locked-replay comparison.
- 26.85s: Switched to the IT service response brief.
- 29.45s: Compiled a distinct IT response model.
- 32.77s: Three actual IT response futures.
- 36.76s: Independent replay receipt and evidence hashes.
- 41.54s: Approved the selected current-revision future.
- 43.16s: Downloaded and checked the actual approved JSON.

The script uses visible application controls and native scrolling. It records actual server results, with no response fixtures, substituted metrics, fake overlays, title cards, speed changes or edited cuts. Browser storage starts empty. The temporary JSON download was checked against its approval revision, model hash and independent evidence hash, then removed during cleanup. It is not a separate permanent deliverable.

## Actual computed outcomes in this take

| Run | Future | On time | Completed | Cost (integer cents) |
| --- | --- | --- | --- | --- |
| Community repair clinic (revision 1) | Throughput | 5/7 | 7 | 226 |
| Community repair clinic (revision 1) | Resilience | 7/7 | 7 | 226 |
| Community repair clinic (revision 1) | Priority | 5/7 | 7 | 226 |
| Community repair clinic (revision 2) | Throughput | 5/7 | 7 | 226 |
| Community repair clinic (revision 2) | Resilience | 3/7 | 7 | 226 |
| Community repair clinic (revision 2) | Priority | 3/7 | 7 | 226 |
| IT service response (revision 1) | Throughput | 5/6 | 6 | 672 |
| IT service response (revision 1) | Resilience | 5/6 | 6 | 672 |
| IT service response (revision 1) | Priority | 5/6 | 6 | 672 |

Outage applied to the repair clinic's first resource pool: start 5m, duration 25m, capacity lost 1. The IT response run is a fresh model and does not inherit that clinic outage. All three futures in each recorded run passed their returned independent verification. No preferred winner or positive recovery gain is required by the script.

## Verification and limits

- Playwright asserted three nonempty verified schedules in each original run and verified the shocked run. It checked that the IT response model differs from the clinic model.
- Playwright checked the downloaded JSON's approval revision, model hash and selected-world evidence hash.
- No external-origin browser requests were allowed or observed; no page errors were observed.
- `ffprobe` confirmed duration, dimensions, codec and absence of audio. `ffmpeg -v error -i VIDEO -f null -` decoded the complete file successfully.
- The recording is evidence of this localhost browser journey and synthetic deterministic computation. It does not establish deployment, competition submission, organizer eligibility, field performance, arbitrary-language understanding or a runtime model-provider integration.
- Visually inspected 11 extracted native-resolution frames at 3, 6, 9.5, 13, 17, 20, 24, 30, 34, 39 and 45 seconds. They show the brief, compiled blueprint, explicit assumptions, actual partial playback, complete futures, outage edit, shocked results, changed domain, receipt and approved export controls. Main labels and results are legible at the native frame size; compact task labels remain deliberately truncated by the product. Sample inspection is not a claim that every frame was reviewed.

## Reproduce

Serve the current frontend and API on `http://127.0.0.1:8000`, then run `node frontend/scripts/record-studio.mjs` from the repository root. The script uses existing local dependencies and browser binaries, finalizes video only after its assertions and complete decode succeed, closes the browser in `finally`, and removes temporary recording/download files. It creates new stored experiments through normal UI actions and does not erase existing experiments.

## Recorder execution notes

The first startup used the global browser cache because Playwright had already been imported; the script now sets the repository cache before dynamically importing Playwright. A sandboxed launch then hit the macOS Mach-port restriction; the authorized browser run succeeded outside that sandbox. One complete take passed the UI and download assertions but was discarded because Chromium was closed before Playwright saved the video. The final take saves the finalized video while Chromium is still available and passed all assertions plus complete decode. No product source changed during these recorder corrections.
