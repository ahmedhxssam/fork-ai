#!/usr/bin/env python3
"""Prepare cached local Kokoro AIFF narration. Never downloads assets or calls a provider.

Usage: FORK_TTS_PYTHON=.cache/tts-venv/bin/python node scripts/media/prepare.mjs
Or: .cache/tts-venv/bin/python scripts/media/narrate.py --storyboard PATH --work-dir PATH
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
MODEL_SHA256 = 'beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a'
VOICES_SHA256 = 'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d'
SENTENCE_PAUSE = .25


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def cache_signature(identity: dict) -> str:
    return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def verify_asset(path: Path, expected: str) -> str:
    if not path.is_file():
        raise ValueError(f'Missing local Kokoro asset: {path}. Download and verify the pinned release assets separately; this script never downloads them.')
    actual = file_hash(path)
    if actual != expected:
        raise ValueError(f'SHA-256 mismatch for {path.name}: expected {expected}, got {actual} ({path.stat().st_size} bytes). The download may be incomplete; no inference was attempted.')
    return actual


def load_cached(audio: Path, sidecar: Path, signature: str) -> dict | None:
    try:
        meta = json.loads(sidecar.read_text())
        if meta.get('signature') == signature and file_hash(audio) == meta.get('audio_sha256'):
            return meta
    except (OSError, ValueError, TypeError):
        pass
    return None


def sentence_groups(text: str) -> list[str]:
    """Keep authored text; combine tiny adjacent sentences so short lines are not isolated."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    groups: list[str] = []
    pending = ''
    for sentence in sentences:
        pending = f'{pending} {sentence}'.strip()
        if len(pending.split()) >= 8:
            groups.append(pending)
            pending = ''
    if pending:
        if groups:
            groups[-1] += ' ' + pending
        else:
            groups.append(pending)
    return groups


