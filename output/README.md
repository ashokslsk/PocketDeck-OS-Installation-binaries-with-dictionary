# Kannada dictionaries for PocketDeck-OS (Xteink X3)

Two dictionaries, one firmware:

| Dictionary | Look up | You get |
|---|---|---|
| **CollinsKannada** | an English word | Collins COBUILD meanings and examples, each with Kannada |
| **KannadaEnglish** | a Kannada word | English meanings, the meaning in Kannada, examples in both languages, and the matching Collins entries |

## Install

1. **Firmware.** Flash `firmware/pocketdeck-os-x3.bin` (copy it to the SD card,
   then **Settings > System > SD Card Firmware Update**). It draws Kannada in
   dictionary entries and finds Kannada words with endings (ಮನೆಯಲ್ಲಿ, ಕಣ್ಣಿನ,
   ಸ್ಮರಿಸಿ); older builds can do neither.
2. **Kannada font.** Keep `/tools/fonts/kannada.knf` on the SD card (it is
   already there if Panchanga shows Kannada).
3. **Dictionaries.** Unzip `CollinsKannada.zip` and `KannadaEnglish.zip` into
   `/.dictionaries/` (or `/dictionaries/`), so you have for example
   `/.dictionaries/KannadaEnglish/KannadaEnglish.idx` and the other files.
4. Choose the dictionary in the reader's dictionary settings (or per book):
   **CollinsKannada** for English books, **KannadaEnglish** for Kannada books.

Both are recognised as Kannada dictionaries by `lang=` in their `.ifo`
(`en-kn`, `kn-en`).

## CollinsKannada (English → Kannada)

The Collins COBUILD Advanced Learner's Dictionary (34,159 headwords) with Kannada
added to every entry:

| Added | Where | Example |
|---|---|---|
| Kannada equivalents | under the headword | `ಕನ್ನಡ: ತ್ಯಜಿಸು, ನಿಲ್ಲಿಸು` |
| Each meaning in Kannada | under the English meaning | `ಅರ್ಥ: ನೀವು ಒಂದು ಸ್ಥಳವನ್ನು ತ್ಯಜಿಸಿದರೆ…` |
| Each example sentence in Kannada | indented under the English example | `ತನ್ನ ಹೆತ್ತವರು ತನ್ನನ್ನು ತೊರೆದಿದ್ದಾರೆ ಎಂದು…` |

The English Collins text is unchanged. A plain headword was also added for each of
the 101 words that Collins splits into numbered entries (`be(1)`, `be(2)`…), so
looking up "be" or "certain" opens the definition directly. The 26,627 inflected
and derived forms that Collins lists inside entries (reparations, abandoning,
fonder, beautifully, insecurity…) open their entry directly too.

**From English Wiktionary** (CC BY-SA 4.0): 3,562 of the 60,000 commonest English
words that Collins lacks (selfie, ketosis, splendor, bullseye…), each with up to
three meanings and an example, in English and Kannada, marked "(Wiktionary)";
and about 1,900 more word forms that open their Collins entry (analyzed ->
analyse, fluxes -> flux). Names are left out, so "John" in a book does not open
a lower-case slang meaning.

## KannadaEnglish (Kannada → English)

About 43,000 Kannada headwords from three sources:

- **Kannada-English Etymological Dictionary** (KEED) by N. Učida and
  B. B. Rajapurohit, edited by J. Takashima (ILCAA, Tokyo University of Foreign
  Studies, 2018; CC BY-NC 4.0), 31,000 entries: transliteration, part of speech,
  usage marks (literary, colloquial, obsolete…), numbered English meanings with
  each meaning also in Kannada (ಅರ್ಥ), the book's own Kannada example sentences
  with their English translation, variant spellings and origin.
- **Kannada-English Wiktionary** (CC BY-SA 4.0), 2,336 words: meanings in
  English and Kannada, and its Kannada example sentences with English.
- **Collins, reversed**: for a Kannada word, the English words whose Kannada
  equivalent it is (ನೀರು → water, moisture…), each with the Collins meaning that
  uses the word, in English and Kannada, and an example in both languages.

About 83,000 inflected forms (ಮನೆಯಲ್ಲಿ, ಪುಸ್ತಕವನ್ನು, ಮಾಡುತ್ತಾನೆ), from
Wiktionary's declension tables and from the Kannada text, open their headword
directly. For any other form the firmware tries
the word with letters removed from the end (ಪಿತೃಗಳನ್ನು → … → ಪಿತ), and with the
ending ು (ಸ್ಮರಿಸಿ → ಸ್ಮರಿಸು), so most words tapped in a Kannada book are found.
That fallback picks the longest headword that fits, which is occasionally a
different word that happens to start the same way.

The dictionary ships without the `.cspt` quick index: it stores 16 bytes of each
word, only five or six Kannada letters, and a third of Kannada lookups missed
through it. The device uses `.idx.oft` instead, which compares whole words.

