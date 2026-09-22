#!/usr/bin/env python3
"""
Build-time audio generation script for HSK Learning.

Generates MP3 files for every HSK 1 and HSK 2 vocabulary word, audio example
sentence, and reading-comprehension sentence declared in their standalone
deck generators. Uses the ElevenLabs API (model: eleven_v3, voice: Bella) and
writes files to audio/ at the repository root.

Usage:
    python3 scripts/generate_audio.py --api-key <ELEVENLABS_API_KEY>

    Or set the ELEVENLABS_API_KEY environment variable and run without --api-key.

The script is idempotent: files that already exist are skipped unless
--force is passed.
"""

import argparse
import ast
import json
import os
import sys
import time
import urllib.error
import urllib.request


def load_deck_vocabulary(level):
    """Read the canonical, ordered audio text from a standalone deck."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    deck_path = os.path.join(project_root, f"generate_{level}_deck.py")
    vocabulary_name = f"{level.upper()}_VOCAB"
    with open(deck_path, encoding="utf-8") as source_file:
        module = ast.parse(source_file.read(), filename=deck_path)

    for node in module.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == vocabulary_name
                and isinstance(node.value, ast.List)):
            vocabulary = ast.literal_eval(node.value)
            break
    else:
        raise RuntimeError(f"Missing {vocabulary_name} in {deck_path}.")

    if len(vocabulary) != 150:
        raise RuntimeError(f"Expected 150 {level.upper()} entries in {deck_path}.")

    try:
        audio_text = [(f"{entry[0]}.mp3", entry[4]) for entry in vocabulary]
        audio_text.extend(
            (f"{entry[0]}_reading.mp3", entry[6]) for entry in vocabulary
        )
        return audio_text + [
            (f"{entry[0]}_word.mp3", entry[1]) for entry in vocabulary
        ]
    except (IndexError, TypeError) as error:
        raise RuntimeError(f"Invalid {vocabulary_name} entry in {deck_path}.") from error


VOCABULARY = [
    entry
    for level in ("hsk1", "hsk2")
    for entry in load_deck_vocabulary(level)
]

VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Bella
MODEL_ID = "eleven_v3"
API_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

# Seconds to wait between requests to respect rate limits.
REQUEST_DELAY = 0.5


def generate_mp3(text: str, api_key: str) -> bytes:
    payload = json.dumps({
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "xi-api-key": api_key,
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate bundled audio assets via ElevenLabs.")
    parser.add_argument("--api-key", default=os.environ.get("ELEVENLABS_API_KEY", ""),
                        help="ElevenLabs API key (or set ELEVENLABS_API_KEY env var)")
    parser.add_argument("--force", action="store_true",
                        help="Re-generate even if the MP3 already exists")
    parser.add_argument("--output-dir", default=None,
                        help="Directory to write MP3 files (default: audio/ at repo root)")
    args = parser.parse_args()

    api_key = args.api_key.strip()
    if not api_key:
        print("ERROR: No API key provided. Use --api-key or set ELEVENLABS_API_KEY.", file=sys.stderr)
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_dir = args.output_dir or os.path.join(project_root, "audio")
    os.makedirs(output_dir, exist_ok=True)

    work = VOCABULARY

    total = len(work)
    generated = 0
    skipped = 0
    failed = 0

    for idx, (filename, text) in enumerate(work, start=1):
        out_path = os.path.join(output_dir, filename)
        if os.path.exists(out_path) and not args.force:
            print(f"[{idx}/{total}] SKIP  {filename} (already exists)")
            skipped += 1
            continue

        print(f"[{idx}/{total}] GEN   {filename}: {text}")
        try:
            audio_bytes = generate_mp3(text, api_key)
            with open(out_path, "wb") as audio_file:
                audio_file.write(audio_bytes)
            generated += 1
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")
            print(f"        ERROR HTTP {exc.code}: {body}", file=sys.stderr)
            failed += 1
        except urllib.error.URLError as exc:
            print(f"        ERROR network: {exc.reason}", file=sys.stderr)
            failed += 1
        except OSError as exc:
            print(f"        ERROR writing file: {exc}", file=sys.stderr)
            failed += 1

        if idx < total:
            time.sleep(REQUEST_DELAY)

    print(f"\nDone. generated={generated}, skipped={skipped}, failed={failed}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
