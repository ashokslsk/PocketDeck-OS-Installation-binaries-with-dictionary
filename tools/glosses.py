"""Short Kannada equivalents for Collins headwords (shown as "ಕನ್ನಡ: ...").

Candidates come from the Alar Kannada-English dictionary (V. Krishna, ODC-ODbL):
a Kannada word is a candidate for an English headword when one of its English
senses is exactly that word. Alar has many old or rare words, so a candidate
is kept only when its stem appears in the Kannada translations of that
headword's own meanings and examples (kn.jsonl), and candidates are ranked by
how many of those translations use it. That picks the everyday word.
The headword translated on its own (heads_kn.jsonl, "to abandon" for verbs,
turned into the verb root: ತ್ಯಜಿಸಲು -> ತ್ಯಜಿಸು) comes first when it is short.

usage: glosses.py COLLINS_FOLDER alar.yml kn.jsonl heads.jsonl heads_kn.jsonl OUT.json
"""
import json
import os
import re
import sys
from collections import defaultdict

import yaml

from collins import classify, read_stardict

KN = re.compile(r"^[ಀ-೿]+$")
ARCHAIC = re.compile(r"[ಱೞ]")  # ಱ ೞ: Old Kannada letters
VOWEL_SIGNS = "ಾಿೀುೂೃೄೆೇೈೊೋೌ"


def stem(word):
    """Drop a final vowel sign so inflected forms match: ಕಣ್ಣು -> ಕಣ್ಣ (ಕಣ್ಣಿನ)."""
    return word[:-1] if len(word) > 2 and word[-1] in VOWEL_SIGNS else word


def aksharas(word):
    """Syllable count: letters not joined to the previous one by a virama, and
    not a dead consonant at the end (\u0C92\u0CB3\u0CCD is one syllable)."""
    n = 0
    for i, ch in enumerate(word):
        if ("\u0C85" <= ch <= "\u0C94" or "\u0C95" <= ch <= "\u0CB9") and not (i and word[i - 1] == "\u0CCD"):
            if not (i + 2 == len(word) and word[-1] == "\u0CCD"):
                n += 1
    return n


def head_gloss(english, kannada):
    """A short gloss from the headword's own translation, or None."""
    words = re.findall(r"[\u0C80-\u0CFF\u200C\u200D]+", kannada)
    if not words or len(words) > 3 or re.search(r"[A-Za-z]", kannada):
        return None
    text = " ".join(words)
    if english.startswith("to ") and len(words) == 1 and text.endswith("\u0CB2\u0CC1") and len(text) > 3:
        text = text[:-2] + "\u0CC1"  # infinitive ...ಲು -> root ...ು
    return text


def main():
    folder, alar_path, kn_path, prompts_path, heads_path, out = sys.argv[1:7]
    kn = {}
    for line in open(kn_path):
        try:
            d = json.loads(line)
            kn[d["t"]] = d["kn"]
        except (ValueError, KeyError):
            pass

    # Kannada text of each headword's own meanings and examples.
    heads = defaultdict(list)
    for w, body in read_stardict(folder, "Collins5"):
        base = re.sub(r"\(\d\)$", "", w).lower()
        for line in body.split("<br>"):
            kind, text = classify(line.replace("<hr>", ""))
            if kind and text in kn:
                heads[base].append(kn[text])
        heads.setdefault(base, [])

    try:
        loader = yaml.CSafeLoader
    except AttributeError:
        loader = yaml.SafeLoader
    cand = defaultdict(set)
    for e in yaml.load(open(alar_path), Loader=loader):
        word = (e.get("entry") or "").strip()
        if not KN.match(word) or ARCHAIC.search(word) or aksharas(word) < 2 or len(word) > 12:
            continue
        for d in e.get("defs") or []:
            text = re.sub(r"\([^)]*\)", "", d.get("entry") or "")
            if re.search(r"[ಀ-೿]", text):
                continue
            for part in re.split(r"[;,]", text):
                p = part.strip(" .:'\"").lower()
                p = re.sub(r"^(to|a|an|the) ", "", p)
                if p in heads:
                    cand[p].add(word)

    result = {}
    for head, words in cand.items():
        tokens = [t for text in heads[head] for t in re.findall(r"[\u0C80-\u0CFF]+", text)]
        if not tokens:
            continue
        hits = {}
        for w in words:
            s = stem(w)
            # A token starting with the whole word counts double (ಮನೆ in ಮನೆಯಲ್ಲಿ);
            # one starting with just the stem may be another word (ಮನ in ಮನಸ್ಸು).
            n = sum(2 if t.startswith(w) else 1 for t in tokens if t.startswith(s))
            if n:
                hits[w] = n
        if not hits:
            continue
        best = max(hits.values())
        keep = []
        for w in sorted(hits, key=lambda w: (-hits[w], -len(w))):
            if hits[w] < max(1, best // 4):
                break
            # ಪುಸ್ತ and ಪುಸ್ತಕ match the same words: keep only the full form.
            related = [k for k in keep if k.startswith(stem(w)) or w.startswith(stem(k))]
            if related:
                if len(w) > len(related[0]) and hits[w] * 5 >= hits[related[0]] * 4:
                    keep[keep.index(related[0])] = w
                continue
            keep.append(w)
            if len(keep) == 2:
                break
        result[head] = keep

    prompt_word = {}
    if os.path.exists(prompts_path):
        for line in open(prompts_path):
            d = json.loads(line)
            prompt_word[d["t"]] = d["w"]
    heads_kn = {}
    if os.path.exists(heads_path):
        for line in open(heads_path):
            try:
                d = json.loads(line)
                heads_kn[d["t"]] = d["kn"]
            except (ValueError, KeyError):
                pass
    for prompt, kannada in heads_kn.items():
        g = head_gloss(prompt, kannada)
        if not g:
            continue
        head = prompt_word.get(prompt)
        if head is None:
            continue
        # A word translated on its own may take the wrong sense (appellation ->
        # ಮೇಲ್ಮನವಿ, "appeal") or just be spelt out (chubby -> ಚಬ್ಬಿ): keep it only
        # if the translations of the word's own meanings and examples use it too.
        tokens = [t for text in heads.get(head, []) for t in re.findall(r"[\u0C80-\u0CFF]+", text)]
        if not all(any(t.startswith(stem(w)) for t in tokens) for w in g.split()):
            continue
        rest = [w for w in result.get(head, []) if w != g and not g.startswith(stem(w))]
        result[head] = [g] + rest
    json.dump(result, open(out, "w"), ensure_ascii=False, indent=0)
    print(len(result), "of", len(heads), "headwords have Kannada equivalents")
    for w in ["abandon", "beautiful", "run", "house", "happy", "be", "certain", "book", "water", "love", "time"]:
        print(" ", w, result.get(w))


if __name__ == "__main__":
    main()