def prepare(story: dict, work: Path) -> dict:
    if story.get('voice_engine') != 'kokoro-onnx':
        raise ValueError('narrate.py requires voice_engine="kokoro-onnx"; legacy macOS say is handled by prepare.mjs.')
    model = Path(os.environ.get('FORK_KOKORO_MODEL', str(ROOT / '.cache/tts-models/kokoro-v1.0.onnx'))).resolve()
    voices = Path(os.environ.get('FORK_KOKORO_VOICES', str(ROOT / '.cache/tts-models/voices-v1.0.bin'))).resolve()
    model_hash = verify_asset(model, MODEL_SHA256)
    voices_hash = verify_asset(voices, VOICES_SHA256)
    names = ['kokoro-onnx', 'onnxruntime', 'soundfile', 'numpy', 'phonemizer', 'espeakng-loader']
    try:
        packages = {name: importlib.metadata.version(name) for name in names}
    except importlib.metadata.PackageNotFoundError as error:
        raise ValueError(f'Missing optional voice dependency: {error.name}. Install scripts/media/requirements-voice.txt in the optional TTS environment.') from error
    if packages['kokoro-onnx'] != '0.6.1':
        raise ValueError('This pipeline requires kokoro-onnx==0.6.1; use scripts/media/requirements-voice.txt.')
    work.mkdir(parents=True, exist_ok=True)
    default_voice = story.get('voice', 'af_heart')
    default_speed = story.get('voice_speed', 1.0)
    lang = story.get('voice_lang', story.get('lang', 'en-us'))
    prepared, runtime = [], None
    for chapter in story['chapters']:
        n = chapter['n']
        text = chapter['narration'].strip()
        speed = float(chapter.get('voice_speed', default_speed))
        voice = chapter.get('voice', default_voice)
        if not text or not math.isfinite(speed) or not .5 <= speed <= 2:
            raise ValueError(f'Chapter {n}: narration must be nonempty and voice_speed must be between 0.5 and 2.')
        identity = dict(engine='kokoro-onnx', voice=voice, speed=speed, lang=lang, text=text,
                        model_sha256=model_hash, voices_sha256=voices_hash, packages=packages,
                        script_sha256=file_hash(Path(__file__)), sentence_pause=SENTENCE_PAUSE,
                        clause_pause=.1, min_sentence_group_words=8, format='AIFF PCM_16',
                        execution_provider='CPUExecutionProvider')
        signature = cache_signature(identity)
        audio_path, sidecar = work / f'{n}.aiff', work / f'{n}.narration.json'
        cached = load_cached(audio_path, sidecar, signature)
        if cached:
            prepared.append(dict(cached, cache_hit=True))
            continue
        if runtime is None:
            import onnxruntime as ort
            ort.disable_telemetry_events()
            import numpy as np
            import soundfile as sf
            from kokoro_onnx import Kokoro
            options = ort.SessionOptions()
            options.intra_op_num_threads = 2
            options.inter_op_num_threads = 1
            session = ort.InferenceSession(str(model), sess_options=options,
                                           providers=['CPUExecutionProvider'])
            runtime = (Kokoro.from_session(session, str(voices)), np, sf)
        kokoro, np, sf = runtime
        chunks, timings, cursor, sample_rate = [], [], 0, None
        for index, sentence in enumerate(sentence_groups(text)):
            # Short authored sentences can share a synthesis unit; measured cues identify that
            # complete sentence group, not unmeasured word/phoneme boundaries.
            audio, rate = kokoro.create(sentence, voice=voice, speed=speed, lang=lang,
                                        trim=True, sentence_pause=SENTENCE_PAUSE, clause_pause=.1)
            audio = np.asarray(audio, dtype=np.float32)
            if audio.ndim != 1 or not len(audio) or not np.isfinite(audio).all() or not np.any(np.abs(audio) > 1e-8):
                raise ValueError(f'Chapter {n}, sentence group {index + 1}: empty, non-finite or silent synthesis.')
            if sample_rate is not None and rate != sample_rate:
                raise ValueError(f'Chapter {n}: inconsistent synthesis sample rates.')
            sample_rate = rate
            if index:
                pause = np.zeros(round(SENTENCE_PAUSE * rate), dtype=np.float32)
                chunks.append(pause)
                cursor += len(pause)
            timings.append(dict(text=sentence, start=cursor / rate, end=(cursor + len(audio)) / rate))
            chunks.append(audio)
            cursor += len(audio)
        audio = np.concatenate(chunks)
        peak = float(np.max(np.abs(audio)))
        pcm_gain = min(1., .98 / peak)
        audio *= pcm_gain
        temporary = audio_path.with_name(f'{n}.tmp.aiff')
        sf.write(temporary, audio, sample_rate, format='AIFF', subtype='PCM_16')
        temporary.replace(audio_path)
        info = sf.info(audio_path)
        meta = dict(chapter=n, signature=signature, identity=identity, audio_file=audio_path.name,
                    audio_sha256=file_hash(audio_path), sample_rate=info.samplerate,
                    samples=info.frames, speech_seconds=info.frames / info.samplerate,
                    sentence_timings=timings, timing_kind='Measured synthesized sentence-group segments; not word alignment.',
                    pcm_gain=pcm_gain, cache_hit=False)
        temp_sidecar = sidecar.with_suffix('.tmp.json')
        temp_sidecar.write_text(json.dumps(meta, indent=2) + '\n')
        temp_sidecar.replace(sidecar)
        prepared.append(meta)
        print(f'Prepared neural chapter {n}: {meta["speech_seconds"]:.3f}s ({voice}, speed {speed})', file=sys.stderr)
    narration = dict(engine='kokoro-onnx', description=f'Offline local Kokoro ONNX neural narration ({default_voice}); a synthetic built-in voice, not the owner\'s voice.',
                     voice=default_voice, speed=default_speed, lang=lang, packages=packages,
                     python=platform.python_version(), model_sha256=model_hash, voices_sha256=voices_hash,
                     execution_provider='CPUExecutionProvider', telemetry_disabled_before_session=True,
                     sentence_pause_seconds=SENTENCE_PAUSE,
                     timing='Measured sentence-group audio segments; short adjacent sentences are synthesized together for prosody.',
                     assets=[dict(chapter=c['chapter'], file=c['audio_file'], sha256=c['audio_sha256'],
                                  signature=c['signature'], sample_rate=c['sample_rate'], samples=c['samples'],
                                  speech_seconds=c['speech_seconds'], voice=c['identity']['voice'], speed=c['identity']['speed']) for c in prepared])
    manifest = dict(narration=narration, chapters=prepared)
    (work / 'narration-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--storyboard', type=Path, required=True)
    parser.add_argument('--work-dir', type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = prepare(json.loads(args.storyboard.read_text()), args.work_dir.resolve())
        print(json.dumps(manifest))
    except (ValueError, OSError, KeyError) as error:
        print(f'Narration preparation failed: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
