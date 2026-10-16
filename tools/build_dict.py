"""Write the English-Kannada Collins StarDict dictionary.

usage: build_dict.py COLLINS_FOLDER kn.jsonl[,kn_better.jsonl] glosses.json OUT_FOLDER [wikt_en.json wikt_en_aliases.json]
(with several translation files, a later file's translation wins)

Every Collins entry keeps its original text. Added in Kannada:
  - after the headword line: short Kannada equivalents (ಕನ್ನಡ: ...)
  - after each meaning: the meaning in Kannada (ಅರ್ಥ: ...)
  - after each example sentence: the sentence in Kannada
Words with no translation yet are kept exactly as in Collins.
"""
import html
import json
import os
import re
import struct
import sys

from collins import classify, clean_kannada, frequency, read_stardict

STEM = "CollinsKannada"
BOOKNAME = "Collins COBUILD English-Kannada"


def main():
    src, kn_path, gloss_path, out = sys.argv[1:5]
    wikt = json.load(open(sys.argv[5])) if len(sys.argv) > 5 and os.path.exists(sys.argv[5]) else {}
    wikt_aliases = json.load(open(sys.argv[6])) if len(sys.argv) > 6 and os.path.exists(sys.argv[6]) else {}
    extra = json.load(open(sys.argv[7])) if len(sys.argv) > 7 and os.path.exists(sys.argv[7]) else {}
    kn = {}
    for path in kn_path.split(","):
        if not os.path.exists(path):
            continue
        with open(path) as f:
            for line in f:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if d.get("kn"):
                    kn[d["t"]] = clean_kannada(d["kn"])
    glosses = json.load(open(gloss_path)) if os.path.exists(gloss_path) else {}

    entries = read_stardict(src, "Collins5")
    stats = {"entries": 0, "with_kannada": 0, "defs": 0, "defs_kn": 0, "ex": 0, "ex_kn": 0, "gloss": 0, "merged": 0, "wiktionary": 0,
             "topic_added_to_existing": 0, "topic_new": 0}

    def augment(word, body):
        base = re.sub(r"\(\d\)$", "", word).lower()
        gloss = glosses.get(base) if not word.endswith(("(2)", "(3)", "(4)")) else None
        added = False
        outl = []
        for n, line in enumerate(body.split("<br>")):
            outl.append(line)
            if n == 0 and gloss:
                outl.append("ಕನ್ನಡ: " + html.escape(clean_kannada(", ".join(gloss))))
                stats["gloss"] += 1
                added = True
            kind, text = classify(line.replace("<hr>", ""))
            if not kind:
                continue
            stats["defs" if kind == "def" else "ex"] += 1
            k = kn.get(text)
            if not k:
                continue
            tail = ""
            if line.endswith("<hr>"):  # keep the entry separator after the added line
                outl[-1] = line[: -len("<hr>")]
                tail = "<hr>"
            if kind == "def":
                # A plain label: the device drops the space after a bold run before Kannada.
                outl.append("  ಅರ್ಥ: " + html.escape(k) + tail)
            else:
                # Indented on its own line under the English example.
                outl[-1] += "<blockquote>" + html.escape(k) + "</blockquote>" + tail
            stats["defs_kn" if kind == "def" else "ex_kn"] += 1
            added = True
        stats["entries"] += 1
        stats["with_kannada"] += added
        return "<br>".join(outl)

    words = [(w, augment(w, b)) for w, b in entries]
    # Collins splits some words into be(1), be(2)...; add a plain "be" holding all
    # of them so a lookup goes straight to the definition.
    groups = {}
    for i, (w, _) in enumerate(words):
        m = re.match(r"^(.*)\((\d)\)$", w)
        if m:
            groups.setdefault(m.group(1), []).append(i)
    present = {w for w, _ in words}
    for base, ids in groups.items():
        if base not in present:
            words.append((base, "".join(words[i][1] for i in ids)))
            stats["merged"] += 1
    # Common English words Collins lacks, from English Wiktionary (CC BY-SA 4.0).
    present = {w.lower() for w, _ in words}
    for word, blocks in sorted(wikt.items()):
        if word in present:
            continue
        lines, n = [f'<b>{html.escape(word)}</b> <FONT COLOR="#909090">(Wiktionary)</FONT>'], 0
        many = sum(len(b["senses"]) for b in blocks) > 1
        for b in blocks:
            for sense in b["senses"]:
                n += 1
                lines.append((f"<b>{n}</b> " if many else "") + f'<FONT COLOR="#007000">[{html.escape(b["pos"].upper())}]</FONT>')
                lines.append("  " + (f'({html.escape(sense["label"])}) ' if sense["label"] else "") + html.escape(sense["text"]))
                if kn.get(sense["text"]):
                    lines.append("  ಅರ್ಥ: " + html.escape(kn[sense["text"]]))
                for ex in sense["examples"]:
                    line = f'  ● <font color="#004080"><i>{html.escape(ex["text"])}</i></font>'
                    if kn.get(ex["text"]):
                        line += "<blockquote>" + html.escape(kn[ex["text"]]) + "</blockquote>"
                    lines.append(line)
        words.append((word, "<br>".join(lines) + "<hr>"))
        stats["wiktionary"] += 1

    # Subject vocabulary (topic_build.py): add to the entry with that headword,
    # or make a new entry.
    by_exact = {w: i for i, (w, _) in enumerate(words)}
    by_lower = {}
    for i, (w, _) in enumerate(words):
        by_lower.setdefault(w.lower(), i)
    for word, sections in sorted(extra.items()):
        block = "<hr>".join(sections) + "<hr>"
        i = by_exact.get(word, by_lower.get(word.lower()))
        if i is not None:
            words[i] = (words[i][0], words[i][1] + block)
            stats["topic_added_to_existing"] += 1
        else:
            words.append((word, block))
            by_exact[word] = len(words) - 1
            by_lower.setdefault(word.lower(), len(words) - 1)
            stats["topic_new"] += 1

    syn_in = open(f"{src}/Collins5.syn", "rb").read()
    syn_words = {m.decode("utf-8").lower() for m in re.findall(rb"([^\x00]+)\x00.{4}", syn_in, re.S)}

    # Forms Collins lists with a headword, "(reparations)", "(abandons abandoning
    # abandoned)", and derived words inside an entry ("■ beautifully" under
    # beautiful), open that entry directly: a word tapped in a book is often one.
    known = {w.lower() for w, _ in words} | syn_words
    aliases = {}
    by_freq = sorted(range(len(entries)), key=lambda i: -frequency(entries[i][1]))
    for i in by_freq:
        body = entries[i][1]
        found = [f for m in re.findall(r"<b>\(([^)<]*)\)</b>", body.split("<br>")[0]) for f in re.split(r"[\s,]+", m)]
        found += re.findall(r'■ <FONT COLOR="#000090"><b>([^<]+)</b>', body)
        for f in found:
            f = f.strip()
            if re.fullmatch(r"[A-Za-z][A-Za-z' -]*", f) and f.lower() not in known and f not in aliases:
                aliases[f] = i  # the commonest entry wins: "leaves" -> leave before leaf
    # Forms English Wiktionary gives for Collins words (analyzed -> analyze).
    position = {w: i for i, (w, _) in enumerate(words)}
    for form, lemma in wikt_aliases.items():
        if form.lower() not in known and form not in aliases and lemma in position:
            aliases[form] = position[lemma]
    # A form of a cross-reference stub ("analyze: see analyse") opens the full entry.
    for form, i in list(aliases.items()):
        body = words[i][1]
        link = re.findall(r'bword://([^"]+)"', body)
        if len(link) == 1 and len(re.sub(r"<[^>]+>", "", body)) < 160 and link[0] in position:
            aliases[form] = position[link[0]]
    stats["forms"] = len(aliases)

    keys = [(w, i) for i, (w, _) in enumerate(words)] + list(aliases.items())
    keys.sort(key=lambda k: (k[0].encode().lower(), k[0].encode()))
    new_index = {}
    for n, (w, i) in enumerate(keys):
        if words[i][0] == w:
            new_index[i] = n

    idx = bytearray()
    dic = bytearray()
    where = {}
    for i in sorted(new_index, key=new_index.get):
        data = words[i][1].encode("utf-8")
        where[i] = (len(dic), len(data))
        dic += data
    for w, i in keys:
        idx += w.encode("utf-8") + b"\0" + struct.pack(">II", *where[i])

    syn = bytearray()
    syn_count = 0
    p = 0
    while p < len(syn_in):
        z = syn_in.index(b"\0", p)
        target = struct.unpack(">I", syn_in[z + 1 : z + 5])[0]
        syn += syn_in[p : z + 1] + struct.pack(">I", new_index[target])
        syn_count += 1
        p = z + 5
    os.makedirs(out, exist_ok=True)
    open(f"{out}/{STEM}.idx", "wb").write(idx)
    open(f"{out}/{STEM}.dict", "wb").write(dic)
    open(f"{out}/{STEM}.syn", "wb").write(syn)
    with open(f"{out}/{STEM}.ifo", "w", encoding="utf-8") as f:
        f.write("StarDict's dict ifo file\nversion=2.4.2\n")
        f.write(f"wordcount={len(keys)}\nsynwordcount={syn_count}\nidxfilesize={len(idx)}\n")
        f.write(f"bookname={BOOKNAME}\nlang=en-kn\nauthor=HarperCollins Publishers; Kannada by IndicTrans2 (AI4Bharat) and Alar (V. Krishna)\n")
        f.write(
            "description=Collins COBUILD Advanced Learner's Dictionary with Kannada equivalents, "
            "meanings and example translations (machine translated).\n"
        )
        f.write("sametypesequence=h\n")
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
