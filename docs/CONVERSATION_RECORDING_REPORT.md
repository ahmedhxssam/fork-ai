# Conversation walkthrough recording evidence

Recorded 2026-11-14T06:01:33.443Z from `http://127.0.0.1:8000` using repository Playwright Chromium, fresh browser storage, and the frozen locally served application.

- Video: [FORK-conversation-demo-silent.webm](../artifacts/FORK-conversation-demo-silent.webm)
- Duration: **58.360 seconds**.
- Size: **6,228,643 bytes**.
- Frame: **1440 × 1000**, vp8, 25/1 fps.
- Audio streams: **0**. This is a silent visual walkthrough, with no narration or soundtrack.
- SHA256: `665959013ededfdffdc3d6e7ca9f4a519d546cf197db667beff7efa73d0266bd`.

## Recorded journey

The following are script action timestamps, not frame-accurate media cues; browser recording starts before navigation orchestration.

- 0.56s: Ordinary incomplete repair-clinic description.
- 2.85s: Focused missing-work question.
- 6.39s: Plain answer: six bikes.
- 8.31s: Plain answer: about 45 minutes each.
- 10.24s: Plain answer: two hours, used as 120 minutes.
- 10.90s: Explicit simplified-scope question and visible limits.
- 13.41s: Reviewable actual model: 2 people, six 45-minute jobs, 120 minutes.
- 17.48s: Three real independently checked futures: each completes 4/6.
- 22.21s: Ordinary conflict example: two versus three technicians, one hour versus 90 minutes.
- 24.72s: Both staffing source claims remain quoted.
- 27.42s: Both time-window source claims remain quoted.
- 29.46s: Person resolves conflicts with three technicians and 90 minutes.
- 30.11s: Explicit simplified-scope question and visible limits.
- 32.60s: Reviewable actual model: 3 people, six 45-minute jobs, 90 minutes.
- 36.67s: Three real independently checked futures: each completes 6/6.
- 40.79s: Independent replay receipt, checks and current evidence hashes.
- 43.99s: Human approval bound to the selected current simulated future.
- 45.04s: Actual approved JSON downloaded and checked.

The first actual built-in prompt has two volunteers and missing work quantity, duration and available time. Visible plain answers are “Six bikes”, “About 45 minutes each” and “We have two hours”. The conflict prompt visibly supplies two versus three technicians and one hour versus 90 minutes; the person selects three people and 90 minutes. Both journeys explicitly accept simplified scope and check the model-review consent before a real run. Equal policy outcomes remain visible.

The script uses application controls and native scrolling. There are no fixtures, substituted metrics, overlays, title cards, edited cuts, speed changes or direct API mutations. API responses are observed only to assert the actual UI actions. Normal actions create new saved experiments without erasing old ones. The temporary actual JSON download is checked and removed during cleanup.

## Actual computed outcomes

| Experiment | Future | Capacity | Horizon (minutes) | On time | Completed |
| --- | --- | --- | --- | --- | --- |
| wf-2cc86a7f7e5a42c5 | Throughput | 2 | 120 | 4/6 | 4 |
| wf-2cc86a7f7e5a42c5 | Resilience | 2 | 120 | 4/6 | 4 |
| wf-2cc86a7f7e5a42c5 | Priority | 2 | 120 | 4/6 | 4 |
| wf-c357040187c346e7 | Throughput | 3 | 90 | 6/6 | 6 |
| wf-c357040187c346e7 | Resilience | 3 | 90 | 6/6 | 6 |
| wf-c357040187c346e7 | Priority | 3 | 90 | 6/6 | 6 |

First model SHA256: `aae2d060b16017f87e7e1ae45bf933196131b529371e4e301b84519c4fe74349`. Second model SHA256: `23d6da1cef02726aa3fc2062f7ac3f4426c87ad11581968c28ddcaa58dca4a84`. They differ. All six displayed futures have valid independent receipts, with every returned check passed.

## Executed checks and limits

- Playwright checked actual capacity, six tasks, 45-minute durations, 120/90-minute model horizons, and canonical model hashes. Staffing conflict choices were 2/3; time conflict choices were 60/90. Both original claims were asserted visibly quoted.
- Launch authoring answers and brief/model hashes match the accepted interview. Every world has segments, the current model hash, a valid receipt and expected hand-derived completion totals: four for two people over 120 minutes, six for three people over 90 minutes.
- Actual downloaded JSON matches the second experiment, current approval revision, model hash and selected independent evidence hash.
- External-origin browser requests were blocked; none were observed. No browser page errors or HTTP responses of 400 or higher were observed.
- `ffprobe` confirmed duration, dimensions, codec and absence of audio. `ffmpeg -v error -i VIDEO -f null -` decoded the complete video successfully.
- Visually inspected 12 extracted full-resolution frames at 1.5, 5.3, 11.8, 14.3, 18.5, 25.4, 28.2, 37.7, 41.7, 43.5, 45.5 and 48.0 seconds with `view_image`. The opening prose, plain answer, scope exclusions, reviewable facts, checked consent, quoted staffing and time conflicts, four-of-six and six-of-six results, independent verification banner, checks, evidence hashes and approved export controls are readable across these frames. Native smooth-scroll transitions remain in the uncut take. Samples were extracted to `/tmp/fork-conversation-frames`; these are QA intermediates, not presentation overlays or permanent deliverables.
- This records localhost synthetic deterministic planning. It does not establish deployment, offline use, competition submission, eligibility, field performance, arbitrary-language understanding or a connected model provider. No real dispatch or external messaging occurs.

The first sandboxed Chromium launch failed before recording because macOS denied its MachPort registration. The same script then ran successfully with the approved execution escalation. No failed take replaced an existing video.

## Reproduce

Serve the frozen current frontend and API at `http://127.0.0.1:8000`, then run `node frontend/scripts/record-conversation.mjs` from the repository root. The script refuses to overwrite an existing take. Move an earlier video to a separately named archive before intentional re-recording. It saves the finalized video before browser shutdown and only promotes a take after assertions, probing and complete decoding pass.
