"""Text of the two-column KEED pages in reading order, from `pdftotext -bbox`.

pdftotext's raw mode keeps the column order but runs some English words
together; its layout modes space words correctly but mix the columns. The
word boxes give both: words are split into columns by position and lines are
rebuilt top to bottom, left column first.

usage: keed_text.py KEED.pdf OUT.txt
"""
import html
import re
import subprocess
import sys

WORD = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>')


def column_lines(words):
    words.sort(key=lambda w: (w[1] + w[3]) / 2)
    lines = []
    for w in words:
        mid = (w[1] + w[3]) / 2
        if lines and abs(mid - lines[-1]["mid"]) < 4.5:
            lines[-1]["words"].append(w)
        else:
            lines.append({"mid": mid, "words": [w]})
    out = []
    for line in lines:
        ws = sorted(line["words"], key=lambda w: w[0])
        text = ws[0][4]
        for prev, w in zip(ws, ws[1:]):
            text += ("" if w[0] - prev[2] < 1.0 else " ") + w[4]
        out.append(text)
    return out


def main():
    pdf, out = sys.argv[1:3]
    data = subprocess.run(["pdftotext", "-bbox", pdf, "-"], capture_output=True, text=True, check=True).stdout
    with open(out, "w", encoding="utf-8") as f:
        for page in data.split("<page ")[1:]:
            width = float(re.search(r'width="([\d.]+)"', page).group(1))
            words = [(float(a), float(b), float(c), float(d), html.unescape(t)) for a, b, c, d, t in WORD.findall(page)]
            words = [w for w in words if w[1] > 52]  # running header: first word, page number, last word
            left = [w for w in words if (w[0] + w[2]) / 2 < width / 2]
            right = [w for w in words if (w[0] + w[2]) / 2 >= width / 2]
            for line in column_lines(left) + column_lines(right):
                f.write(line + "\n")
            f.write("\f\n")


if __name__ == "__main__":
    main()
