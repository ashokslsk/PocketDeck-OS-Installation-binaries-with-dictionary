"""Strings to translate for the subject vocabulary.

usage: topic_mt_input.py WORK_DIR
  mt_topic_text.jsonl  meanings and examples (English Wiktionary), and English
                       Wikipedia openings of Kannada articles that have no
                       Kannada opening -> translated into Kannada
  mt_topic_terms.jsonl the subject words themselves -> a Kannada headword,
                       kept only if it translates back to the same word
"""
import json
import re
import sys


def clean_lead(text, sentences=2):
    """First sentences of a Wikipedia opening, without bracketed scripts and pronunciations."""
    text = re.sub(r"\s*\([^()]*\)", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?।])\s+", text)
    return " ".join(parts[:sentences]).strip()


def term_prompt(word, pos):
    """'a mine' for a one-word noun, 'to go' for a verb: context for a one-word translation."""
    if " " not in word and pos == "Noun":
        return ("an " if word[0].lower() in "aeiou" else "a ") + word
    if " " not in word and pos == "Verb":
        return "to " + word
    return word


def main():
    work = sys.argv[1]
    topic = json.load(open(f"{work}/topic_wikt.json"))
    knwiki = json.load(open(f"{work}/topic_knwiki_text.json"))
    texts, terms = [], []
    for word, e in sorted(topic.items(), key=lambda kv: -kv[1]["zipf"]):
        pos = e["blocks"][0]["pos"]
        terms.append(term_prompt(word, pos))
        for b in e["blocks"]:
            for s in b["senses"]:
                texts.append(s["text"])
                texts += [x["text"] for x in s["examples"]]
    for i in knwiki:
        if not i.get("kn_text") and i.get("en_text"):
            texts.append(clean_lead(i["en_text"]))
    for name, items in (("mt_topic_text", texts), ("mt_topic_terms", terms)):
        seen = set()
        with open(f"{work}/{name}.jsonl", "w") as f:
            for t in items:
                if t and t not in seen and re.search(r"[A-Za-z]{2}", t):
                    seen.add(t)
                    f.write(json.dumps({"t": t}) + "\n")
        print(name, len(seen))


if __name__ == "__main__":
    main()
