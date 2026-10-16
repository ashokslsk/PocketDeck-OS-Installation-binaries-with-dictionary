"""Turn the subject vocabulary into dictionary sections for both dictionaries.

usage: topic_build.py WORK_DIR CURATED_DIR WIKT_WORDS.json

Writes WORK_DIR/extra_en.json and WORK_DIR/extra_kn.json: headword -> list of
HTML sections. build_dict.py / build_kn_dict.py add a section to the existing
entry for that headword, or make it a new entry. Sources:
  - curated lists (AI, Gen Z, Kannada slang, Kannada genres, Ayurveda), written by hand;
  - English Wiktionary subject words, Kannada by IndicTrans2; a Kannada
    headword only when the Kannada term translates back to the same English;
  - Kannada Wikipedia articles with an English twin: their opening sentences
    in both languages (written by people; machine translated only when the
    Kannada article has no opening text).
"""
import html
import json
import os
import re
import sys
from collections import Counter, defaultdict

from collins import clean_kannada
from domains import DOMAINS
from topic_mt_input import clean_lead, term_prompt

E = lambda t: html.escape(t, quote=False)  # noqa: E731
KN = re.compile(r"[ಀ-೿]")


def subject(domain):
    d = DOMAINS[domain]
    return f'{d["kn"]} / {domain.replace("_", " ").replace("genz", "youth slang").replace("ai", "AI")}'


def load(path):
    out = {}
    if os.path.exists(path):
        for line in open(path):
            try:
                d = json.loads(line)
                out[d["t"]] = clean_kannada(d["kn"]).strip()
            except (ValueError, KeyError):
                pass
    return out


def norm(text):
    text = text.lower().strip(" .!?,;:'\"")
    text = re.sub(r"^(a|an|the|to)\s+", "", text)
    text = re.sub(r"[-\s]+", " ", text)
    return re.sub(r"(ies|es|s)$", "", text)


def kannada_term(word, prompt, terms, back):
    """The Kannada for a subject word, if translating it back gives the same word."""
    kn = re.sub(r"^ಒಂದು\s+", "", terms.get(prompt, "")).strip(" .,")
    if not kn or not KN.search(kn) or len(kn.split()) > 4 or re.search(r"[A-Za-z]", kn):
        return None
    b = back.get(terms.get(prompt, "").strip(), "") or back.get(kn, "")
    if not b:
        return None
    nb, nw = norm(b), norm(word)
    if nb == nw or re.search(r"\b" + re.escape(nw) + r"\b", nb) and len(nb.split()) <= len(nw.split()) + 2:
        return kn
    return None


def en_sense_lines(n, pos, label, text, kn_text, examples, many):
    lines = [(f"<b>{n}</b> " if many else "") + f'<FONT COLOR="#007000">[{E(pos.upper())}]</FONT>',
             "  " + (f"({E(label)}) " if label else "") + E(text)]
    if kn_text:
        lines.append("  ಅರ್ಥ: " + E(kn_text))
    for ex, kn_ex in examples:
        line = f'  ● <font color="#004080"><i>{E(ex)}</i></font>'
        if kn_ex:
            line += f"<blockquote>{E(kn_ex)}</blockquote>"
        lines.append(line)
    return lines


