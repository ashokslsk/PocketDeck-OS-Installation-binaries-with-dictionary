"""English meanings from KEED to translate into Kannada (most useful first).

A meaning is sent without its Kannada cross references ("cow = ಹಸು (hasu)" ->
"cow") and without usage labels such as "(fig.)", which the translator reads
as the fruit. A one-word meaning gets its part of speech as context: "mine" of
a noun is sent as "a mine" (ಗಣಿ, not ನನ್ನದು), "go" of a verb as "to go".
usage: keed_mt_input.py keed.jsonl OUT.jsonl
"""
import json
import re
import sys

KN = "ಀ-೿"
LABEL = re.compile(r"^\s*\((fig|col|pej|dig|lit|hon|pl|sg|vul|obs)\.\)\s*")
LABEL_KN = {"fig": "ಲಾಕ್ಷಣಿಕ", "col": "ಆಡುಮಾತು", "pej": "ನಿಂದಾರ್ಥ", "dig": "ಗೌರವಾರ್ಥ", "lit": "ಸಾಹಿತ್ಯಿಕ",
            "hon": "ಗೌರವಾರ್ಥ", "vul": "ಅಸಭ್ಯ", "obs": "ಪ್ರಾಚೀನ", "pl": "ಬಹುವಚನ", "sg": "ಏಕವಚನ"}


def label_of(sense):
    """Kannada name of the sense's usage label, or ""."""
    m = LABEL.match(sense)
    return LABEL_KN.get(m.group(1), "") if m else ""


def mt_text(sense, pos=""):
    text = sense.split(" = ")[0]
    text = re.sub(r"[" + KN + r"]+(\s*\([^)]*\))?", "", text)
    text = LABEL.sub("", text)
    text = re.sub(r"\s+", " ", text).strip(" ,;")
    if re.fullmatch(r"[A-Za-z'-]+", text):
        if pos.startswith(("n", "(n")):
            text = ("an " if text[0].lower() in "aeiou" else "a ") + text
        elif pos.startswith(("v", "(v")) and pos not in ("v.adj.", "v.adv."):
            text = "to " + text
    return text


def kannada_meaning(kn):
    """Drop the ಒಂದು ("a") the translator adds for "a mine", and repeats: "to remember,
    to recall, to recollect" often comes back as the same Kannada three times."""
    kn = re.sub(r"^ಒಂದು\s+", "", kn).strip()
    parts, seen = [], set()
    for p in re.split(r"\s*,\s*", kn):
        if p and p not in seen:
            seen.add(p)
            parts.append(p)
    return ", ".join(parts)


if __name__ == "__main__":
    src, out = sys.argv[1:3]
    entries = [json.loads(l) for l in open(src)]
    # Entries with examples and without status marks are the everyday words: first.
    entries.sort(key=lambda e: (bool(e["status"]), not e["examples"]))
    seen = set()
    with open(out, "w") as f:
        for e in entries:
            for s in e["senses"]:
                t = mt_text(s["en"], s.get("pos") or e["pos"])
                if t and t not in seen and re.search(r"[A-Za-z]{2}", t):
                    seen.add(t)
                    f.write(json.dumps({"t": t}) + "\n")
    print(len(seen))
