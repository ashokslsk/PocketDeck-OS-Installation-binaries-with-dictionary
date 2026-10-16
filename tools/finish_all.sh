#!/bin/bash
# Rebuild both dictionaries with the Wiktionary additions and the context-fixed
# KEED meanings (translations in work/kn_extra.jsonl).
# usage: finish_all.sh PYTHON COLLINS_FOLDER FIRMWARE_REPO
set -e
PY="$1"; COLLINS="$2"; REPO="$3"
TOOLS="$(cd "$(dirname "$0")" && pwd)"; WORK="$TOOLS/../work"; OUT="$TOOLS/../output"
cd "$TOOLS"

rm -rf "$OUT/CollinsKannada"
"$PY" build_dict.py "$COLLINS" "$WORK/kn.jsonl,$WORK/kn_best.jsonl,$WORK/kn_extra.jsonl" "$WORK/glosses.json" \
  "$OUT/CollinsKannada" "$WORK/wikt_en.json" "$WORK/wikt_en_aliases.json" "$WORK/extra_en.json"
python3 dictionary_tools.py prep "$OUT/CollinsKannada" > /dev/null
rm -f "$OUT/CollinsKannada.zip"; (cd "$OUT" && zip -qr CollinsKannada.zip CollinsKannada)

rm -rf "$OUT/KannadaEnglish"
"$PY" build_kn_dict.py "$WORK/keed.jsonl" "$WORK/keed_senses_kn.jsonl,$WORK/kn_extra.jsonl" "$COLLINS" \
  "$WORK/kn.jsonl,$WORK/kn_best.jsonl" "$WORK/glosses.json" "$WORK/wikt_kn.json" "$WORK/wikt_kn_forms.json" \
  "$OUT/KannadaEnglish" "$WORK/extra_kn.json"
python3 dictionary_tools.py prep "$OUT/KannadaEnglish" > /dev/null
# .cspt keeps 16 bytes of each word (five or six Kannada letters): a third of
# Kannada lookups miss through it. Without it the device compares whole words.
rm -f "$OUT/KannadaEnglish/"*.cspt
rm -f "$OUT/KannadaEnglish.zip"; (cd "$OUT" && zip -qr KannadaEnglish.zip KannadaEnglish)

# Display check of every Kannada word in both dictionaries.
"$PY" -c "
import json
with open('$WORK/all_kannada.jsonl', 'w') as f:
    for p in ['$WORK/kn.jsonl', '$WORK/kn_best.jsonl', '$WORK/kn_extra.jsonl', '$WORK/keed_senses_kn.jsonl', '$WORK/kn_topic_text.jsonl', '$WORK/kn_topic_terms.jsonl']:
        for line in open(p):
            f.write(line)
    for line in open('$WORK/keed.jsonl'):
        e = json.loads(line)
        f.write(json.dumps({'kn': ' '.join([e['kn']] + [x['kn'] for x in e['examples']])}, ensure_ascii=False) + '\n')
    for k, blocks in json.load(open('$WORK/wikt_kn.json')).items():
        ex = [x['text'] for b in blocks for s in b['senses'] for x in s['examples']]
        f.write(json.dumps({'kn': ' '.join([k] + ex)}, ensure_ascii=False) + '\n')
    for k, secs in json.load(open('$WORK/extra_kn.json')).items():
        f.write(json.dumps({'kn': ' '.join([k] + secs)}, ensure_ascii=False) + '\n')
"
"$PY" verify_shaping.py "$REPO" "$WORK/all_kannada.jsonl" "$WORK/glosses.json" 2>/dev/null | tee "$OUT/shaping-report.txt"
rm -f "$OUT/shaping-report-kannada-english.txt"
ls -la "$OUT"
