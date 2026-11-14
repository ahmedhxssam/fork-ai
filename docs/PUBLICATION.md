# Public source publication

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
