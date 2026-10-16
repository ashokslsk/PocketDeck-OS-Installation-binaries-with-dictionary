#!/bin/bash
# Build the finished Kannada-English dictionary.
# usage: finish_kn.sh PYTHON keed.jsonl COLLINS_FOLDER FIRMWARE_REPO
set -e
PY="$1"; KEED="$2"; COLLINS="$3"; REPO="$4"
TOOLS="$(cd "$(dirname "$0")" && pwd)"
WORK="$TOOLS/../work"
OUT="$TOOLS/../output"
cd "$TOOLS"
rm -rf "$OUT/KannadaEnglish"
"$PY" build_kn_dict.py "$KEED" "$WORK/keed_senses_kn.jsonl" "$COLLINS" "$WORK/kn.jsonl,$WORK/kn_best.jsonl" \
  "$WORK/glosses.json" "$OUT/KannadaEnglish"
python3 dictionary_tools.py prep "$OUT/KannadaEnglish"
# The .cspt prefix index keeps 16 bytes of each word, five or six Kannada letters,
# and many Kannada words share that much: lookups through it miss a third of
# them. Without it the device uses .idx.oft, which compares whole words.
rm -f "$OUT/KannadaEnglish/"*.cspt
# Every Kannada word shown: headwords, KEED examples and the Kannada meanings.
"$PY" -c "
import json, sys
with open('$WORK/kn_dict_text.jsonl', 'w') as f:
    for line in open('$KEED'):
        e = json.loads(line)
        f.write(json.dumps({'kn': ' '.join([e['kn']] + [x['kn'] for x in e['examples']])}, ensure_ascii=False) + '\n')
    for line in open('$WORK/keed_senses_kn.jsonl'):
        f.write(line)
"
"$PY" verify_shaping.py "$REPO" "$WORK/kn_dict_text.jsonl" 2>/dev/null | tee "$OUT/shaping-report-kannada-english.txt"
rm -f "$OUT/KannadaEnglish.zip"
(cd "$OUT" && zip -qr KannadaEnglish.zip KannadaEnglish)
ls -la "$OUT/KannadaEnglish" "$OUT/KannadaEnglish.zip"
