"""
Generate ElevenLabs TTS audio for every sentence in VocabData.kt.

Run from the repository root. Requires the environment variable
ELEVENLABS_API_KEY to be set.

Existing files are skipped so the workflow is incremental — only new or
changed entries consume API quota.
"""

import os
import re
import sys
import time
import requests

API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
if not API_KEY:
    print("ERROR: ELEVENLABS_API_KEY environment variable is not set.", file=sys.stderr)
    sys.exit(1)

VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel (multilingual)
MODEL_ID = "eleven_multilingual_v2"
OUTPUT_DIR = os.path.join("app", "src", "main", "res", "raw")
VOCAB_FILE = os.path.join(
    "app", "src", "main", "java", "com", "laufbanane2", "hsklearning", "data", "VocabData.kt"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(VOCAB_FILE, encoding="utf-8") as fh:
    content = fh.read()

# Match VocabItem("id", level, "chinese", "pinyin", "english", "sentence", ...)
pattern = re.compile(
    r'VocabItem\(\s*"(\w+)"\s*,\s*\d+\s*,\s*"[^"]*"\s*,\s*"[^"]*"\s*,\s*"[^"]*"\s*,\s*"([^"]+)"'
)
items = pattern.findall(content)

if not items:
    print("ERROR: No VocabItem entries found in VocabData.kt.", file=sys.stderr)
    sys.exit(1)

print(f"Found {len(items)} vocabulary items.")

generated = 0
skipped = 0
errors = 0

for item_id, sentence in items:
    output_path = os.path.join(OUTPUT_DIR, f"{item_id}.mp3")
    if os.path.exists(output_path):
        print(f"  skip  {item_id} (file already exists)")
        skipped += 1
        continue

    print(f"  gen   {item_id}: {sentence}")
    try:
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
            headers={
                "xi-api-key": API_KEY,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            json={
                "text": sentence,
                "model_id": MODEL_ID,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True,
                },
            },
            timeout=30,
        )
        response.raise_for_status()
        with open(output_path, "wb") as out:
            out.write(response.content)
        generated += 1
        # Small delay to avoid hitting rate limits
        time.sleep(0.5)
    except requests.HTTPError as exc:
        print(f"  ERROR generating {item_id}: {exc}", file=sys.stderr)
        errors += 1
    except requests.RequestException as exc:
        print(f"  ERROR generating {item_id}: {exc}", file=sys.stderr)
        errors += 1

print(f"\nDone. Generated: {generated}, Skipped: {skipped}, Errors: {errors}")
if errors:
    sys.exit(1)
