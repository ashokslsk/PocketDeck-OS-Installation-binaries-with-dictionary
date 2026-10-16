"""Read the Wiktionary StarDict dictionaries made by xxyzz/wiktionary_stardict
(CC BY-SA 4.0) and turn an entry's HTML into parts of speech, meanings and examples.
"""
import html
import re
import struct

POS_NAMES = {"Noun", "Verb", "Adjective", "Adverb", "Pronoun", "Particle", "Suffix", "Prefix", "Interjection",
             "Conjunction", "Postposition", "Preposition", "Numeral", "Number", "Determiner", "Proper noun",
             "Phrase", "Proverb", "Prepositional phrase", "Article", "Contraction", "Symbol", "Infix",
             "Abbreviation", "Initialism", "Acronym", "Classifier"}
SKIP_LABELS = re.compile(r"\b(obsolete|archaic|rare|dated|nonstandard|vulgar|offensive|derogatory|historical|"
                         r"misspelling|eye dialect|nonce)\b", re.I)


def read_index(folder, stem):
    """[(word, offset, size)] from .idx."""
    idx = open(f"{folder}/{stem}.idx", "rb").read()
    out, i = [], 0
    while i < len(idx):
        j = idx.index(b"\0", i)
        out.append((idx[i:j].decode("utf-8"),) + struct.unpack(">II", idx[j + 1:j + 9]))
        i = j + 9
    return out


def read_syn(folder, stem):
    """[(form, index ordinal)] from .syn."""
    syn = open(f"{folder}/{stem}.syn", "rb").read()
    out, i = [], 0
    while i < len(syn):
        j = syn.index(b"\0", i)
        out.append((syn[i:j].decode("utf-8", "replace"), struct.unpack(">I", syn[j + 1:j + 5])[0]))
        i = j + 5
    return out


def text(fragment):
    fragment = re.sub(r"<style.*?</style>", "", fragment, flags=re.S)
    fragment = re.sub(r'<span class="defdate">.*?</span>', "", fragment, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", fragment))).strip()


def top_level(fragment, tag):
    """Contents of each top-level <tag>...</tag> in fragment (nesting aware)."""
    parts, depth, start = [], 0, 0
    for m in re.finditer(rf"<(/?){tag}\b[^>]*>", fragment):
        if not m.group(1):
            if depth == 0:
                start = m.end()
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                parts.append(fragment[start:m.start()])
    return parts


def parse(entry_html):
    """[{pos, tr, senses: [{text, label, examples: [{text, tr, en}]}]}] for one entry."""
    blocks = []
    for m in re.finditer(r"<h4>([^<]+)</h4>", entry_html):
        pos = m.group(1).strip()
        if pos not in POS_NAMES:
            continue
        rest = entry_html[m.end():]
        nxt = re.search(r"<h4>", rest)
        body = rest[: nxt.start()] if nxt else rest
        tr = re.search(r'class="headword-tr[^"]*"[^>]*>(.*?)</span>', body)
        ol = top_level(body, "ol")
        if not ol:
            continue
        senses = []
        for li in top_level(ol[0], "li"):
            examples = []
            for ex in re.finditer(r'<div class="h-usage-example">(.*?)</div>', li, re.S):
                e = ex.group(1)
                kn = re.search(r'class="[^"]*e-example[^"]*"[^>]*>(.*?)</i>', e, re.S)
                tr_ex = re.search(r'class="[^"]*e-transliteration[^"]*"[^>]*>(.*?)</i>', e, re.S)
                en = re.search(r'class="e-translation"[^>]*>(.*?)</span>', e, re.S)
                if kn:
                    examples.append({"text": text(kn.group(1)), "tr": text(tr_ex.group(1)) if tr_ex else "",
                                     "en": text(en.group(1)) if en else ""})
            label = re.search(r'<span class="usage-label-sense">(.*?)</span></span>', li, re.S)
            label_text = text(label.group(1)).strip("() ") if label else ""
            core = re.sub(r"<dl>.*?</dl>|<ol>.*?</ol>", "", li, flags=re.S)
            if label:
                core = core.replace(label.group(0), "")
            t = text(core)
            if t:
                senses.append({"text": t, "label": label_text, "examples": examples})
        if senses:
            blocks.append({"pos": pos, "tr": text(tr.group(1)) if tr else "", "senses": senses})
    return blocks
