# HSK Learning Scripts

Python scripts for generating audio and Anki decks for HSK vocabulary.

## What is HSK?

HSK (汉语水平考试, *Hànyǔ Shuǐpíng Kǎoshì*) is the official Chinese language proficiency exam. The vocabulary is organised into levels:

| Level | Words | Description |
|-------|-------|-------------|
| HSK 1 | 150 official words | Basic everyday vocabulary |
| HSK 2 | +150 official words | Elementary vocabulary (builds on HSK 1) |

## Scripts

### Generate Audio Files

Word and example-sentence audio are generated with the ElevenLabs API. You need an API key.

```bash
pip install requests
python scripts/generate_audio.py --api-key YOUR_ELEVENLABS_KEY
```

Generated `.mp3` files are placed in `audio/` at the repository root. Each vocabulary entry has a word-audio file and an example-sentence-audio file. Run this before building the Anki deck so available audio is embedded in the cards.

Options:

| Flag | Description |
|------|-------------|
| `--api-key` | ElevenLabs API key (or set `ELEVENLABS_API_KEY` env var) |
| `--output-dir` | Directory to write MP3 files (default: `audio/`) |
| `--force` | Re-generate even if the MP3 already exists |

### Generate Anki Deck

An Anki deck (`.apkg`) for either HSK level can be generated and imported directly into [Anki](https://apps.ankiweb.net/).

```bash
pip install genanki
python scripts/generate_anki_deck.py          # writes scripts/hsk2.apkg
python scripts/generate_anki_deck.py -o ~/Desktop/hsk2.apkg  # custom path
python scripts/generate_anki_deck.py --level hsk1 -o ~/Desktop/hsk1.apkg
```

Each deck contains **150 vocabulary entries × 3 card types = 450 cards**. HSK 1 contains its 150 words, and HSK 2 follows the official 150-word HSK 2 list.

| Card type | Front | Back |
|-----------|-------|------|
| **Word** | Chinese character(s) | Pinyin, English, word audio, example sentence, and sentence audio |
| **Sentence** | Chinese example sentence | Pinyin, English translation, word, word audio, and sentence audio |
| **Audio** | 🔊 spoken example sentence and prompt | Chinese sentence, pinyin, English, word, and word audio |

Audio files from `audio/` are embedded automatically when present.

## Project Structure

```
audio/                             # Generated word and sentence MP3 files
scripts/
├── generate_audio.py              # ElevenLabs audio generation script
└── generate_anki_deck.py          # Anki deck (.apkg) generation script
```

## Vocabulary Coverage

| Level | Words | Status |
|-------|-------|--------|
| HSK 1 | 150 | ✅ 150-word HSK 1 deck |
| HSK 2 | 150 | ✅ Official 150-word HSK 2 list |

Every entry includes:
- Simplified Chinese character(s)
- Pinyin with tone marks
- English meaning
- Example sentence in Chinese
- Example sentence in pinyin
- English translation of the example sentence

## Contributing

Pull requests are welcome. When adding vocabulary:

1. Add the full entry (id, chinese, pinyin, english, sentence, sentence_pinyin, sentence_english) to the appropriate `HSK1_VOCAB` or `HSK2_VOCAB` list in `scripts/generate_anki_deck.py`.
2. Add its Chinese word to the corresponding `OFFICIAL_HSK1_WORDS` or `OFFICIAL_HSK2_WORDS` list so it is included in the deck.
3. Keep IDs unique and prefixed with the level, e.g. `hsk1_apple`, `hsk2_compare`. The audio script automatically supplements its vocabulary from the deck lists.

## License

This project is open source. See [LICENSE](LICENSE) for details.
