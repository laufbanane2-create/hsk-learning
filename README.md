# HSK Learning Scripts

Python scripts for generating audio and Anki decks for HSK vocabulary.

## What is HSK?

HSK (汉语水平考试, *Hànyǔ Shuǐpíng Kǎoshì*) is the official Chinese language proficiency exam. The vocabulary is organised into levels:

| Level | Words | Description |
|-------|-------|-------------|
| HSK 1 | 150   | Basic everyday vocabulary |
| HSK 2 | +150  | Elementary vocabulary (builds on HSK 1) |

## Scripts

### Generate Audio Files

Audio is generated with the ElevenLabs API. You need an API key.

```bash
pip install requests
python scripts/generate_audio.py --api-key YOUR_ELEVENLABS_KEY
```

Generated `.mp3` files are placed in `audio/` at the repository root. Run this before building the Anki deck so audio is embedded in the cards.

Options:

| Flag | Description |
|------|-------------|
| `--api-key` | ElevenLabs API key (or set `ELEVENLABS_API_KEY` env var) |
| `--output-dir` | Directory to write MP3 files (default: `audio/`) |
| `--force` | Re-generate even if the MP3 already exists |

### Generate Anki Deck

An Anki deck (`.apkg`) with all HSK 2 vocabulary can be generated and imported directly into [Anki](https://apps.ankiweb.net/).

```bash
pip install genanki
python scripts/generate_anki_deck.py          # writes scripts/hsk2.apkg
python scripts/generate_anki_deck.py -o ~/Desktop/hsk2.apkg  # custom path
```

The deck contains **155 vocabulary entries × 3 card types = 465 cards**:

| Card type | Front | Back |
|-----------|-------|------|
| **Word** | Chinese character(s) | Pinyin + English + example sentence + audio |
| **Sentence** | Chinese example sentence + audio | Pinyin + English translation + word |
| **Audio** | 🔊 (spoken example sentence) | Chinese sentence + pinyin + English + word |

Audio files from `audio/` are embedded automatically when present.

## Project Structure

```
audio/                             # Generated MP3 files (one per vocab entry)
scripts/
├── generate_audio.py              # ElevenLabs audio generation script
└── generate_anki_deck.py          # Anki deck (.apkg) generation script
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

1. Add the entry to the `VOCAB` list in `scripts/generate_audio.py`.
2. Add the full entry (id, chinese, pinyin, english, sentence, sentence_pinyin, sentence_english) to `HSK2_VOCAB` in `scripts/generate_anki_deck.py`.
3. Keep IDs unique and prefixed with the level, e.g. `hsk1_apple`, `hsk2_compare`.

## License

This project is open source. See [LICENSE](LICENSE) for details.