## Subject vocabulary (both dictionaries)

Added in both directions, marked with the subject (e.g. "ವೈದ್ಯಕೀಯ / medical"):

- **Written by hand** (Kannada written directly, not machine translated): 62 AI and
  technology terms (LLM, RAG, context window, hallucination, agentic, UPI…),
  65 English Gen Z words (rizz, delulu, no cap, aura farming…), 47 Kannada youth
  slang words (ಮಗಾ, ಸಖತ್, ಬೊಂಬಾಟ್, ಚಿಂದಿ, ಕಿರಿಕ್, ಹವಾ…), 33 Kannada literary
  movements, genres and art forms (ನವೋದಯ, ನವ್ಯ, ಬಂಡಾಯ, ದಲಿತ, ನವ್ಯೋತ್ತರ, ವಚನ,
  ಯಕ್ಷಗಾನ, ಹನಿಗವನ, ವೆಬ್ ಸರಣಿ…) and 39 Ayurveda and yoga terms (ವಾತ, ಪಿತ್ತ, ಕಫ,
  ಪಂಚಕರ್ಮ, ತ್ರಿಫಲಾ…), each with an example in both languages.
- **English Wiktionary**: 8,968 medical, computing, AI, maths, politics,
  socio-economic, Hindu/Purana and Internet-slang words that Collins lacks, with
  their meanings and examples in Kannada. 4,648 of them also became Kannada
  headwords: only where the Kannada term translates back to the same English.
- **Kannada Wikipedia** (CC BY-SA 4.0): 2,692 subject articles with an English
  twin (ವೃತ್ತ = circle, ಸಂವಿಧಾನ = constitution, ಕಪ್ಪು ಶಿಲೀಂಧ್ರ = mucormycosis,
  ದುರ್ಗೆ, ಅಗ್ನಿ ಪುರಾಣ…): the opening sentences of the Kannada and the English
  article, written by people.

Where a word already had an entry, the subject sense is added below it
("hallucination" keeps its Collins meaning and gains the AI sense).

## Memory

- Firmware image: 6,425,088 bytes, fits the 6,553,600-byte X3 app partition with
  128,512 bytes free. Static RAM 64,424 of 327,680 bytes.
- At run time the Kannada font takes about 20 KB of heap while a definition is
  open. It is opened only for a Kannada dictionary and only when at least 40 KB is
  free (24 KB contiguous); otherwise the entry is shown without Kannada shaping
  rather than risking a crash. Closing the definition frees it.
- Kannada lookups try at most 40 shorter forms of a word, one small index read each.
- The dictionary files live on the SD card; the device reads one page of a
  definition at a time.

## How the Kannada was made (and its limits)

- Collins meanings and examples: machine translated with **IndicTrans2**
  (AI4Bharat), run locally. Every string was translated with the 200M model; the
  most common words were translated again with the larger 1B model, and where the
  two differ, both Kannada versions were translated back into English and the one
  closer to the Collins English was kept.
- KEED meanings in Kannada: translated with the IndicTrans2 1B model. Usage
  labels are kept out of the translation and shown in Kannada ((fig.) ->
  ಲಾಕ್ಷಣಿಕ), and a one-word meaning is translated with its part of speech
  ("mine" of a noun -> ಗಣಿ, not ನನ್ನದು). KEED's own
  example sentences and their English are from the book, not machine translated.
- Collins equivalents: the headword translated on its own, kept only when the
  translations of that word's own meanings and examples use the same Kannada word
  (this drops wrong senses and mere spellings of the English word), plus words
  from the **Alar** Kannada–English dictionary by V. Krishna (ODC-ODbL) that pass
  the same check.
- Machine translation is usually right but can be literal or awkward, especially
  for idioms, grammar notes and one-word meanings without context.
- Display: every distinct Kannada word was checked against HarfBuzz using the
  device's own syllable algorithm; see the `shaping-report*.txt` files.
- `CollinsKannada-200M.zip` is the first complete Collins build (200M model only).
- Collins COBUILD is © HarperCollins Publishers and KEED is CC BY-NC 4.0: these
  files are for personal use.

## Rebuilding

`tools/` holds the scripts. Collins: `extract.py` (strings to translate),
`translate.py` (IndicTrans2, resumable), `heads.py` + `glosses.py` (equivalents),
`choose.py` (back-translation check), `build_dict.py`, `finish.sh`. KEED:
`keed_text.py` (PDF text in reading order), `keed.py` (entries),
`keed_mt_input.py`, `build_kn_dict.py`. Wiktionary: `wiktionary.py` (entry
parser), `wikt_prepare.py` (what to add). `finish_all.sh` rebuilds both. Shared:
`dictionary_tools.py prep` (from CrossInk/PocketDeck-OS) and `verify_shaping.py`.
`firmware/kannada-dictionary.patch` is the firmware change.
