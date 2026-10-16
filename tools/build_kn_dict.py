"""Write the Kannada-English StarDict dictionary.

usage: build_kn_dict.py keed.jsonl senses_kn.jsonl[,more.jsonl] COLLINS_FOLDER kn.jsonl[,more.jsonl] glosses.json
                        wikt_kn.json wikt_kn_forms.json OUT_FOLDER [extra_kn.json]

Headwords are Kannada. Each entry has, when available:
  - the Kannada-English Etymological Dictionary (KEED) entry: transliteration,
    part of speech, numbered English meanings each followed by the meaning in
    Kannada (machine translated), the book's own Kannada examples with English;
  - "Wiktionary": the Kannada-English Wiktionary entry (CC BY-SA 4.0), its
    meanings in English and Kannada and its examples in both languages;
  - "Collins": English words whose Kannada equivalent is this word, with the
    Collins meaning that uses it, in English and Kannada, and an example in both.
Inflected forms from Wiktionary's declension tables, and those seen in the
Kannada text (ಮನೆಯಲ್ಲಿ, ಮನೆಗೆ), are added as extra index entries that open the
same definition, so a word tapped in a book is found.
"""
import html
import json
import os
import re
import struct
import sys
from collections import Counter, defaultdict

from collins import classify, clean_kannada, frequency, read_stardict
from keed_mt_input import kannada_meaning, label_of, mt_text

STEM = "KannadaEnglish"
BOOKNAME = "Kannada-English (KEED + Wiktionary + Collins)"
KN_WORD = re.compile(r"[ಀ-೿‌‍]+")
VOWEL_SIGNS = "ಾಿೀುೂೃೄೆೇೈೊೋೌ"
STATUS_KN = {"obsolete": "ಪ್ರಾಚೀನ", "literary": "ಸಾಹಿತ್ಯಿಕ", "regional": "ಪ್ರಾದೇಶಿಕ", "highly literary": "ಕಾವ್ಯ",
             "variant spelling": "ರೂಪಾಂತರ", "uncommon": "ವಿರಳ", "colloquial": "ಆಡುಮಾತು", "doubtful": "ಸಂದೇಹಾಸ್ಪದ"}
def E(text):
    return html.escape(text, quote=False)


def stem(word):
    return word[:-1] if len(word) > 2 and word[-1] in VOWEL_SIGNS else word


def load_kn(paths):
    kn = {}
    for path in paths.split(","):
        if os.path.exists(path):
            for line in open(path):
                try:
                    d = json.loads(line)
                    if d.get("kn"):
                        kn[d["t"]] = clean_kannada(d["kn"])
                except ValueError:
                    pass
    return kn


def collins_senses(body, kn):
    """[(pos, definition, kannada definition, [(example, kannada example)])] of one Collins entry."""
    senses, pos = [], ""
    for line in body.split("<br>"):
        tag = re.search(r'<FONT COLOR="#007000">\[([^\]]+)\]', line)
        if tag:
            pos = tag.group(1)
        kind, text = classify(line.replace("<hr>", ""))
        if kind == "def":
            senses.append([pos, text, kn.get(text, ""), []])
        elif kind == "ex" and senses:
            senses[-1][3].append((text, kn.get(text, "")))
    return senses


def keed_html(entries, senses_kn):
    out = []
    for e in entries:
        head = f'<b>{E(e["kn"])}</b> <i>{E(e["tr"])}</i>'
        if e["pos"]:
            head += f' <FONT COLOR="#007000">{E(e["pos"])}</FONT>'
        if e["status"]:
            head += " (" + ", ".join(f'{STATUS_KN.get(s, s)} / {s}' for s in e["status"]) + ")"
        out.append(head)
        if e.get("variants"):
            out.append("ರೂಪಾಂತರ / also: " + E(", ".join(e["variants"])))
        many = len(e["senses"]) > 1
        for n, s in enumerate(e["senses"], 1):
            line = (f"<b>{n}</b> " if many else "") + (f'({E(s["pos"])}) ' if s.get("pos") else "")
            line += ("(lit.) " if s["lit"] else "") + E(s["en"])
            out.append(line)
            k = kannada_meaning(senses_kn.get(mt_text(s["en"], s.get("pos") or e["pos"]), ""))
            if k and KN_WORD.search(k):  # "pl." comes back unchanged
                label = label_of(s["en"])
                out.append("  ಅರ್ಥ: " + (f"({label}) " if label else "") + E(k))
        for ex in e["examples"]:
            out.append(f'  • {E(ex["kn"])}<blockquote><i>{E(ex["en"])}</i></blockquote>')
        if e["see"]:
            out.append("ನೋಡಿ / see: " + E("; ".join(e["see"])))
        if e["origin"] and e["origin"] != "Kannada":
            out.append(f'<FONT COLOR="#909090">ಮೂಲ / origin: {E(e["origin"])}</FONT>')
    return "<br>".join(out)


