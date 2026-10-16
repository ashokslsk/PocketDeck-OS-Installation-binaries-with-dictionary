"""Pick what the two Wiktionary dictionaries add, and the strings to translate.

usage: wikt_prepare.py KN_EN_FOLDER EN_EN_FOLDER COLLINS_KANNADA_FOLDER WORK_DIR [TOP_N]

Kannada-English Wiktionary -> KannadaEnglish:
  wikt_kn.json        headword -> parts of speech, meanings, examples
  wikt_kn_forms.json  inflected form (from its declension tables) -> headword
English Wiktionary -> CollinsKannada, for the TOP_N commonest English words
(wordfreq) that Collins lacks:
  wikt_en_aliases.json  form -> Collins headword, when Wiktionary says the word
                        is a form of a Collins word (worked -> work)
  wikt_en.json          new words: up to three meanings, one example each
mt_wikt.jsonl         English strings to translate into Kannada
"""
import json
import re
import sys

from wordfreq import top_n_list

import wiktionary as wk
from collins import read_stardict

KN = re.compile(r"[ಀ-೿]")


def load_entries(folder, stem):
    """lower-case headword -> [(headword, blocks)] (one per part-of-speech entry)."""
    dic = open(f"{folder}/{stem}.dict", "rb")
    index = wk.read_index(folder, stem)
    return index, dic


def main():
    kn_folder, en_folder, collins_folder, work = sys.argv[1:5]
    top_n = int(sys.argv[5]) if len(sys.argv) > 5 else 60000
    strings = []

    # --- Kannada-English -------------------------------------------------
    index, dic = load_entries(kn_folder, "kn-en")
    kn_entries = {}
    for word, off, size in index:
        if word.startswith("-") or len(word) < 2 or not KN.search(word):
            continue  # suffixes and single letters cannot be tapped in a book
        dic.seek(off)
        blocks = wk.parse(dic.read(size).decode("utf-8"))
        if blocks:
            kn_entries.setdefault(word, []).extend(blocks)
    forms = {}
    for form, ordinal in wk.read_syn(kn_folder, "kn-en"):
        head = index[ordinal][0] if ordinal < len(index) else ""
        if head in kn_entries and form != head and re.fullmatch(r"[ಀ-೿‌‍]+", form):
            forms.setdefault(form, head)
    for blocks in kn_entries.values():
        for b in blocks:
            strings += [s["text"] for s in b["senses"]]
    json.dump(kn_entries, open(f"{work}/wikt_kn.json", "w"), ensure_ascii=False)
    json.dump(forms, open(f"{work}/wikt_kn_forms.json", "w"), ensure_ascii=False)
    print(f"Kannada: {len(kn_entries)} headwords, {len(forms)} forms")

    # --- English -------------------------------------------------------------
    collins_keys = [w for w, _ in read_stardict(collins_folder, "CollinsKannada")]
    collins_lower = {}
    for w in collins_keys:
        collins_lower.setdefault(w.lower(), w)
    collins_syn = {f.lower() for f, _ in wk.read_syn(collins_folder, "CollinsKannada")}
    known = set(collins_lower) | collins_syn

    index, dic = load_entries(en_folder, "en-en")
    by_word = {}
    for i, (word, off, size) in enumerate(index):
        by_word.setdefault(word, []).append(i)
    lemma_of = {}
    for form, ordinal in wk.read_syn(en_folder, "en-en"):
        if ordinal < len(index):
            lemma_of.setdefault(form, []).append(index[ordinal][0])

    aliases, en_entries = {}, {}
    for word in top_n_list("en", top_n):
        if not re.fullmatch(r"[a-z][a-z'-]+", word) or word in known:
            continue
        lemma = next((l for l in lemma_of.get(word, []) if l.lower() in collins_lower), None)
        if lemma and (len(word) < 3 or word.capitalize() in by_word):
            continue  # "ch" -> chain, "holden" -> hold: abbreviations and names
        if lemma:
            aliases[word] = collins_lower[lemma.lower()]
            continue
        if word not in by_word or word.capitalize() in by_word:
            continue  # unknown, or a name (john -> John) whose lower-case entry would mislead
        blocks = []
        for i in by_word[word]:
            dic.seek(index[i][1])
            blocks += wk.parse(dic.read(index[i][2]).decode("utf-8"))
        kept, total = [], 0
        for b in blocks:
            senses = [s for s in b["senses"] if not wk.SKIP_LABELS.search(s["label"])]
            senses = senses[: max(0, 3 - total)]
            if senses:
                for s in senses:
                    s["examples"] = s["examples"][:1]
                kept.append({"pos": b["pos"], "senses": senses})
                total += len(senses)
        if kept:
            en_entries[word] = kept
            for b in kept:
                for s in b["senses"]:
                    strings.append(s["text"])
                    strings += [e["text"] for e in s["examples"]]
    json.dump(aliases, open(f"{work}/wikt_en_aliases.json", "w"), ensure_ascii=False)
    json.dump(en_entries, open(f"{work}/wikt_en.json", "w"), ensure_ascii=False)
    print(f"English: {len(en_entries)} new words, {len(aliases)} forms of Collins words")

    seen = set()
    with open(f"{work}/mt_wikt.jsonl", "w") as f:
        for s in strings:
            if s and s not in seen and re.search(r"[A-Za-z]{2}", s):
                seen.add(s)
                f.write(json.dumps({"t": s}) + "\n")
    print(f"{len(seen)} strings to translate")


if __name__ == "__main__":
    main()
