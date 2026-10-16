"""Collect the unique definitions and examples to translate, most frequent words first."""
import json
import sys

from collins import classify, frequency, read_stardict

folder, out = sys.argv[1], sys.argv[2]
entries = read_stardict(folder, "Collins5")
order = sorted(range(len(entries)), key=lambda k: (-frequency(entries[k][1]), k))
seen, items = set(), []
for k in order:
    for line in entries[k][1].split("<br>"):
        kind, text = classify(line)
        if kind and text not in seen:
            seen.add(text)
            items.append({"t": text, "k": kind, "f": frequency(entries[k][1])})
with open(out, "w") as f:
    for it in items:
        f.write(json.dumps(it, ensure_ascii=False) + "\n")
from collections import Counter
print(len(items), Counter((i["k"], i["f"]) for i in items), sum(len(i["t"]) for i in items))
