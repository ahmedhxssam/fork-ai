# Presentation build verification

Mode: **Deterministic Planner Mode**. No runtime model/API key, external dispatch,
production logistics claim, hosted deployment, or competition submission is implied.

## Verified commands and outputs

| Command | Actual result |
| --- | --- |
| `make setup` | Exact Python lock audited/synced and clean `npm ci` completed |
| `make test` | 84 Python tests; 4 frontend model tests; TypeScript and Vite build passed |
| `make test-browser` | 14 real Chromium checks passed against production assets/local API |
| `make demo` | Builds and serves the application at `127.0.0.1:8000` in one backend process |
| `make evidence` | 18 paired disruption cases / 108 verified adaptive and fixed executions saved |

Python reports four upstream deprecation warnings: Starlette's HTTPX test-client
transition and OR-Tools SWIG type metadata. They do not cause test failures.

## Browser acceptance

- Real fork, common shock, receipt inspection, approval and export.
- Every judge vehicle choice A/B/C at 30 minutes recomputes actual valid recovery.
- JSON and CSV actually download and parse; the JSON records approval and validity.
- All external browser origins blocked: fresh experiment and new shock still run
  through localhost; refresh/resume and playback remain usable.
- 390-pixel layout has no horizontal document overflow and supports world focus.
- Failed preference saves hide prior exports and block approval until resolved.
- Zero preference weights block approval; concurrent edits serialize and acknowledge
  the latest desired values. Lost POST responses can recover through a fresh GET.
- Transient 503 resume failure retains its saved pointer; confirmed 404 clears it.
- An approval response delayed past a newer preference acknowledgment cannot replace
  the newer revision or expose stale approved downloads.

Network fault injection is limited to the transport boundary; worlds, plans,
metrics, persistence and approval logic use the actual application.

## Independent evidence

The broad finite audit checked 6,780 generated worlds across seeds 1/26/73, all
policies and failed vehicles, adaptation on/off, and selected operation boundaries.
It reported zero invalid receipts and zero metric discrepancies. The final
recovery-load guard adds 471 hand-derived shock classifications and 270 generated
load-boundary worlds. These sets overlap; do not add them as independent samples.

Independent review identified three actionable issues. All were addressed and
reviewed: acknowledged preference consistency, saved-run retry recovery, and
recovery-load counting. Targeted regressions were observed failing before fixes.
The resulting scoped review has no unresolved P0/P1/P2 finding.

## Genuine artifacts

- [Mission briefing](assets/01-mission.png)
- [Initial parallel outcomes](assets/02-parallel-worlds.png)
- [Breakdown and recovery](assets/03-aftershock.png)
- [Three-world comparison](assets/04-world-comparison.png)
- [Referee inspection](assets/05-referee.png)
- [Narrow layout](assets/06-mobile.png)
- [Approved synthetic JSON](../artifacts/approved-resilience.json)
- [Approved synthetic CSV](../artifacts/approved-resilience.csv)
- [Paired demo evidence](../artifacts/demo-evidence.json)
- [Silent actual-UI recording](../artifacts/FORK-demo-silent.webm)
- [Recording provenance and full decode check](RECORDING_REPORT.md)

The video is a 37.08-second, 1440×960 genuine automated walkthrough without audio.
It is not a two-minute narrated pitch. See [PITCH.md](PITCH.md) for live narration.

## Boundaries

Use one backend worker. Roads, demand, priorities, costs and emissions are synthetic.
Initial routing is one trip; recovery permits one explicit extra depot load for a
healthy vehicle. That extra opportunity can produce more meals than the unshocked
reference; the breakdown itself is not claimed to be beneficial. No roadside rescue,
live LLM integration, real dispatch, global optimum, or field-validation claim.

Public source is published at [ahmedhxssam/fork-ai](https://github.com/ahmedhxssam/fork-ai).
Creation was verified as November 13, 2026 at 11:13 PM Eastern, with anonymous
source access confirmed. The competition entry has not been submitted and no
hosted deployment is claimed; the verified primary application runs locally.
