"""Parse the Kannada-English Etymological Dictionary (N. Učida & B. B. Rajapurohit,
ed. J. Takashima, ILCAA Tokyo 2018, CC BY-NC 4.0) from `pdftotext -raw` output.

usage: keed.py keed.txt OUT.jsonl

Each output line is one entry:
  {"kn": headword, "tr": transliteration, "status": [...], "pos": "n.",
   "senses": [{"en": "...", "lit": bool}], "examples": [{"kn": "...", "en": "..."}],
   "see": [...], "origin": "Sanskrit"}
"""
import json
import re
import sys

KN = "ಀ-೿‌‍"
STATUS = {"Ĺ": "obsolete", "đ": "literary", "Ď": "regional", "Ě": "highly literary", "♠": "variant spelling",
          "♢": "uncommon", "*": "colloquial", "?": "doubtful"}
# headword (Kannada, maybe a homonym number), transliteration, [IPA], rest of the line
START = re.compile(
    r"^(?P<mark>[ĹđĎĚ♠♢*?\s]*)(?P<kn>[" + KN + r"][" + KN + r"\-\s]*?)\s*(?P<num>[¹²³⁴⁵⁶⁷⁸⁹]*)\s*"
    r"(?P<tr>[^\s\[\]" + KN + r"]+(?:\s[^\s\[\]" + KN + r"]+){0,3}?)\s*\[(?P<ipa>[^\]]+)\]\s*(?P<rest>.*)$")
HEADER = re.compile(r"^[" + KN + r"\-\s]+\s\d+\s[" + KN + r"\-\s]+$|^[" + KN + r"\-\s]+\s\d+$|^\d+\s[" + KN + r"\-\s]+$")
POS = re.compile(r"^(\(?(?:n|adj|adv|vt|vi|v|pron|numr|postp|part|intrj|conj|suf|pref|snt|onom|mim|echo|"
                 r"v\.aux|v\.adj|v\.adv|p\.part|m|f|mf|mn|imp|subj|denm|dat|gen|ins|obl|ibc|ifc|col|dig|pej)\.\)?,?\s*)+")
LANGS = {"Sk.": "Sanskrit", "Ka.": "Kannada", "Te.": "Telugu", "Ta.": "Tamil", "Ma.": "Malayalam", "Tu.": "Tulu",
         "Hi.": "Hindi", "Ar.": "Arabic", "Pers.": "Persian", "Per.": "Persian", "Eng.": "English", "E.": "English",
         "Mar.": "Marathi", "Pkt.": "Prakrit", "Por.": "Portuguese", "Port.": "Portuguese", "Urd.": "Urdu",
         "U.": "Urdu", "H.": "Hindi", "Kod.": "Kodagu", "Tam.": "Tamil", "Tel.": "Telugu", "Mal.": "Malayalam"}


def tidy(text):
    """Turn the book's symbols into plain text a reader can show."""
    text = re.sub(r"ú[^û]*û", "", text)  # semantic class 〖mind〗: not needed when reading
    # Sources and figure pointers: [see Fig.], (Kitt.), (R.,M. (Kitt.)), [Ka. āvu + kaḷ ?, *D334]
    text = re.sub(r"\[see Fig\.?\]|\[Ø\]", "", text)
    text = re.sub(r"\((?:[^()]|\([^()]*\))*Kitt\.\)?\)", "", text)
    text = re.sub(r"\[(?:" + "|".join(re.escape(k) for k in LANGS) + r")[^\]]*\]", "", text)
    text = text.replace("þ", "(").replace("ß", ")").replace("《", "(").replace("》", ")")
    text = text.replace("〈", "(").replace("〉", ")").replace("｟", "(").replace("｠", ")")
    text = text.replace("↔", "opposite:").replace("’", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"\s+", " ", text).strip(" ,;")
    return re.sub(r"\s*\([^()]*$", "", text)  # a citation cut short: "steepness (R.,M."


def split_senses(text):
    """Split '1 mine 2 rich source 3 crowd' into senses (numbers must count up)."""
    parts, want, pos = [], 1, 0
    for m in re.finditer(r"(?:(?<=\s)|^)(đ?)(\d{1,2})(?=[\s‘'\"(])", text):
        if int(m.group(2)) == want:
            if want > 1:
                parts.append(text[pos:m.start()])
            elif m.start() > 0 and text[:m.start()].strip():
                parts.append(text[:m.start()])  # text before "1" (rare)
            pos = m.end()
            want += 1
    parts.append(text[pos:])
    return [p.strip() for p in parts if p.strip()]


