"""Check that every Kannada word in the dictionary is drawn on the device exactly
as HarfBuzz shapes it, using the device algorithm from PocketDeck-OS's
scripts/kannada/build_kannada_font.py (same font, same syllable table).

usage: verify_shaping.py FIRMWARE_REPO kn.jsonl [glosses.json]
"""
import importlib.util
import json
import re
import sys

repo, kn_path = sys.argv[1:3]
spec = importlib.util.spec_from_file_location("knf", f"{repo}/scripts/kannada/build_kannada_font.py")
knf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(knf)

text = open(kn_path, encoding="utf-8").read()
if len(sys.argv) > 3:
    text += open(sys.argv[3], encoding="utf-8").read()
words = set(re.findall("[ಀ-೿‌‍]+", json.loads(json.dumps(text))))
text_words = {}
for line in open(kn_path, encoding="utf-8"):
    for w in re.findall("[ಀ-೿‌‍]+", json.loads(line).get("kn", "")):
        text_words[w] = text_words.get(w, 0) + 1

reg = knf.TTFont(knf.REGULAR)
order = reg.getGlyphOrder()
adv_r = [reg["hmtx"][n][0] for n in order]
cmap = {cp: order.index(n) for cp, n in reg.getBestCmap().items() if 0x0C80 <= cp <= 0x0CFF or cp in knf.EXTRA_CODEPOINTS}
reph = order.index("rephknda")
shaper = knf.Shaper(knf.REGULAR)
dic, _ = knf.build_dictionary(shaper)
kern = knf.build_kerning(shaper, dic, cmap, reph)
space = order.index("space")
bad = []
for w in sorted(words):
    want = [(g, a) for g, a in shaper.shape(w) if not (g == space and a == 0)]
    got = knf.device_shape(w, dic, cmap, reph, adv_r, kern)
    if [g for g, _ in want] != [g for g, _ in got] or sum(a for _, a in want) != sum(a for _, a in got):
        bad.append(w)
occ = sum(text_words.values())
bad_occ = sum(text_words.get(w, 0) for w in bad)
print(f"{len(words)} distinct Kannada words: {len(words) - len(bad)} identical to HarfBuzz, {len(bad)} differ")
print(f"word occurrences in translations: {occ}, affected: {bad_occ} ({100 * bad_occ / max(1, occ):.3f}%)")
for w in sorted(bad, key=lambda w: -text_words.get(w, 0))[:25]:
    print("  differs:", w, text_words.get(w, 0))
