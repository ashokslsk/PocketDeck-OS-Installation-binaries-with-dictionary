"""Translate to_translate.jsonl into Kannada with IndicTrans2 (resumable).

usage: translate.py IN.jsonl OUT.jsonl [--model M] [--limit N] [--beams B] [--stop-at HH:MM]
Each output line is {"t": english, "kn": kannada}. Rerunning skips lines already done.
"""
import argparse
import json
import re
import os
import time

import torch
from IndicTransToolkit.processor import IndicProcessor
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("inp")
ap.add_argument("out")
ap.add_argument("--model", default="prajdabre/rotary-indictrans2-en-indic-dist-200M")
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--beams", type=int, default=4)
ap.add_argument("--tokens", type=int, default=6000, help="padded source tokens per batch")
ap.add_argument("--chunk", type=int, default=2048)
ap.add_argument("--src", default="eng_Latn")
ap.add_argument("--tgt", default="kan_Knda")
ap.add_argument("--device", default="")
ap.add_argument("--stop-at", default="", help="local time HH:MM to stop (resume later)")
a = ap.parse_args()

done = set()
if os.path.exists(a.out):
    with open(a.out) as f:
        for line in f:
            try:
                done.add(json.loads(line)["t"])
            except ValueError:
                pass
todo = [json.loads(l)["t"] for l in open(a.inp)]
todo = [t for t in todo if t not in done]
if a.limit:
    todo = todo[: a.limit]
print(f"{len(done)} done, {len(todo)} to go", flush=True)

dev = a.device or ("mps" if torch.backends.mps.is_available() else "cpu")
tok = AutoTokenizer.from_pretrained(a.model, trust_remote_code=True)
model = AutoModelForSeq2SeqLM.from_pretrained(a.model, trust_remote_code=True, torch_dtype=torch.float16 if dev != "cpu" else torch.float32).to(dev).eval()
ip = IndicProcessor(inference=True)

out = open(a.out, "a")
start, n = time.time(), 0
def past_stop_time():
    if not a.stop_at:
        return False
    h, m = map(int, a.stop_at.split(":"))
    now = time.localtime()
    return (now.tm_hour, now.tm_min) >= (h, m) and now.tm_hour < 18  # an overnight run stops in the morning


for c in range(0, len(todo), a.chunk):
    if past_stop_time():
        print("stop time reached", flush=True)
        break
    # Keep the priority order across chunks, sort by length inside one to cut padding.
    chunk = sorted(todo[c : c + a.chunk], key=len)
    i = 0
    while i < len(chunk):
        j = i + 1
        while j < len(chunk) and (j - i + 1) * (len(chunk[j]) // 3 + 8) <= a.tokens and j - i < 128:
            j += 1
        batch = chunk[i:j]
        pre = ip.preprocess_batch(batch, src_lang=a.src, tgt_lang=a.tgt)
        enc = tok(pre, truncation=True, max_length=256, padding="longest", return_tensors="pt").to(dev)
        # Kannada output is rarely over twice the source tokens; the cap stops
        # the occasional repetition loop from holding the whole batch.
        cap = min(320, int(enc["input_ids"].shape[1] * 2.2) + 12)
        with torch.no_grad():
            gen = model.generate(**enc, use_cache=True, min_length=0, max_new_tokens=cap, num_beams=a.beams,
                                 no_repeat_ngram_size=0, repetition_penalty=1.1)
        dec = ip.postprocess_batch(tok.batch_decode(gen, skip_special_tokens=True, clean_up_tokenization_spaces=True), lang=a.tgt)
        for s, d in zip(batch, dec):
            d = re.sub(r"([.।,!?-])\1{3,}", r"\1", d)
            out.write(json.dumps({"t": s, "kn": d.strip()}, ensure_ascii=False) + "\n")
        out.flush()
        n += len(batch)
        i = j
    if dev == "mps":
        torch.mps.empty_cache()
    el = time.time() - start
    print(f"{n}/{len(todo)}  {n/el:.1f}/s  eta {(len(todo)-n)/(n/el)/3600:.1f} h", flush=True)
