# FORK submission film source

This pipeline records the real local application with synthetic data. It does not redraw the product, mock API outcomes, contact a model provider, dispatch a vehicle, or erase stored experiments. Separate editorial graphics occupy the margin around the recorded app. The pointer is a recording aid added to the captured page.

Requirements: the repository's Playwright/Chromium install, `ffmpeg`/`ffprobe`, Python 3.10–3.13, and the optional [voice requirements](requirements-voice.txt) in a separate media environment. Current narration uses the built-in `af_heart` voice from [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M) through [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx). It is synthetic neural speech generated locally, not the project owner's voice. No voice is cloned, no API key or hosted speech service is used, and there is no music. This media-only model does not change FORK's deterministic application runtime.

One-time voice setup:

```sh
uv venv --python 3.13 .cache/tts-venv
uv pip install --python .cache/tts-venv/bin/python -r scripts/media/requirements-voice.txt
```

Download `kokoro-v1.0.onnx` and `voices-v1.0.bin` from the runtime's [model-files-v1.1 release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1) into `.cache/tts-models/`. The narration script verifies their pinned SHA-256 hashes before loading. Downloads and optional dependencies stay outside version control; synthesis itself does not fetch anything. The runtime is MIT-licensed; Kokoro model weights are Apache 2.0. `FORK_TTS_PYTHON` can override the isolated Python executable.

From the repository root, serve the built production application against a dedicated temporary database. Then:

```sh
node scripts/media/prepare.mjs
FORK_URL=http://127.0.0.1:8767/ node frontend/scripts/record-judging.mjs
.venv/bin/python scripts/media/render.py
```

For a voice-only revision, retain the existing evidence receipt and source take; no browser recapture is needed:

```sh
mkdir -p /private/tmp/fork-submission-media
cp artifacts/FORK-submission-source.webm /private/tmp/fork-submission-media/screen.webm
node scripts/media/prepare.mjs
.venv/bin/python scripts/media/render.py
```

The final output remains `artifacts/FORK-submission-demo.mp4`, so a branch-based GitHub link already on Devpost opens the replacement after publication. The original capture assertions remain evidence for that retained take; the new receipt records the replacement narration and delivery checks separately.

`FORK_MEDIA_WORK` optionally overrides `/private/tmp/fork-submission-media`. Intermediate audio and rendering assets stay there. A per-chapter audio manifest keys the cache by engine, voice, language, speed, text, model/voice-bank hashes and package version. Changing the narrator cannot silently reuse old system-voice audio. Captions follow measured sentence-group synthesis boundaries, including explicit pauses; short adjacent sentences can share one cue. This is not word alignment. The raw 2880×1600 browser capture is retained as `artifacts/FORK-submission-source.webm`; the final film, captions, storyboard, exact transcript, approved plan exports and evidence receipt are in `artifacts/`. Native source screenshots, chapter frames and contact sheet are in `docs/assets/presentation/`. The film is 115 seconds, including a three-second logo-only close. Review generated media before claiming a specific delivery check passed.

The recorder creates a fresh experiment through the visible UI and asserts the filmed figures: greedy 224 versus named policies 216/192/216 initially; shared vehicle A failure at minute 25; adapted outcomes 168 each versus fixed-route 144/120/144. It also checks preference persistence, referee validity, current-revision approval, JSON/CSV downloads, `external_dispatch=false`, no page errors, and zero external browser requests.

## Downloaded guidance and provenance

At the user's request, the [GitHub product-demo topic](https://github.com/topics/product-demo) was explored. The MIT-licensed [Product Demo Director](https://github.com/crimeacs/product-demo-director/tree/8de3b3b8d8f55bec01b0d57bbc2fd0ed9b703bf6) skill was downloaded at commit `8de3b3b8d8f55bec01b0d57bbc2fd0ed9b703bf6` using the built-in skill installer into the ignored local directory `.superpowers/demo-skills/product-demo-director`.

Its `SKILL.md`, license, and editing/capture/color guidance were reviewed as untrusted source. Its useful principles informed this film: source-bound claims, a causal sequence, complete meaningful UI, narration-safe holds, visible authority, and independent final-media checks. None of its downloaded scripts, npm dependencies, external voice/music APIs or advisory AI judge were run. This repository's small local pipeline adapts those principles to the existing installed tools. The downloaded skill retains its MIT license (copyright 2026 Artemii Novoselov); no vendor implementation code is copied into the production scripts.

OpenAI Codex assisted with the storyboard, local recording automation, compositing, verification and documentation. Runtime FORK remains deterministic, with no model provider connected.

## Color and delivery checks

The browser's retained VP8 recording is untagged YUV. The compositor decodes it as limited-range BT.601, applies the documented neutral-patch capture calibration (`Y+1`, `U+2`, `V+1`) against the retained native PNG, and then works in RGBA. It composites native footage, the chapter rail and exact-text captions in RGB before an explicit limited-range BT.709/YUV420 conversion with matching H.264 color tags. The logo close uses the same RGB-to-BT.709 path. This is a media format correction; it changes no UI layout, labels, scenario, routes, events or results. The raw recording and native screenshots retain the original capture.

The render script fully decodes the MP4, asserts 3,450 video frames at exactly 30 fps, H.264/YUV420P 1920×1080 and AAC 48 kHz, checks duration against the 120-second ceiling, and measures the narration level. It decodes reference paper patches in the chapter rail, app and outro and requires each RGB channel to remain within 3 of `(247,247,242)`. Extracted chapter frames, an opening/ending frame, and both five-second and one-second contact sheets support a separate visual review. Passing those technical checks does not establish event eligibility, submission, publication or real-world operational safety.
