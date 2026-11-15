# FORK submission pack

**Recommended main track: Business and Enterprise.** Operations planning → Food-bank delivery resilience.

A delivery vehicle breaks down. FORK lets a food-bank coordinator compare recovery under the same shock, inspect independently checked evidence, and choose a simulated plan before dispatch.

## Open and review

Start `make demo`, then open:

- **Learn the story:** [three-minute guided walkthrough](http://127.0.0.1:8000/?view=logistics&tour=1), with Back, Next, Restart and a pauseable timer.
- **Present to judges:** [two-minute guided cut](http://127.0.0.1:8000/?view=logistics&tour=1&pace=120). The three-minute mode is rehearsal only.
- **Submission video:** [MP4](artifacts/FORK-submission-demo.mp4) · [captions](artifacts/FORK-submission-demo.srt) · [transcript](artifacts/FORK-submission-demo-transcript.txt) · [storyboard](artifacts/FORK-submission-demo-storyboard.json) · [media evidence](artifacts/FORK-submission-demo-evidence.json).
- **Presentation:** [guided mode instructions](docs/JUDGING_MODE.md) · [3-minute / 2-minute spoken scripts and FAQ](docs/PITCH.md) · [click sequence](DEMO.md).
- **Entry:** [copy-ready Devpost draft](DEVPOST.md) · [public source repository](https://github.com/ahmedhxssam/fork-ai).
- **Evidence:** [current presentation release](docs/PRESENTATION_RELEASE.md) · [test history](TESTING.md) · [earlier judge-readiness report](docs/JUDGE_READINESS.md) · [publication history](docs/PUBLICATION.md).

The final recording uses genuine browser interactions with the synthetic deterministic app. Narration uses local Kokoro neural speech with the built-in **af_heart** synthetic voice, not the owner's voice. Narration requires no API key and is separate from the app's deterministic runtime. Read the [presentation release report](docs/PRESENTATION_RELEASE.md) and media evidence for the measured duration, actual run and inspection boundaries; no listening or browser check is implied unless recorded there. The earlier [92-second recording](artifacts/FORK-judge-demo.mp4) remains historical fallback material.

## Which tracks fit this version?

Choose **one** main track. Business and Enterprise is the strongest fit because the product streamlines a coordinator's operations-management workflow through planning, dashboards, analytics and human review. Sustainability is a possible thematic alternative, but synthetic food-bank planning does not establish measured environmental impact. Education and Science and Discovery are less direct than the product's operational purpose; Healthcare and Entertainment are not the primary use case. Do not enter multiple main tracks.

**Best Overall Hack is automatic upon submission.** The supplied main-track source lists a **PlayStation 5 Disc Edition for each winning team member** and says a main-track winner cannot also win Best Overall. Enter the strongest appropriate main track and present the product honestly; there is no separate PS5 track to select or guaranteed award.

| Optional / special track | Source requirement | Current FORK fit |
|---|---|---|
| Best Rookie Hack | First-hackathon participants | Participant history is unverified; select only if the team meets the actual rule. |
| Best Hardware Hack | Creative physical-computing integration | No hardware integration is implemented. |
| CoStar: Inside and Out | Combine at least two of CoStar / Matterport / Vexcel layers; agentic, spatial/visual use | No implemented sponsor-data integration or runtime agent. Do not claim this track. |
| Amazon: Best Practical AI Innovation | AI-powered useful application; emphasis on agentic behavior, adaptation and user experience | Logistics is a named example, but the theme alone does not establish fit. Current runtime is a deterministic solver/simulator; no verified sponsor acceptance, runtime model or real-world adoption claim. Do not present it as an agentic AI integration. |
| Peri: Forward Deployed Challenge | Real business consulted during the hackathon; business name, contact name/role and supporting evidence | No evidenced business consultation is part of this release. |
| LangChain: Best use of deepagents | Build a deepagent | deepagents is not implemented. |
| Arlequin: AI-Driven Forensics | AI to uncover illegal/criminal patterns in forensic data | Food-bank planning is outside this use case. |
| Arlequin: Social Media analysis | Analyze social content and connectivity patterns | No social-network analysis is implemented. |
| Best Physical AI Hack | AI incorporated into physical hardware | No physical hardware or runtime AI integration is implemented. |

These recommendations describe demonstrated scope, not an organizer eligibility ruling. OpenAI Codex substantially assisted architecture, implementation, tests, debugging, review and documentation. Keep that disclosure; it neither proves eligibility nor constitutes a sponsor integration.

## Event requirements verified from the supplied files

*F26 Onsite Hacker Packet*, p. 4, specifies:

- Deliverables due **November 15, 2026, 8:00 AM**. The packet prints “8 am”; Princeton event-local time is Eastern.
- A **public GitHub repository created November 13–15, 2026**; hacking officially starts November 13 at 8:00 PM. Verify actual repository/history and participant eligibility separately.
- Exactly **one main track**; special tracks may be additional.
- Optional, highly recommended video **no longer than two minutes**, uploaded to a video platform and linked in Devpost.
- **Required in-person demo no longer than two minutes**, even with a video; judging November 15, 9:30 AM–2:30 PM.
- Discord usernames in the submission.

Pages 4–5 list Creativity, Utility, Charity and Avidity as judging criteria. The coherent food-bank story makes the need clear; the real app journey demonstrates functionality; the fair control and independent receipt explain the technical contribution. Synthetic results do not establish real charitable impact.

Pages 10–12 and *F26 Main Track.docx* establish the main-track descriptions, automatic Overall consideration and prizes. *F26 Special Tracks.pdf*, pp. 1–5, supplies the sponsor requirements summarized above. These files were read as event source material; they do not authorize external publication or submission actions.

## Readiness and remaining actions

The guided tour, shared brand and new submission video have their own [release verification](docs/PRESENTATION_RELEASE.md). The earlier source/media publication remains a separate [historical record](docs/PUBLICATION.md). Localhost is a local app, not a hosted demo URL. The existing [FORK.ai entry](https://devpost.com/software/fork-ai-pmeja0) was observed in Dia as **SUBMITTED — 5/5 steps done** before agent edits on November 15. Its name, tagline, thumbnail, story and gallery were subsequently updated in Dia and verified; submitted status, the original public URL, submission ID and team remain. [Publication record](docs/PUBLICATION.md)

1. Review the exact release, video, captions, entry text and substantial Codex-assistance disclosure.
2. Use the final release evidence to confirm the video is at most 2:00 and the actual judging-laptop journey works. Rehearse the short cut within the live limit.
3. The user chose the existing GitHub MP4 link, already prominent in the Devpost story. Keep the film at `artifacts/FORK-submission-demo.mp4` so the link stays unchanged. No separate upload or embedded player was requested; the dedicated video field remains empty.
4. Preserve the existing submitted entry. Confirm its Business and Enterprise selection, participant/eligibility information, repository timing and Discord usernames; verify any saved updates retain submitted status.
5. Keep the existing [entry URL](https://devpost.com/software/fork-ai-pmeja0) and verification record. The interface was observed as submitted; eligibility and award outcomes remain organizer decisions.

Preserve the initial greedy win (**224 meals**), the A-at-1,500 adaptive tie (**168 / 168 / 168**), paired controls (**144 / 120 / 144**) and gains (**+24 / +48 / +24**). Preserve unmet demand and any zero gain on other shocks. The independent referee checks consistency inside the declared model; it does not establish optimality or real-world safety. Exports never dispatch vehicles or contact volunteers.
