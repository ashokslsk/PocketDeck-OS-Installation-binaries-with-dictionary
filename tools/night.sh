#!/bin/bash
# Overnight: finish v1 with the 200M translations, then improve with the 1B model until morning.
# usage: night.sh PYTHON SCRATCH_SCRIPTS_DIR COLLINS ALAR FIRMWARE_REPO
PY="$1"; SCRIPTS="$2"; COLLINS="$3"; ALAR="$4"; REPO="$5"
TOOLS="$(cd "$(dirname "$0")" && pwd)"; WORK="$TOOLS/../work"; OUT="$TOOLS/../output"
log() { echo "$(date '+%H:%M') $*" | tee -a "$WORK/night.log"; }
while pgrep -f "scripts/translate.py" >/dev/null || [ ! -s "$WORK/heads_kn.jsonl" ]; do sleep 60; done
log "200M and headword translations finished: $(wc -l < "$WORK/kn.jsonl") strings, $(wc -l < "$WORK/heads_kn.jsonl") headwords"
bash "$TOOLS/finish.sh" "$PY" "$COLLINS" "$ALAR" "$REPO" >> "$WORK/night.log" 2>&1 && cp "$OUT/CollinsKannada.zip" "$OUT/CollinsKannada-200M.zip" && log "v1 dictionary built"
cp "$TOOLS/translate.py" "$SCRIPTS/translate.py"
log "starting 1B model"
(cd "$SCRIPTS/.." && HF_HUB_DISABLE_PROGRESS_BARS=1 caffeinate -i "$PY" -I scripts/translate.py "$WORK/to_translate.jsonl" "$WORK/kn_1b.jsonl" \
  --model prajdabre/rotary-indictrans2-en-indic-1B --beams 4 --stop-at 07:30 > "$WORK/translate_1b.log" 2>&1)
log "1B model stopped: $(wc -l < "$WORK/kn_1b.jsonl" 2>/dev/null) strings"
bash "$TOOLS/finish.sh" "$PY" "$COLLINS" "$ALAR" "$REPO" >> "$WORK/night.log" 2>&1 && log "final dictionary built"
