# Public source publication

Published on November 14, 2026 with explicit user authorization to push the latest conversational flow, documentation and demo video.

- Repository: https://github.com/ahmedhxssam/fork-ai
- Public default branch: `codex/fork`
- Reviewed application commit: `8a37394da6d8da4fb97ec1c9ee0a4c5b1e827a9d`
- Included earlier Studio commit: `94f182417cf1c524510fb67999c8a6954fb3b95a`
- Push: fast-forward from `8bc1649` to `8a37394`, no force push.
- Remote branch was independently checked with `git ls-remote` and matched the reviewed commit. The GitHub connector retrieved the published README containing the conversational flow.
- Current video: `artifacts/FORK-conversation-demo-silent.webm`, 6,228,643 bytes, 58.360 seconds, 1440×1000, silent VP8.
- GitHub video Git-blob SHA: `189d2578d930d444dd6c0a173d998703e9df7b2a`; it matches the local tracked blob.
- Video content SHA256: `665959013ededfdffdc3d6e7ca9f4a519d546cf197db667beff7efa73d0266bd`.

Immediately before publishing, `make test` passed 252 Python tests, 4 frontend model tests, TypeScript and the production build. The recorded final 36-browser-check release evidence remains in `CONVERSATION_RELEASE_VERIFICATION.md`; this publication step did not alter runtime source. A tracked-file scan found no credential-format matches or private runtime/cache/database/preparation files.

A subsequent documentation-only commit updates the README, submission draft and roadmap to reflect this verified publication. The earlier verification reports remain historical snapshots and do not retroactively claim that publication happened during those tests.

This is source/media publication, not a hosted application deployment or a competition submission. Runtime remains deterministic; no model-provider connection or API credential was added.
