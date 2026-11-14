# Silent automated walkthrough

Delivered [FORK-demo-silent.webm](../artifacts/FORK-demo-silent.webm): a genuine silent automated walkthrough of the running local application. This is **not** the two-minute human-narrated pitch or evidence of a live LLM integration.

## Actual artifact

| Property | Verified value |
| --- | --- |
| Duration | 37.080 seconds |
| Dimensions | 1440 × 960 |
| Container / codec | WebM / VP8 |
| File size | 3,230,843 bytes |
| Audio | No audio stream; intentionally silent |
| Experiment | `405e59812daf4931` |
| Breakdown | Vehicle B, elapsed 1,800 seconds (09:30) |
| Approved world | Equity, revision 3 |
| Browser page errors | Zero recorded |
| SHA-256 | `eb784d74e151df025851f6fba5bac884c24cf182b5207dadab26b3353a6f940d` |

## What was captured

The official installed Playwright Chromium recorded the actual production frontend and localhost API at `http://127.0.0.1:8000`. The fresh browser context began at the mission briefing, forked the three worlds, ran at 600× speed, paused, selected B at 30 minutes, and submitted a genuine common breakdown. The script checked the actual response and all three valid referee receipts.

It then ran nine seconds of 600× playback, selected verified outcomes, showed post-shock exposure, scrolled to the decision lens, raised the cost slider with the End key, inspected the decision and independent referee receipt, and approved the current simulated plan. Export links appear at the end; the video does not claim that an export was downloaded during recording.

The initial recommendation was Resilience. The settled cost-preference response visibly recommends Equity; a frame at 28 seconds shows “CURRENT RECOMMENDATION”, “Equity”, and “Preferences saved”. Equity's receipt and revision-3 approval are visible later. The recorder's immediate response metadata was sampled during “SAVING PRIORITIES”; visual frame inspection confirmed the settled response in the delivered video. The reusable script now explicitly waits for “CURRENT RECOMMENDATION” before sampling that metadata on future runs.

No API mocks, fabricated frames, overlays, edits, soundtrack or narration were added. Short intentional waits make actual UI states readable. The video was finalized after the recording page/context closed.

## Verification

- `node --check frontend/scripts/record-demo.mjs`: passed.
- Recording script completed with exit code 0 and wrote the actual artifact above.
- Trusted local `ffprobe` confirmed duration, dimensions, VP8 codec and absence of audio.
- Trusted local `ffmpeg` decoded the entire file to a null sink with exit code 0 and no errors.
- Extracted actual frames at 28, 30 and 35 seconds were visually inspected: settled recommendation, Equity route inspector, and independent receipt/current approval are legible.
- The local health response reported deterministic mode, synthetic data and external dispatch disabled before capture.

An initial launch attempt looked in the default Playwright cache and failed before recording. The script was corrected to set the project browser path before dynamically importing Playwright, then the successful capture above ran. No browser installation or alternate executable was downloaded for this task.

The recording was completed after the root's production-build signal. A subsequent narrow concurrent-preference/approval response guard was scheduled after capture; no capture remained active during that rebuild. This video demonstrates the successfully exercised normal path, not that concurrency edge case. Native desktop media-player playback was not separately tested by this worker; complete decode and sampled visual inspection were verified.

## Reproduce

Start the production demo first, then run from the repository root:

```sh
make demo
```

In another terminal:

```sh
node frontend/scripts/record-demo.mjs
```

The script defaults to the official browser under `.cache/ms-playwright`; `PLAYWRIGHT_BROWSERS_PATH` and `FORK_URL` may override their locations. It creates a fresh real experiment, preserves existing history, and overwrites the named video with a new genuine capture. Browser process/local-network permissions may require approval in a sandboxed environment.
