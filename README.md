# HSK 2 Learning Scripts

Python scripts for generating audio and an Anki deck for the official HSK 2.0
vocabulary.

## What is HSK?

HSK (汉语水平考试, *Hànyǔ Shuǐpíng Kǎoshì*) is the official Chinese language proficiency exam. The vocabulary is organised into levels:

| Level | Words | Description |
|-------|-------|-------------|
| HSK 2 | 150 official words | Elementary vocabulary |

## Scripts

### Generate Audio Files

Word and audio-example-sentence audio are generated with the ElevenLabs API.
You need an API key.

```bash
python scripts/generate_audio.py --api-key YOUR_ELEVENLABS_KEY
```

Generated `.mp3` files are placed in `audio/` at the repository root. Each HSK
2 entry has a word-audio file and an audio-example-sentence file. Run this
before building the Anki deck so available audio is embedded in the cards.

Options:

| Flag | Description |
|------|-------------|
| `--api-key` | ElevenLabs API key (or set `ELEVENLABS_API_KEY` env var) |
| `--output-dir` | Directory to write MP3 files (default: `audio/`) |
| `--force` | Re-generate even if the MP3 already exists |

### Generate Anki Deck

The standalone HSK 2 deck (`.apkg`) can be generated and imported directly into
[Anki](https://apps.ankiweb.net/).

```bash
pip install genanki
python generate_hsk2_deck.py                    # writes hsk2.apkg
python generate_hsk2_deck.py -o ~/Desktop/hsk2.apkg
```

The deck contains **150 vocabulary entries × 2 card types = 300 cards** and is
named **HSK 2 Vocabulary - Learning Progress**.

| Card type | Front | Back |
|-----------|-------|------|
| **Audio sentence** | 🔊 spoken Chinese example sentence | Chinese sentence, German translation, word, pinyin, and German meaning |
| **Reading sentence** | Chinese reading example sentence | German translation, word, pinyin, German meaning, and audio example |

Audio files from `audio/` are embedded automatically when present.

## Project Structure

```
audio/                             # Generated HSK 2 word and sentence MP3 files
generate_hsk2_deck.py              # Standalone HSK 2 Anki deck generator
scripts/
└── generate_audio.py              # ElevenLabs audio generation script
```

## Vocabulary Coverage

| Level | Words | Status |
|-------|-------|--------|
| HSK 2 | 150 | ✅ Official HSK 2.0 list |

Every entry includes:
- Simplified Chinese character(s)
- Pinyin with tone marks
- German meaning
- A Chinese audio-example sentence and German translation
- A distinct Chinese reading-example sentence and German translation

## Contributing

Pull requests are welcome. When adding vocabulary:

1. Add the full nine-value entry to `HSK2_VOCAB` in `generate_hsk2_deck.py`.
2. Add its Chinese word to `OFFICIAL_HSK2_WORDS` in the same order.
3. Keep IDs unique and prefixed with `hsk2_`. The audio script derives its text
   directly from this standalone vocabulary list.

## License

This project is open source. See [LICENSE](LICENSE) for details.
