#!/usr/bin/env python3
"""
Build-time audio generation script for HSK Learning.

Generates MP3 files for every vocabulary sentence using the ElevenLabs API
(model: eleven_v3, voice: Bella) and writes them to
app/src/main/res/raw/ so they are bundled with the APK.

Usage:
    python3 scripts/generate_audio.py --api-key <ELEVENLABS_API_KEY>

    Or set the ELEVENLABS_API_KEY environment variable and run without --api-key.

The script is idempotent: files that already exist are skipped unless
--force is passed.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

# ---------------------------------------------------------------------------
# Vocabulary data — mirrors VocabData.kt so the script has no build dependency
# on the Android project.  Keep in sync with VocabData.kt.
# ---------------------------------------------------------------------------
VOCAB = [
    # HSK 1
    ("hsk1_ai",       "我爱我的家人。"),
    ("hsk1_ba",       "我爸爸在家工作。"),
    ("hsk1_beizi",    "请给我一个杯子。"),
    ("hsk1_bu",       "我不喝咖啡，我喝茶。"),
    ("hsk1_chi",      "我喜欢吃米饭。"),
    ("hsk1_da",       "这个苹果很大。"),
    ("hsk1_dianshi",  "我每天晚上看电视。"),
    ("hsk1_diannao",  "他用电脑工作。"),
    ("hsk1_gou",      "我家有一只狗。"),
    ("hsk1_hao",      "今天天气很好。"),
    ("hsk1_he",       "我想喝一杯茶。"),
    ("hsk1_hen",      "我今天很高兴。"),
    ("hsk1_hui",      "我会说一点汉语。"),
    ("hsk1_jia",      "我家在北京附近。"),
    ("hsk1_jintian",  "今天是星期几？"),
    ("hsk1_kan",      "我们一起看书吧。"),
    ("hsk1_lai",      "请你来我家吃饭。"),
    ("hsk1_laoshi",   "我的老师很好。"),
    ("hsk1_mama",     "我妈妈在家做饭。"),
    ("hsk1_mao",      "我有一只猫。"),
    ("hsk1_meiyou",   "我今天没有时间。"),
    ("hsk1_mingtian", "明天我去学校。"),
    ("hsk1_nihao",    "你好，我叫小明。"),
    ("hsk1_pengyou",  "他是我的好朋友。"),
    ("hsk1_qu",       "我们去北京旅游。"),
    ("hsk1_shi",      "我是学生。"),
    ("hsk1_shu",      "这本书很有意思。"),
    ("hsk1_shui",     "请给我一杯水。"),
    ("hsk1_xuesheng", "他们都是学生。"),
    ("hsk1_you",      "你有兄弟姐妹吗？"),
    ("hsk1_zai",      "他在哪里工作？"),
    ("hsk1_zaijian",  "明天见，再见！"),
    ("hsk1_zhongguo", "我来自中国。"),
    ("hsk1_xuexi",    "我每天学习汉语。"),
    ("hsk1_tianqi",   "今天天气怎么样？"),
    # HSK 2
    ("hsk2_bangzhu",   "谢谢你帮助我。"),
    ("hsk2_bi",        "今天比昨天冷。"),
    ("hsk2_bie",       "别忘了带水。"),
    ("hsk2_chuan",     "今天很冷，多穿衣服。"),
    ("hsk2_cong",      "我从北京来。"),
    ("hsk2_dadianhua", "我给妈妈打电话。"),
    ("hsk2_danshi",    "我想去，但是没有时间。"),
    ("hsk2_difang",    "北京是一个好地方。"),
    ("hsk2_du",        "他喜欢读书。"),
    ("hsk2_dui",       "你说的对。"),
    ("hsk2_fangjian",  "我的房间很小。"),
    ("hsk2_gaosu",     "请告诉我你的名字。"),
    ("hsk2_gen",       "我跟朋友一起去。"),
    ("hsk2_hai",       "他还在学校。"),
    ("hsk2_haizi",     "这个孩子很聪明。"),
    ("hsk2_huanying",  "欢迎来到我家。"),
    ("hsk2_huozhe",    "你喝茶或者咖啡？"),
    ("hsk2_jichang",   "我去机场接朋友。"),
    ("hsk2_jide",      "你记得我的名字吗？"),
    ("hsk2_juede",     "我觉得今天很冷。"),
    ("hsk2_kaishi",    "我们开始学习吧。"),
    ("hsk2_li",        "学校离我家很近。"),
    ("hsk2_lianxi",    "每天练习说汉语。"),
    ("hsk2_luyou",     "我喜欢旅游，看新地方。"),
    ("hsk2_nan",       "汉语有一点难。"),
    ("hsk2_piao",      "我买了两张电影票。"),
    ("hsk2_ren",       "我认识她，她是我朋友。"),
    ("hsk2_shenti",    "身体健康最重要。"),
    ("hsk2_shijian",   "我没有时间看电视。"),
    ("hsk2_xihuan",    "我喜欢学习汉语。"),
    ("hsk2_xiao",      "他总是笑着说话。"),
    ("hsk2_yiqi",      "我们一起去吃饭吧。"),
    ("hsk2_zhunbei",   "我在准备考试。"),
    ("hsk2_zuo",       "我坐公共汽车去学校。"),
    ("hsk2_zuotian",   "昨天我见了一个老朋友。"),
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
                        help="Directory to write MP3 files (default: app/src/main/res/raw/)")
    args = parser.parse_args()

    api_key = args.api_key.strip()
    if not api_key:
        print("ERROR: No API key provided. Use --api-key or set ELEVENLABS_API_KEY.", file=sys.stderr)
        sys.exit(1)

    # Resolve output directory relative to the project root (one level up from
    # this script's own directory when the script lives in scripts/).
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_dir = args.output_dir or os.path.join(project_root, "app", "src", "main", "res", "raw")
    os.makedirs(output_dir, exist_ok=True)

    total = len(VOCAB)
    generated = 0
    skipped = 0
    failed = 0

    for idx, (vocab_id, sentence) in enumerate(VOCAB, start=1):
        out_path = os.path.join(output_dir, f"{vocab_id}.mp3")
        if os.path.exists(out_path) and not args.force:
            print(f"[{idx}/{total}] SKIP  {vocab_id} (already exists)")
            skipped += 1
            continue

        print(f"[{idx}/{total}] GEN   {vocab_id}: {sentence}")
        try:
            audio_bytes = generate_mp3(sentence, api_key)
            with open(out_path, "wb") as f:
                f.write(audio_bytes)
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

        # Brief pause to avoid hitting rate limits.
        if idx < total:
            time.sleep(REQUEST_DELAY)

    print(f"\nDone. generated={generated}, skipped={skipped}, failed={failed}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
