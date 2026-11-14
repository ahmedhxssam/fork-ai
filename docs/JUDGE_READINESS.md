# Judge-readiness release verification

November 14, 2026. This report describes the locally prepared FORK polish, not a competition submission or publication receipt.

## What changed

Both existing entry screens now identify **Business & Enterprise / Operations planning**. Studio provides a prominent **Try the food-bank demo** link to the retained logistics route. The logistics view names **Food-bank delivery resilience**, identifies the food-bank coordinator and explains compare plans → shared breakdown → recovery review before launch. Mobile entry text and header spacing were checked and improved.

The existing simulation, referee, preference, persistence and approval/export interfaces were preserved. No model provider, sponsor integration, dispatch capability or new engine physics was added. README, Devpost copy, demo guide and pitch now tell the same primary logistics story, with Studio as an existing secondary capability.

## Executed verification

- `make test`: **252 Python tests passed**, four existing third-party deprecation warnings; **4 frontend model tests passed**; TypeScript and production Vite build passed.
- New presentation acceptance was observed **RED** against the old UI, then **2/2 GREEN** after implementation. It tests category/above-fold CTA → real launch → A-at-1,500 shared shock → referee → approved current synthetic JSON, plus the 390px mobile journey and document width.
- A review-driven mobile CTA check observed **13px < 16px** before the CSS correction. The submitted style uses 16px on mobile.
- A complete production-browser run passed **38/38 in 50.0 seconds** after the CTA correction. The final acceptance run after the mobile header spacing adjustment also passed **38/38 (reported 1.2 minutes)** using Node 24.18.0.
- An earlier full attempt stopped at the Studio proof with an abrupt Node 22 worker termination and no usable failure diagnostic. The unchanged isolated proof file passed 2/2; the complete 38-case run then passed. That interrupted attempt is not counted as a pass.
- Independent source review found no P0–P2 defects in the scoped patch. Its mobile-size observation was fixed; release test-history wording was updated.

The full suite includes actual API computation, all supported failed vehicles, stale/uncertain preferences, lost/delayed responses, revision-bound approval, JSON/CSV downloads, Studio authoring/outages and external-origin-blocked journeys. Finite tests prove their observed behavior, not optimality, safety, arbitrary natural-language understanding or real-world validity.

Test server: localhost 8766 with a separate temporary SQLite database. User-saved experiments were not deleted. Historical screenshots/exports were backed up before evidence tests and restored afterward; current media uses distinct `judge/` and `FORK-judge-*` paths.

The already-running server on localhost 8000 was verified as FORK seed 26, and its served index matched the final production-build bytes. It was reused; an attempted second bind was stopped by the occupied port, rather than replacing the user's server. The native in-app browser confirmed the primary link and polished entry on 8000.

## Genuine current media

- [Narrated MP4](../artifacts/FORK-judge-demo.mp4): **92.166667 seconds**, 1440×900, H.264 video/AAC 48kHz audio, approximately 3.7MB. Below the two-minute limit.
- Narration: offline installed macOS Samantha system voice, 208 words; not an imitation of the owner. [Transcript](../artifacts/FORK-judge-demo-transcript.txt) and [captions](../artifacts/FORK-judge-demo.srt) are included.
- Actual browser actions were recorded. At A-at-1,500, adaptive meals are 168/168/168 and fixed-plan controls 144/120/144. All three displayed referee receipts were valid. The run's synthetic packet was actually approved and downloaded. [Run/timeline evidence](../artifacts/FORK-judge-demo-evidence.json)
- External origins were blocked during recording; **zero external requests observed**. No credentials or proprietary sponsor material were used.
- Encoded frames at 1s, 69s and 85s were inspected, corresponding to the category/entry, referee and approved-export moments. Current entry, recovery and mobile screenshots were separately opened and inspected. Audio stream/duration and non-silence were checked: mean −16.4dB, max −0.5dB; no human listening check is claimed.

Recording was captured against the same desktop UI; the final later style adjustment only removes the cramped caption in the ≤620px mobile header. It does not change the recorded 1440px desktop UI or computed results. The refreshed 390px screenshots show that final mobile presentation.

## Reviewable files

- [Entry](assets/judge/01-entry.png) and [food-bank landing](assets/judge/02-food-bank.png)
- [Greedy baseline](assets/judge/03-baseline.png) and [shared shock](assets/judge/04-shared-shock.png)
- [Recovery](assets/judge/05-recovery.png) and [full comparison](assets/judge/06-comparison.png)
- [Referee](assets/judge/07-referee.png) and [approved export](assets/judge/08-approved.png)
- [390px entry](assets/judge/09-mobile-entry.png) and [390px food-bank view](assets/judge/10-mobile-food-bank.png)

The exact small media-generation scripts remain under `/private/tmp/fork-judge-media/`; they do not call an external model service. Older clips and evidence files remain version-specific historical records.

## Remaining owner actions

Review the local pack, authorize/publish the exact tested source update, upload/link the optional video, complete track/participant fields and submit Devpost before the written 8:00 AM Eastern cutoff. [Submission pack](../SUBMISSION_READY.md) is the single index. Current local checks do not establish those external actions, clean-machine setup, unrestricted offline installation or organizer eligibility.
