"""Totals for the finished dictionaries.

usage: dict_stats.py OUTPUT_DIR
For each dictionary: headwords (distinct entries), index entries (headwords
plus word forms that open them), Kannada explanations (ಅರ್ಥ lines and Kannada
lines under a Kannada headword), example sentences with a translation, the
size of the dictionary folder and of its zip.
"""
import os
import re
import struct
import sys


def stats(folder, stem):
    idx = open(f"{folder}/{stem}.idx", "rb").read()
    entries, i = set(), 0
    count = 0
    while i < len(idx):
        j = idx.index(b"\0", i)
        entries.add(struct.unpack(">II", idx[j + 1:j + 9]))
        count += 1
        i = j + 9
    text = open(f"{folder}/{stem}.dict", encoding="utf-8").read()
    return {
        "headwords": len(entries),
        "index_entries": count,
        "kannada_explanations": text.count("ಅರ್ಥ:"),
        "kannada_equivalent_lines": text.count("ಕನ್ನಡ:"),
        "examples_with_translation": text.count("<blockquote>"),
        "folder_mb": round(sum(os.path.getsize(f"{folder}/{f}") for f in os.listdir(folder)) / 1e6, 1),
    }


def main():
    out = sys.argv[1]
    for stem in ("CollinsKannada", "KannadaEnglish"):
        s = stats(f"{out}/{stem}", stem)
        z = f"{out}/{stem}.zip"
        s["zip_mb"] = round(os.path.getsize(z) / 1e6, 1) if os.path.exists(z) else None
        print(stem, s)


if __name__ == "__main__":
    main()
