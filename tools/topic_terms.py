"""Subject vocabulary from English Wiktionary and Kannada Wikipedia.

usage: topic_terms.py EN_EN_FOLDER COLLINS_KANNADA_FOLDER KNWIKI_FOLDER WORK_DIR

English Wiktionary: words whose meanings carry a subject label ("(medicine)",
"(machine learning)", "(Internet slang)"...), not already in CollinsKannada,
commonest first, at most PER_DOMAIN per subject; only the labelled meanings
are kept (up to three).            -> topic_wikt.json
Kannada Wikipedia: articles in subject categories that have an English twin
and name a term, not a person or event.  -> topic_knwiki.json
Also writes wikt_words.json, the set of English Wiktionary headwords.
"""
import json
import os
import re
import sys

from wordfreq import zipf_frequency

import wiktionary as wk
from collins import read_stardict
from domains import DOMAINS, domain_of_categories, domain_of_label, is_term, looks_like_term

PER_DOMAIN = 1500
MIN_ZIPF = {"genz": 1.0, "ai": 1.0}  # new and specialist words are rare in general text
LABEL_RX = re.compile(r'class="ib-content label-content">(.*?)</span><span class="ib-brac label-brac">\)', re.S)


def score(word):
    """How common a term is. wordfreq rates a phrase by its common words ("in play"
    looks frequent), so a phrase counts as its rarest word, less a penalty."""
    parts = [p for p in re.split(r"[\s-]+", word.lower()) if p]
    if any(len(p) == 1 for p in parts):
        return -1.0  # "A-line", "Party A", "T-state"
    if len(parts) == 1:
        return zipf_frequency(parts[0], "en")
    return min(zipf_frequency(p, "en") for p in parts) - 1.5


def main():
    en_folder, collins_folder, knwiki, work = sys.argv[1:5]
    collins = {w.lower() for w, _ in read_stardict(collins_folder, "CollinsKannada")}
    labels = {w.lower() for d in DOMAINS.values() for w in d["wikt"]}

    index = wk.read_index(en_folder, "en-en")
    words = {w for w, _, _ in index}
    json.dump(sorted(words), open(f"{work}/wikt_words.json", "w"))
    dic = open(f"{en_folder}/en-en.dict", "rb")
    cache = f"{work}/topic_found_raw.json"
    found = {}
    if os.path.exists(cache):
        found = json.load(open(cache))
        index = []  # scanned before: the labelled meanings are in the cache
    for word, off, size in index:
        if word.lower() in collins or not re.fullmatch(r"[A-Za-z][A-Za-z' -]*", word) or len(word) > 40:
            continue
        dic.seek(off)
        raw = dic.read(size).decode("utf-8")
        tags = {wk.text(m).lower() for m in LABEL_RX.findall(raw)}
        if not any(l.strip() in labels for t in tags for l in re.split(r"[,;]", t)):
            continue
        for b in wk.parse(raw):
            for s in b["senses"]:
                if wk.SKIP_LABELS.search(s["label"]) or not s["label"]:
                    continue
                s["examples"] = s["examples"][:1]
                found.setdefault(word, []).append({"pos": b["pos"], **s})
    if index:
        json.dump(found, open(cache, "w"), ensure_ascii=False)
    # Classify with the current subject rules: a word takes the subject of its
    # first labelled meaning, and keeps up to three meanings of that subject.
    classified = {}
    for word, senses in found.items():
        if not looks_like_term(word):
            continue
        for s in senses:
            d = domain_of_label(s["label"])
            if not d:
                continue
            if d == "genz" and "slang" == s["label"].lower().strip() and zipf_frequency(word.lower(), "en") < 3:
                continue  # plain old slang only when it is common
            e = classified.setdefault(word, {"domain": d, "blocks": {}})
            if e["domain"] == d and sum(len(v) for v in e["blocks"].values()) < 3:
                e["blocks"].setdefault(s["pos"], []).append({k: s[k] for k in ("text", "label", "examples")})
    found = classified
    # A common word belongs to a subject only if that is its first meaning:
    # "John" or "acquired" have a labelled minor sense, "radio-" is a prefix.
    full_index = {w: (o, n) for w, o, n in wk.read_index(en_folder, "en-en")}

    def primary_domain(word):
        o, n = full_index[word]
        dic.seek(o)
        blocks = wk.parse(dic.read(n).decode("utf-8"))
        if not blocks or not blocks[0]["senses"] or blocks[0]["pos"] == "Proper noun":
            return None
        if word[:1].isupper() and not word.isupper() and word not in ("iOS",):
            return None  # "John", "Andy", "Moscow"
        if word.isupper() and len(word) > 4:
            return None  # "HAROLD", "ALICE", "LUCAS": acronyms that are mostly names
        if word.islower() and zipf_frequency(word.capitalize(), "en") > zipf_frequency(word, "en") + 0.5:
            return None  # "morgan", "helen": mostly a name
        return domain_of_label(blocks[0]["senses"][0]["label"])

    chosen = {}
    for name in DOMAINS:
        cands = [(score(w), w) for w, e in found.items() if e["domain"] == name and not w.startswith("-")
                 and not w.endswith("-")]
        cands = [c for c in cands if c[0] >= MIN_ZIPF.get(name, 1.5)]
        cands = [c for c in cands if c[0] < 3.0 or primary_domain(c[1]) == name]
        for z, w in sorted(cands, reverse=True)[:PER_DOMAIN]:
            e = found[w]
            chosen[w] = {"domain": name, "zipf": round(z, 2),
                         "blocks": [{"pos": p, "senses": s} for p, s in e["blocks"].items()]}
        print(f"  Wiktionary {name}: {len(cands)} candidates, kept {min(len(cands), PER_DOMAIN)}")
    json.dump(chosen, open(f"{work}/topic_wikt.json", "w"), ensure_ascii=False)

    cats = json.load(open(f"{knwiki}/kn_categories.json"))
    pairs = json.load(open(f"{knwiki}/kn_en_titles.json"))
    lower_words = {w.lower() for w in words} | words
    items = []
    for kn, cs in cats.items():
        d = domain_of_categories(cs)
        en = pairs.get(kn, "")
        if d and en and is_term(en, d, lower_words):
            items.append({"kn": re.sub(r"\s*\([^)]*\)$", "", kn), "kn_title": kn, "en_title": en,
                          "en": re.sub(r"\s*\([^)]*\)$", "", en), "domain": d})
    json.dump(items, open(f"{work}/topic_knwiki.json", "w"), ensure_ascii=False)
    from collections import Counter
    print("  Kannada Wikipedia:", dict(Counter(i["domain"] for i in items)))


if __name__ == "__main__":
    main()
