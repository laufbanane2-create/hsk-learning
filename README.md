# HSK Learning

An Android flashcard app for studying Mandarin Chinese vocabulary at HSK levels 1 and 2.

## What is HSK?

HSK (汉语水平考试, *Hànyǔ Shuǐpíng Kǎoshì*) is the official Chinese language proficiency exam. The vocabulary is organised into levels:

| Level | Words | Description |
|-------|-------|-------------|
| HSK 1 | 150   | Basic everyday vocabulary |
| HSK 2 | +150  | Elementary vocabulary (builds on HSK 1) |

## Features

- **Flashcard review** — tap to reveal the translation, rate yourself, and move on
- **Spaced-repetition system (SRS)** — words you find hard appear more often
- **Audio playback** — hear each word and example sentence pronounced correctly
- **Example sentences** — every word comes with a full Chinese sentence, pinyin, and English translation
- **Multiple Chinese fonts** — choose from several Google Fonts to practise reading different typefaces
- **Per-level selection** — study HSK 1 only, HSK 2 only, or both together
- **Progress stats** — track how many words you have reviewed in each session

## Screenshots

> Add screenshots here once the app is built.

## Getting Started

### Prerequisites

- Android Studio (Hedgehog or newer)
- Android SDK 26+
- A physical device or emulator running Android 8.0+

### Build & Run

```bash
git clone https://github.com/laufbanane2-create/hsk-learning.git
cd hsk-learning
./gradlew assembleDebug
```

Install on a connected device:

```bash
./gradlew installDebug
```

Or open the project in Android Studio and click **Run**.

### Generate Audio Files

Audio is generated with the ElevenLabs API. You need an API key.

```bash
pip install requests
python scripts/generate_audio.py --api-key YOUR_ELEVENLABS_KEY
```

Generated `.mp3` files are placed in `app/src/main/res/raw/`. Add them to the project and rebuild.

## Project Structure

```
app/
└── src/main/
    ├── java/com/laufbanane2/hsklearning/
    │   ├── data/
    │   │   ├── VocabData.kt       # All 300 vocabulary items (HSK1 + HSK2)
    │   │   ├── VocabItem.kt       # Data model
    │   │   ├── SrsManager.kt      # Spaced-repetition logic
    │   │   └── StatsManager.kt    # Session statistics
    │   ├── ui/
    │   │   ├── learn/             # Flashcard screen
    │   │   └── settings/          # Settings screen (level & font selection)
    │   └── MainActivity.kt
    ├── res/
    │   ├── layout/                # XML layouts
    │   ├── raw/                   # Audio files (.mp3)
    │   └── values/strings.xml     # All user-facing strings
scripts/
└── generate_audio.py              # ElevenLabs audio generation script
```

## Vocabulary Coverage

| Level | Words | Status |
|-------|-------|--------|
| HSK 1 | 150   | ✅ Complete |
| HSK 2 | 150   | ✅ Complete |

Every entry includes:
- Simplified Chinese character(s)
- Pinyin with tone marks
- English meaning
- Example sentence in Chinese
- Example sentence in pinyin
- English translation of the example sentence

## Contributing

Pull requests are welcome. When adding vocabulary:

1. Add `VocabItem` entries to `VocabData.kt` (inside the correct `hsk1` or `hsk2` list).
2. Add a matching entry to `scripts/generate_audio.py` so audio can be generated.
3. Keep IDs unique and prefixed with the level, e.g. `hsk1_apple`, `hsk2_compare`.

## License

This project is open source. See [LICENSE](LICENSE) for details.
