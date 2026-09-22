# HSK Learning Scripts

Python scripts for generating audio and standalone Anki decks for the official
HSK 1.0 and HSK 2.0 vocabulary.

## What is HSK?

HSK (汉语水平考试, *Hànyǔ Shuǐpíng Kǎoshì*) is the official Chinese language proficiency exam. The vocabulary is organised into levels:

| Level | Words | Description |
|-------|-------|-------------|
| HSK 1 | 150 official words | Beginner vocabulary |
| HSK 2 | 150 official words | Elementary vocabulary |

## Scripts

### Generate Audio Files

Word, audio-example-sentence, and reading-comprehension-sentence audio are
generated with the ElevenLabs API.
You need an API key.

```bash
python scripts/generate_audio.py --api-key YOUR_ELEVENLABS_KEY
```

Generated `.mp3` files are placed in `audio/` at the repository root. Each HSK
entry has a word-audio file and an audio-example-sentence file. Each standalone
deck embeds its 150 matching sentence MP3s for listening prompts; it does not
use Anki's native Chinese TTS.

Options:

| Flag | Description |
|------|-------------|
| `--api-key` | ElevenLabs API key (or set `ELEVENLABS_API_KEY` env var) |
| `--output-dir` | Directory to write MP3 files (default: `audio/`) |
| `--force` | Re-generate even if the MP3 already exists |

### Generate Anki Deck

The standalone HSK 1 and HSK 2 decks (`.apkg`) can be generated and imported
directly into [Anki](https://apps.ankiweb.net/).

```bash
pip install genanki
python generate_hsk1_deck.py                    # writes HSK1_DualTask_Deck.apkg
python generate_hsk1_deck.py -o ~/Desktop/HSK1_DualTask_Deck.apkg
python generate_hsk2_deck.py                    # writes HSK2_DualTask_Deck.apkg
python generate_hsk2_deck.py -o ~/Desktop/HSK2_DualTask_Deck.apkg
```

Each deck contains **150 vocabulary entries × 3 card types = 450 cards** and
is named **HSK 1/2 - Offizieller Wortschatz (Hör- & Leseverstehen)**.

| Card type | Front | Back |
|-----------|-------|------|
| **1. Leseverstehen** | Chinese reading sentence | Sentence pinyin, German translation, word, pinyin, and German meaning |
| **2. Hörverstehen** | Visible, replayable embedded sentence-audio control | Chinese sentence, sentence pinyin, German translation, word, pinyin, and German meaning |
| **3. Wortschatz** | Isolated Chinese word | Pinyin and German meaning |

Each generator verifies the actual package contains 150 notes and 450 cards, and
embeds its 150 reading-sentence and 150 listening-sentence audio files. Reading
audio plays on the answer card.

## Project Structure

```
audio/                             # Generated HSK 1 and HSK 2 word and sentence MP3 files
generate_hsk1_deck.py              # Standalone HSK 1 Anki deck generator
generate_hsk2_deck.py              # Standalone HSK 2 Anki deck generator
scripts/
└── generate_audio.py              # ElevenLabs audio generation script
```

## Vocabulary Coverage

| Level | Words | Status |
|-------|-------|--------|
| HSK 1 | 150 | ✅ Official HSK 1.0 list |
| HSK 2 | 150 | ✅ Official HSK 2.0 list |

Every entry includes:
- Simplified Chinese character(s)
- Pinyin with tone marks
- German meaning
- A Chinese audio-example sentence, hard-coded pinyin, and German translation
- A distinct Chinese reading-example sentence, hard-coded pinyin, and German translation

## Contributing

Pull requests are welcome. When adding vocabulary:

1. Add the vocabulary entry to the matching `HSK1_VOCAB` or `HSK2_VOCAB` list,
   with hard-coded sentence pinyin.
2. Add its Chinese word to the matching official-word tuple in the same order.
3. Keep IDs unique and prefixed with the level (`hsk1_` or `hsk2_`). The audio
   script derives its text directly from these standalone vocabulary lists.

## License

This project is open source. See [LICENSE](LICENSE) for details.
