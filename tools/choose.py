"""Pick the better of two Kannada translations by back-translation.

Both candidates are translated back into English (IndicTrans2 Kannada->English)
and the one whose back-translation is closer to the Collins English (chrF++)
is kept. Ties go to the larger (1B) model.

usage: choose.py prepare kn.jsonl kn_1b.jsonl BT_IN.jsonl
       choose.py pick    kn.jsonl kn_1b.jsonl BT_OUT.jsonl KN_BEST.jsonl
"""
import json
import sys

from collins import clean_kannada


def load(path):
    out = {}
    for line in open(path):
        try:
            d = json.loads(line)
            out[d["t"]] = d["kn"]
        except (ValueError, KeyError):
            pass
    return out


mode, small_path, big_path = sys.argv[1:4]
small, big = load(small_path), load(big_path)
both = [t for t in big if t in small and clean_kannada(small[t]) != clean_kannada(big[t])]

if mode == "prepare":
    seen = set()
    with open(sys.argv[4], "w") as f:
        for t in both:
            for k in (small[t], big[t]):
                if k not in seen:
                    seen.add(k)
                    f.write(json.dumps({"t": k}, ensure_ascii=False) + "\n")
    print(f"{len(big)} 1B translations, {len(both)} differ from 200M; {len(seen)} to back-translate")
else:
    from sacrebleu.metrics import CHRF

    chrf = CHRF(word_order=2)
    back = load(sys.argv[4])
    kept_big = kept_small = 0
    with open(sys.argv[5], "w") as f:
        for t, k in big.items():
            choice = k
            if t in both and small[t] in back and k in back:
                s_small = chrf.sentence_score(back[small[t]], [t]).score
                s_big = chrf.sentence_score(back[k], [t]).score
                if s_small > s_big + 2:
                    choice = small[t]
            if choice == k:
                kept_big += 1
            else:
                kept_small += 1
            f.write(json.dumps({"t": t, "kn": choice}, ensure_ascii=False) + "\n")
    print(f"kept 1B for {kept_big}, 200M for {kept_small} (of {len(big)} strings the 1B model translated)")