def wikt_html(blocks, kn):
    """The Kannada-English Wiktionary entry: meanings in English and Kannada, examples in both."""
    out = ["<b>Wiktionary</b>"]
    n = 0
    many = sum(len(b["senses"]) for b in blocks) > 1
    for b in blocks:
        out.append((f'<i>{E(b["tr"])}</i> ' if b["tr"] else "") + f'<FONT COLOR="#007000">{E(b["pos"])}</FONT>')
        for s in b["senses"]:
            n += 1
            out.append((f"<b>{n}</b> " if many else "") + (f'({E(s["label"])}) ' if s["label"] else "") + E(s["text"]))
            k = kn.get(s["text"], "")
            if k and KN_WORD.search(k):
                out.append("  ಅರ್ಥ: " + E(k))
            for ex in s["examples"]:
                line = f'  • {E(ex["text"])}'
                if ex["en"]:
                    line += f'<blockquote><i>{E(ex["en"])}</i></blockquote>'
                out.append(line)
    return "<br>".join(out)


def collins_html(word, english, collins, kn):
    """Collins senses whose Kannada uses `word`, for each English headword that has it as an equivalent."""
    s = stem(word)
    blocks = []
    for eng in english[:4]:
        senses = collins.get(eng) or []
        uses = [x for x in senses if s in x[2] or any(s in k for _, k in x[3])]
        chosen = (uses or senses)[:2]
        if not chosen:
            continue
        lines = [f"<b>{E(eng)}</b>"]
        for pos, en_def, kn_def, exs in chosen:
            lines.append((f'<FONT COLOR="#007000">[{E(pos)}]</FONT> ' if pos else "") + E(en_def))
            if kn_def:
                lines.append("  ಅರ್ಥ: " + E(kn_def))
            ex = next(((a, b) for a, b in exs if s in b), exs[0] if exs else None)
            if ex:
                lines.append(f"  • <i>{E(ex[0])}</i>" + (f"<blockquote>{E(ex[1])}</blockquote>" if ex[1] else ""))
        blocks.append("<br>".join(lines))
    if not blocks:
        return ""
    return "<b>Collins</b> — ಇಂಗ್ಲಿಷ್ ಪದಗಳು / English words<br>" + "<br>".join(blocks)


def inflections(headwords, texts):
    """Kannada word forms in the text that are a headword plus a common ending."""
    by_stem = defaultdict(list)
    for h in headwords:
        if len(h) >= 2:
            by_stem[stem(h)].append(h)
    max_len = max(map(len, headwords))
    tokens = Counter(t for text in texts for t in KN_WORD.findall(text))
    for hs in by_stem.values():  # ನೀರಿನ: ನೀರು (common) rather than ನೀರೆ
        hs.sort(key=lambda h: -tokens[h])
    def candidates(t):
        """(headword, ending), longest first: the whole headword at the start
        (ಎಲೆ + ಯ, not ಎಲೊ), else its stem for endings that replace the last
        vowel (ಕಣ್ಣು -> ಕಣ್ಣ + ಿನ). "~" marks a stem ending."""
        for n in range(min(len(t) - 1, max_len), 1, -1):
            if t[:n] in headwords:
                yield t[:n], t[n:]
            if t[:n] in by_stem:
                yield by_stem[t[:n]][0], "~" + t[n:]

    forms = [t for t in tokens if t not in headwords]
    # A real ending recurs with many different words: count the longest match of each form.
    endings = Counter(next(candidates(t), (None, None))[1] for t in forms)
    common = {end for end, c in endings.items() if end and c >= 40 and len(end) <= 9}
    result = {}
    for t in forms:
        for h, end in candidates(t):
            if end in common:
                result[t] = h
                break
    return result, common


