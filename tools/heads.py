"""Headword prompts for machine translation: "to abandon" for verbs, the word itself otherwise.

usage: heads.py COLLINS_FOLDER OUT.jsonl
"""
import json
import re
import sys

from collins import read_stardict

folder, out = sys.argv[1:3]
seen = set()
with open(out, "w") as f:
    for w, body in read_stardict(folder, "Collins5"):
        base = re.sub(r"\(\d\)$", "", w)
        if base.lower() in seen or not re.match(r"^[A-Za-z][A-Za-z' -]*$", base):
            continue
        seen.add(base.lower())
        first = re.search(r"\[([A-Z-]+(?: [A-Z]+)?)\]", body)
        pos = first.group(1) if first else ""
        prompt = f"to {base}" if pos in ("VERB", "PHRASAL VERB") else base
        f.write(json.dumps({"t": prompt, "w": base.lower(), "pos": pos}) + "\n")
print(len(seen))
