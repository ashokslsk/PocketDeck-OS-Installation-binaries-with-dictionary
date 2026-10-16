#!/bin/bash
# Build the finished dictionary from the translations.
# usage: finish.sh PYTHON COLLINS_FOLDER ALAR_YML FIRMWARE_REPO
set -e
PY="$1"; COLLINS="$2"; ALAR="$3"; REPO="$4"
TOOLS="$(cd "$(dirname "$0")" && pwd)"
WORK="$TOOLS/../work"
OUT="$TOOLS/../output"
cd "$TOOLS"
"$PY" glosses.py "$COLLINS" "$ALAR" "$WORK/kn.jsonl" "$WORK/heads.jsonl" "$WORK/heads_kn.jsonl" "$WORK/glosses.json"
rm -rf "$OUT/CollinsKannada"
# Where the 1B model also translated a string, keep whichever of the two
# translations comes back closer to the English (choose.py).
: > "$WORK/kn_best.jsonl"
if [ -s "$WORK/kn_1b.jsonl" ]; then
  "$PY" choose.py prepare "$WORK/kn.jsonl" "$WORK/kn_1b.jsonl" "$WORK/bt_in.jsonl"
  HF_HUB_DISABLE_PROGRESS_BARS=1 "$PY" -I translate.py "$WORK/bt_in.jsonl" "$WORK/bt_out.jsonl" \
    --model prajdabre/rotary-indictrans2-indic-en-dist-200M --src kan_Knda --tgt eng_Latn --device mps --beams 2 \
    2>&1 | grep -E "/s|Traceback|Error" || true
  "$PY" choose.py pick "$WORK/kn.jsonl" "$WORK/kn_1b.jsonl" "$WORK/bt_out.jsonl" "$WORK/kn_best.jsonl"
fi
"$PY" build_dict.py "$COLLINS" "$WORK/kn.jsonl,$WORK/kn_best.jsonl" "$WORK/glosses.json" "$OUT/CollinsKannada"
python3 dictionary_tools.py prep "$OUT/CollinsKannada"
cat "$WORK/kn.jsonl" "$WORK/kn_best.jsonl" > "$WORK/kn_all.jsonl"
"$PY" verify_shaping.py "$REPO" "$WORK/kn_all.jsonl" "$WORK/glosses.json" 2>/dev/null | tee "$OUT/shaping-report.txt"
rm -f "$OUT/CollinsKannada.zip"
(cd "$OUT" && zip -qr CollinsKannada.zip CollinsKannada)
ls -la "$OUT" "$OUT/CollinsKannada"
