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
2 entry has a word-audio file and an audio-example-sentence file. The
standalone deck embeds all 150 matching sentence MP3s for listening prompts;
it does not use Anki's native Chinese TTS.

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
python generate_hsk2_deck.py                    # writes HSK2_DualTask_Deck.apkg
python generate_hsk2_deck.py -o ~/Desktop/HSK2_DualTask_Deck.apkg
```

The deck contains **150 vocabulary entries × 3 card types = 450 cards** and is
named **HSK 2 - Offizieller Wortschatz (Hör- & Leseverstehen)**.

| Card type | Front | Back |
|-----------|-------|------|
| **1. Leseverstehen** | Chinese reading sentence | Sentence pinyin, German translation, word, pinyin, and German meaning |
| **2. Hörverstehen** | Visible, replayable embedded sentence-audio control | Chinese sentence, sentence pinyin, German translation, word, pinyin, and German meaning |
| **3. Wortschatz** | Isolated Chinese word | Pinyin and German meaning |

The generator verifies the actual package contains 150 notes, 450 cards, and
all 150 required sentence-audio files.

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
- A Chinese audio-example sentence, hard-coded pinyin, and German translation
- A distinct Chinese reading-example sentence, hard-coded pinyin, and German translation

## Contributing

Pull requests are welcome. When adding vocabulary:

1. Add the vocabulary entry to `HSK2_VOCAB`, its hard-coded audio-sentence
   pinyin to `AUDIO_SENTENCE_PINYIN`, and its hard-coded reading-sentence
   pinyin to `READING_SENTENCE_PINYIN` in `generate_hsk2_deck.py`.
2. Add its Chinese word to `OFFICIAL_HSK2_WORDS` in the same order.
3. Keep IDs unique and prefixed with `hsk2_`. The audio script derives its text
   directly from this standalone vocabulary list.

## License

This project is open source. See [LICENSE](LICENSE) for details.
