"""Opening sentences of Wikipedia articles (CC BY-SA 4.0), Kannada and English.

usage: wiki_extracts.py topic_knwiki.json OUT.json
Adds "kn_text" (Kannada Wikipedia, first two sentences) and "en_text" (English
Wikipedia, first two sentences) to each item. Resumable: items already in OUT
are kept.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

UA = "KannadaDictBuilder/1.0 (personal e-reader dictionary; contact via Wikipedia user page)"


def extracts(lang, titles):
    q = urllib.parse.urlencode({"action": "query", "prop": "extracts", "exintro": 1, "explaintext": 1,
                                "exsentences": 2, "redirects": 1, "format": "json", "formatversion": 2,
                                "titles": "|".join(titles)})
    req = urllib.request.Request(f"https://{lang}.wikipedia.org/w/api.php?{q}", headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            data = json.load(urllib.request.urlopen(req, timeout=30))
            break
        except Exception:
            time.sleep(5 * (attempt + 1))
    else:
        return {}
    q = data.get("query", {})
    back = {n["to"]: n["from"] for n in q.get("normalized", []) + q.get("redirects", [])}
    out = {}
    for p in q.get("pages", []):
        title = p.get("title", "")
        text = (p.get("extract") or "").strip()
        while title in back:
            title = back[title]
        if text:
            out[title] = text
    return out


def main():
    src, out_path = sys.argv[1:3]
    items = json.load(open(src))
    done = {i["kn_title"]: i for i in json.load(open(out_path))} if os.path.exists(out_path) else {}
    todo = [i for i in items if i["kn_title"] not in done]
    for lang, key, field in (("kn", "kn_title", "kn_text"), ("en", "en_title", "en_text")):
        for n in range(0, len(todo), 20):
            batch = todo[n:n + 20]
            got = extracts(lang, [i[key] for i in batch])
            for i in batch:
                i[field] = got.get(i[key], "")
            time.sleep(1.0)
            print(f"{lang} {min(n + 20, len(todo))}/{len(todo)}", end="\r", flush=True)
        print()
    for i in todo:
        done[i["kn_title"]] = i
    json.dump(list(done.values()), open(out_path, "w"), ensure_ascii=False)
    print(len(done), "items;", sum(1 for i in done.values() if i.get("kn_text")), "with Kannada text;",
          sum(1 for i in done.values() if i.get("en_text")), "with English text")


if __name__ == "__main__":
    main()