def main():
    keed_path, senses_path, collins_folder, kn_paths, gloss_path, wikt_path, wikt_forms_path, out = sys.argv[1:9]
    extra = json.load(open(sys.argv[9])) if len(sys.argv) > 9 and os.path.exists(sys.argv[9]) else {}
    wikt = json.load(open(wikt_path)) if os.path.exists(wikt_path) else {}
    wikt_forms = json.load(open(wikt_forms_path)) if os.path.exists(wikt_forms_path) else {}
    keed = defaultdict(list)
    for line in open(keed_path):
        e = json.loads(line)
        keed[e["kn"]].append(e)
    senses_kn = load_kn(senses_path)
    kn = load_kn(kn_paths)

    # Collins: English headword -> senses; Kannada equivalent -> English headwords.
    collins, freq = {}, Counter()
    for w, body in read_stardict(collins_folder, "Collins5"):
        base = re.sub(r"\(\d\)$", "", w).lower()
        collins.setdefault(base, []).extend(collins_senses(body, kn))
        freq[base] = max(freq[base], frequency(body))
    # Kannada word -> English headwords, best first: those whose first equivalent
    # it is (water -> ನೀರು before bath -> ಸ್ನಾನ, ನೀರು), then the commoner English word.
    ranked = defaultdict(list)
    for eng, kws in json.load(open(gloss_path)).items():
        for i, k in enumerate(kws):
            ranked[clean_kannada(k)].append((i, -freq[eng], len(eng), eng))
    reverse = {k: [e for *_, e in sorted(v)] for k, v in ranked.items()}

    words = {}
    stats = Counter()
    for k in sorted(set(keed) | set(reverse) | set(wikt)):
        parts = []
        if k in keed:
            parts.append(keed_html(keed[k], senses_kn))
            stats["keed"] += 1
        if k in wikt:
            if k not in keed:
                parts.append(f"<b>{E(k)}</b>")
            parts.append(wikt_html(wikt[k], senses_kn))
            stats["wiktionary"] += 1
        if k in reverse:
            c = collins_html(k, reverse[k], collins, kn)
            if c:
                parts.append(c)
                stats["collins"] += 1
        if parts:
            if k not in keed and k not in wikt:
                parts.insert(0, f"<b>{E(k)}</b> — " + E(", ".join(reverse[k][:6])))
            words[k] = "<hr>".join(parts) + "<hr>"

    # Subject vocabulary (topic_build.py): add to the entry, or make a new one.
    for k, sections in sorted(extra.items()):
        block = "<hr>".join(sections) + "<hr>"
        if k in words:
            words[k] += block
            stats["topic_added_to_existing"] += 1
        else:
            words[k] = block
            stats["topic_new"] += 1

    # Word forms from the Kannada text: KEED examples and the Collins translations.
    texts = list(kn.values()) + [x["kn"] for es in keed.values() for e in es for x in e["examples"]]
    forms, endings = inflections(set(words), texts)
    # Wiktionary's declension tables are written by people: they win over guesses.
    for form, head in wikt_forms.items():
        if form not in words and head in words:
            forms[form] = head
    stats["forms"] = len(forms)

    os.makedirs(out, exist_ok=True)
    keys = sorted(set(words) | set(forms), key=lambda w: (w.encode().lower(), w.encode()))
    idx, dic, where = bytearray(), bytearray(), {}
    for w in sorted(words, key=lambda w: (w.encode().lower(), w.encode())):
        data = words[w].encode("utf-8")
        where[w] = (len(dic), len(data))
        dic += data
    for w in keys:
        off, size = where[w] if w in words else where[forms[w]]
        idx += w.encode("utf-8") + b"\0" + struct.pack(">II", off, size)
    open(f"{out}/{STEM}.idx", "wb").write(idx)
    open(f"{out}/{STEM}.dict", "wb").write(dic)
    with open(f"{out}/{STEM}.ifo", "w", encoding="utf-8") as f:
        f.write("StarDict's dict ifo file\nversion=2.4.2\n")
        f.write(f"wordcount={len(keys)}\nidxfilesize={len(idx)}\n")
        f.write(f"bookname={BOOKNAME}\nlang=kn-en\n")
        f.write("author=N. Učida & B. B. Rajapurohit (KEED, CC BY-NC 4.0); Wiktionary (CC BY-SA 4.0); "
                "HarperCollins (Collins COBUILD); Kannada by IndicTrans2 (AI4Bharat)\n")
        f.write("description=Kannada headwords with English and Kannada meanings and examples in both languages.\n")
        f.write("sametypesequence=h\n")
    stats["headwords"] = len(words)
    stats["index_entries"] = len(keys)
    print(json.dumps(stats), "endings:", len(endings))


if __name__ == "__main__":
    main()