def main():
    work, curated, wikt_words_path = sys.argv[1:4]
    wikt_words = set(json.load(open(wikt_words_path)))
    text_kn = load(f"{work}/kn_topic_text.jsonl")
    terms = load(f"{work}/kn_topic_terms.jsonl")
    back = {}
    for line in open(f"{work}/bt_topic_out.jsonl") if os.path.exists(f"{work}/bt_topic_out.jsonl") else []:
        d = json.loads(line)
        back[clean_kannada(d["t"]).strip()] = d["kn"]
    extra_en, extra_kn = defaultdict(list), defaultdict(list)
    stats = Counter()

    # 1. Curated English: AI and technology, Gen Z slang.
    for fname, domain in (("ai_en.json", "ai"), ("genz_en.json", "genz")):
        for e in json.load(open(f"{curated}/{fname}")):
            head = f'<b>{E(e["term"])}</b> <FONT COLOR="#909090">({subject(domain)})</FONT>'
            lines = [head, "ಕನ್ನಡ: " + E(e["kn_term"])]
            lines += en_sense_lines(1, e["pos"], "", e["en"], e["kn"], [(e["ex"], e["kn_ex"])], False)
            extra_en[e["term"]].append("<br>".join(lines))
            k = re.sub(r"\s*\([^)]*\)", "", e["kn_term"].split(",")[0]).strip()
            extra_kn[k].append("<br>".join([
                f'<b>{E(k)}</b> — <b>{E(e["term"])}</b> <FONT COLOR="#909090">({subject(domain)})</FONT>',
                E(e["kn"]), E(e["en"]),
                f'  • {E(e["kn_ex"])}<blockquote><i>{E(e["ex"])}</i></blockquote>']))
            stats[f"curated_{domain}"] += 1

    # 2. Curated Kannada: youth slang, literature and arts, Ayurveda and yoga.
    for fname, domain in (("kn_slang.json", "genz"), ("kn_genres.json", "kannada_genres"),
                          ("ayurveda.json", "ayurveda")):
        for e in json.load(open(f"{curated}/{fname}")):
            extra_kn[e["kn"]].append("<br>".join([
                f'<b>{E(e["kn"])}</b> <i>{E(e["tr"])}</i> <FONT COLOR="#007000">{E(e["pos"])}</FONT> '
                f'<FONT COLOR="#909090">({subject(domain)})</FONT>',
                "  ಅರ್ಥ: " + E(e["kn_def"]), E(e["en"]),
                f'  • {E(e["kn_ex"])}<blockquote><i>{E(e["en_ex"])}</i></blockquote>']))
            if e.get("en_term"):
                lines = [f'<b>{E(e["en_term"])}</b> <FONT COLOR="#909090">({subject(domain)})</FONT>',
                         "ಕನ್ನಡ: " + E(e["kn"])]
                lines += en_sense_lines(1, "noun", "", e["en"], e["kn_def"], [(e["en_ex"], e["kn_ex"])], False)
                extra_en[e["en_term"]].append("<br>".join(lines))
            stats[f"curated_{domain}"] += 1

    # 3. English Wiktionary subject words.
    topic = json.load(open(f"{work}/topic_wikt.json"))
    for word, e in topic.items():
        k = kannada_term(word, term_prompt(word, e["blocks"][0]["pos"]), terms, back)
        lines = [f'<b>{E(word)}</b> <FONT COLOR="#909090">(Wiktionary · {subject(e["domain"])})</FONT>']
        if k:
            lines.append("ಕನ್ನಡ: " + E(k))
        many = sum(len(b["senses"]) for b in e["blocks"]) > 1
        n = 0
        kn_lines = []
        for b in e["blocks"]:
            for s in b["senses"]:
                n += 1
                exs = [(x["text"], text_kn.get(x["text"], "")) for x in s["examples"]]
                lines += en_sense_lines(n, b["pos"], s["label"], s["text"], text_kn.get(s["text"], ""), exs, many)
                if text_kn.get(s["text"]):
                    kn_lines.append("  ಅರ್ಥ: " + E(text_kn[s["text"]]))
                kn_lines.append("  " + E(s["text"]))
                for ex, kn_ex in exs:
                    if kn_ex:
                        kn_lines.append(f"  • {E(kn_ex)}<blockquote><i>{E(ex)}</i></blockquote>")
        extra_en[word].append("<br>".join(lines))
        stats["wiktionary_en"] += 1
        if k:
            extra_kn[k].append("<br>".join(
                [f'<b>{E(k)}</b> — <b>{E(word)}</b> <FONT COLOR="#909090">({subject(e["domain"])})</FONT>'] + kn_lines))
            stats["wiktionary_kn_terms"] += 1

    # 4. Kannada Wikipedia: human Kannada term and explanation.
    for i in json.load(open(f"{work}/topic_knwiki_text.json")):
        en_term = i["en"]
        if en_term.lower() in wikt_words and not en_term.isupper():
            en_term = en_term.lower() if en_term[:1].isupper() and en_term.lower() in wikt_words else en_term
        kn_text = clean_lead(i.get("kn_text", "")) if i.get("kn_text") else ""
        en_text = clean_lead(i.get("en_text", "")) if i.get("en_text") else ""
        kn_expl = kn_text or text_kn.get(en_text, "")
        if not kn_expl and not en_text:
            continue
        src = "ವಿಕಿಪೀಡಿಯ / Wikipedia"
        extra_kn[i["kn"]].append("<br>".join(filter(None, [
            f'<b>{E(i["kn"])}</b> — <b>{E(en_term)}</b> <FONT COLOR="#909090">({subject(i["domain"])}; {src})</FONT>',
            ("  ಅರ್ಥ: " + E(kn_expl)) if kn_expl else "",
            ("  " + E(en_text)) if en_text else ""])))
        extra_en[en_term].append("<br>".join(filter(None, [
            f'<b>{E(en_term)}</b> <FONT COLOR="#909090">({subject(i["domain"])}; {src})</FONT>',
            "ಕನ್ನಡ: " + E(i["kn"]),
            ("  " + E(en_text)) if en_text else "",
            ("  ಅರ್ಥ: " + E(kn_expl)) if kn_expl else ""])))
        stats["wikipedia"] += 1

    json.dump(extra_en, open(f"{work}/extra_en.json", "w"), ensure_ascii=False)
    json.dump(extra_kn, open(f"{work}/extra_kn.json", "w"), ensure_ascii=False)
    stats["en_headwords"] = len(extra_en)
    stats["kn_headwords"] = len(extra_kn)
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
