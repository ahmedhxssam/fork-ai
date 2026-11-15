# Public source publication

## Neural narration replacement — November 15, 2026

The owner selected the built-in Kokoro **Heart (`af_heart`)** voice after three local auditions and requested replacement at the exact existing film path. The final MP4 remains `artifacts/FORK-submission-demo.mp4`; the branch-based link already in the Devpost story is unchanged. No separate video-platform upload was requested.

The replacement is **115.021333 seconds**, **1920×1080 / 30 fps**, **14,061,282 bytes**, SHA-256 `842700e74746913f85bc3e37a373785c888187e64a4301873e7632efe5ef56e5`. Full decoding, all eight static chapter frames, opening/outro/ending, caption text/timing bounds, audio levels and neutral-color checks passed. Audio measured −16.2 dB mean / −1.5 dB peak; no full-film human listening check is claimed. The existing raw browser take and application runtime were preserved. [Current release evidence](PRESENTATION_RELEASE.md)

The narration runs locally using Kokoro ONNX with pinned model/voice-bank hashes, isolated optional dependencies, measured sentence-group captions and cache invalidation for engine, voice, language, speed, text, model, package and script changes. Runtime FORK remains deterministic and has no model provider connected.

Publication verification will be recorded after the replacement is pushed and its existing public link is checked.

## Guided presentation publication — November 15, 2026

The application, shared brand, eight-chapter guide, final film, raw browser take, captions, scripts, screenshots and release documentation were committed as [`d406d2b`](https://github.com/ahmedhxssam/fork-ai/commit/d406d2b584c6a43de4d11e31f5fd4e4481a49c9b) and pushed to the public default branch `codex/fork`. `git ls-remote` returned that exact commit. The GitHub connector fetched the updated README at the exact commit.

The GitHub content API returned **14,121,445 bytes** for `artifacts/FORK-submission-demo.mp4`, with Git blob **`375f6e0f24c6295aba8edfe417e716ef2c3ce40a`**, matching local `git hash-object`. The decoded film is **115.021333 seconds**, 1920×1080 at 30 fps, H.264/AAC. Its SHA-256 is `ddb9b8d1767da14e0cc78ec64a2474cb68ee309f51b13e9a5f5342ee4750da49`. [Local release and media verification](PRESENTATION_RELEASE.md)

The user separately authorized updating the existing Devpost submission in **Dia** after the GitHub push. The existing project [FORK](https://devpost.com/software/fork-ai-pmeja0), submission ID **1305400**, was edited in place. Its original public URL and team were preserved. No project or gallery image was deleted.

Observed after save:

- Management interface: **SUBMITTED — 5/5 steps done**, project name **FORK**. The management slug changes from `1305400-fork-ai` to `1305400-fork`; the submission ID and public software URL remain the same.
- Main track: **Business/Enterprise**; this selection was inspected and left unchanged.
- New name/tagline, larger minimal brand thumbnail, updated story with the 44-browser-test result and guided mode, and a prominent link to the 1:55 GitHub film.
- Gallery: **nine images**, with five numbered current screenshots first. The four existing images remain, explicitly labeled as earlier prototype views.
- Public page: refreshed name/tagline, first new mission image, new film/guide links, one Challenges section and current guide/test descriptions were visible after saving.

[Published story copy](DEVPOST_PUBLIC_STORY.md) · [native public-page capture](assets/presentation/devpost-public.png) · [brand thumbnail](assets/brand/FORK-thumbnail.png)

The video is linked in the story. Its dedicated embedded-video field remains empty: Devpost requires YouTube/Vimeo/Youku, and separate YouTube hosting permission was requested rather than inferred from permission to edit Devpost. No hosted app or embedded player is claimed. User-specific eligibility and organizer decisions are separate from the observed submitted status.


## Judge-readiness release — November 14, 2026

Published with the owner's explicit approval: “Publish the tested FORK update.”

- Repository: https://github.com/ahmedhxssam/fork-ai
- Public default branch: `codex/fork`
- Tested UI/code/media commit: [`e37a0ee`](https://github.com/ahmedhxssam/fork-ai/commit/e37a0ee79849a42f021fdf520e8473f5ae4ddab4)
- Normal fast-forward push: `e7afc37` → `e37a0ee`; no force push.
- Anonymous GitHub API verification confirmed public visibility, the default branch and its exact head. The complete recursive tree excluded `.env.local`, the private CoStar report and reconnaissance paths.
- Anonymous raw HTTPS downloads of 13 selected docs/media/exports/screenshots matched the local files byte-for-byte. [Machine-readable receipt](../artifacts/FORK-judge-publication.json)
- Published [MP4](../artifacts/FORK-judge-demo.mp4): 3,703,039 bytes, 92.166667 seconds, 1440×900, H.264/AAC. SHA256 `7ff3cde0213b236e391a5c82a0cc22c27103e7ec7a6c3f3c149da030e22260d9`. [Captions](../artifacts/FORK-judge-demo.srt) and [transcript](../artifacts/FORK-judge-demo-transcript.txt) are included.
- Narration is the offline macOS Samantha system voice; browser actions and computed results are genuine. All scenario data is synthetic.

The tested release passed 252 Python tests, 4 frontend model tests, TypeScript/production build and the final 38-browser-check suite. A subsequent documentation-only commit records this publication and updates the owner checklist; it does not change tested runtime behavior or media. See [judge-readiness verification](JUDGE_READINESS.md).

The first anonymous verification attempt used a system Python with a missing local CA bundle and failed TLS validation. Verification then succeeded with the project's certificate-enabled HTTP client, with TLS checks retained and no authorization header. No security warning was bypassed.

This is public source/media publication, not a hosted app or Devpost submission. The remaining owner actions are optional video-host upload, final entry fields and submission confirmation.

---

# Earlier conversational source publication

Published on November 14, 2026 with explicit user authorization to push the latest conversational flow, documentation and demo video.

- Repository: https://github.com/ahmedhxssam/fork-ai
- Public default branch: `codex/fork`
- Reviewed application commit: `8a37394da6d8da4fb97ec1c9ee0a4c5b1e827a9d`
- Included earlier Studio commit: `94f182417cf1c524510fb67999c8a6954fb3b95a`
- Push: fast-forward from `8bc1649` to `8a37394`, no force push.
- Remote branch was independently checked with `git ls-remote` and matched the reviewed commit. The GitHub connector retrieved the published README containing the conversational flow.
- Video for that earlier release: `artifacts/FORK-conversation-demo-silent.webm`, 6,228,643 bytes, 58.360 seconds, 1440×1000, silent VP8.
- GitHub video Git-blob SHA: `189d2578d930d444dd6c0a173d998703e9df7b2a`; it matches the local tracked blob.
- Video content SHA256: `665959013ededfdffdc3d6e7ca9f4a519d546cf197db667beff7efa73d0266bd`.

Immediately before publishing, `make test` passed 252 Python tests, 4 frontend model tests, TypeScript and the production build. The recorded final 36-browser-check release evidence remains in `CONVERSATION_RELEASE_VERIFICATION.md`; this publication step did not alter runtime source. A tracked-file scan found no credential-format matches or private runtime/cache/database/preparation files.

A subsequent documentation-only commit updates the README, submission draft and roadmap to reflect this verified publication. The earlier verification reports remain historical snapshots and do not retroactively claim that publication happened during those tests.

This is source/media publication, not a hosted application deployment or a competition submission. Runtime remains deterministic; no model-provider connection or API credential was added.