def parse_body(rest):
    e = {"pos": "", "senses": [], "examples": [], "see": [], "origin": "", "variants": []}
    rest = rest.strip()
    # Cross references: ù ākarṣaṇa or ù ಆಕರ್ಷಣ
    for s in re.findall(r"ù\s*([^ù\[\]ű]+)", rest):
        e["see"].append(tidy(s))
    rest = re.sub(r"ù\s*[^ù\[\]ű]+", " ", rest).strip()
    # Origin: the last [..] group, e.g. [Sk.] or [Ka. D332] (Kitt.)
    m = re.search(r"\[([^\[\]]*)\]\s*(\([^)]*\))?\s*(\[Ø\])?\s*$", rest)
    if m:
        src = m.group(1).strip()
        lang = src.split()[0] if src.split() else ""
        e["origin"] = LANGS.get(lang, "") if lang else ""
        rest = rest[: m.start()]
    # Variant spellings right after the pronunciation: "ಆಕಳ್, ಆಕಳ n." or "ಆಖರಿ ① n."
    m = re.match(r"^\s*([" + KN + r"\s,\-]+?)\s*(?=[①②]?\s*\(?(?:n|adj|adv|vt|vi|v|pron|intrj|part|postp|numr)\.)", rest)
    if m:
        e["variants"] = [v.strip(" -") for v in m.group(1).split(",") if v.strip(" -")]
        rest = rest[m.end():]
    # Examples: ű <Kannada sentence> <English translation>
    chunks = rest.split("ű")
    head = chunks[0]
    for ch in chunks[1:]:
        m = re.match(r"\s*([" + KN + r"0-9\s,.!?;:'\"()\-–—…]+?)\s*([A-Z\"'(].*)$", ch.strip(), re.S)
        if not m:
            head += " " + ch
            continue
        kn, en = m.group(1).strip(), m.group(2).strip()
        # Sense numbers after the example's English belong to the meanings.
        n = re.search(r"(?<=[.!?\"'])\s+(?=đ?\d{1,2}\s|[①②③]|\(?(?:n|adj|adv|vt|vi|v|pron|intrj|part|postp)\.\s)", en)
        tail = ""
        if n:
            tail, en = en[n.start():], en[: n.start()]
        e["examples"].append({"kn": tidy(kn), "en": tidy(en)})
        head += " " + tail
    # ① n. ... ② adv. ...: one block per part of speech, numbered senses in each.
    for i, block in enumerate(re.split(r"[①②③④⑤]", head)):
        block = tidy(block)
        if not block:
            continue
        pos = ""
        m = POS.match(block)
        if m:
            pos = m.group(0).strip(" ,")
            block = block[m.end():]
        if not e["pos"]:
            e["pos"] = pos
        for s in split_senses(block):
            lit = s.startswith("đ")
            s = tidy(s.lstrip("đ")).replace("đ", "")
            if s and re.search(r"[A-Za-z]", s):
                e["senses"].append({"en": s, "lit": lit, "pos": pos if pos != e["pos"] else ""})
    return e


def main():
    src, out = sys.argv[1:3]
    lines = open(src, encoding="utf-8").read().split("\n")
    # The dictionary proper starts at the first entry for ಅ.
    start = next(i for i, l in enumerate(lines) if re.match(r"^ಅ\s*a\s*\[", l))
    entries, cur, pending = [], None, ""
    for line in lines[start:]:
        line = line.replace("\f", "").strip()
        if not line or HEADER.match(line):
            continue
        if re.fullmatch(r"[ĹđĎĚ♠♢*?\s]+", line):
            pending += line
            continue
        m = START.match(line)
        if m and re.search(r"[a-zāīūēō]", m.group("tr")):
            if cur:
                entries.append(cur)
            cur = {"kn": re.sub(r"\s+", " ", m.group("kn")).strip(" -"), "num": m.group("num"),
                   "tr": m.group("tr"), "ipa": m.group("ipa"),
                   "status": [STATUS[c] for c in pending + m.group("mark") if c in STATUS], "body": m.group("rest")}
            pending = ""
        elif cur:
            if cur["body"].endswith("-") and re.match(r"^[a-z" + KN + r"]", line):
                cur["body"] = cur["body"][:-1] + line  # "po-" + "litical", "ಆಕಾಂ-" + "ಕ್ಷಿಸು"
            else:
                cur["body"] += " " + line
    if cur:
        entries.append(cur)
    with open(out, "w", encoding="utf-8") as f:
        for c in entries:
            e = {"kn": c["kn"], "num": c["num"], "tr": c["tr"], "status": c["status"]}
            e.update(parse_body(c["body"]))
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(len(entries), "entries")


if __name__ == "__main__":
    main()
