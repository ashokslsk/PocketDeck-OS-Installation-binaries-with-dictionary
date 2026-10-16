"""Shared helpers: read a StarDict dictionary and classify Collins COBUILD lines."""
import html
import re
import struct

TAG = re.compile(r"<[^>]+>")
SKIP_DEF = re.compile(r"^(see also|see |→|\W*$)|^\S+( \S+)? (is|are) also (an? )?\w+\.?$", re.I)


def read_stardict(folder, stem):
    idx = open(f"{folder}/{stem}.idx", "rb").read()
    dic = open(f"{folder}/{stem}.dict", "rb").read()
    entries, i = [], 0
    while i < len(idx):
        j = idx.index(b"\0", i)
        off, size = struct.unpack(">II", idx[j + 1:j + 9])
        entries.append((idx[i:j].decode("utf-8"), dic[off:off + size].decode("utf-8")))
        i = j + 9
    return entries


def plain(fragment):
    return re.sub(r"\s+", " ", html.unescape(TAG.sub("", fragment))).strip()


def frequency(body):
    """Collins frequency band from the ◆ markers on the headword (0..5)."""
    m = re.match(r"<b>(◆*)", body)
    return len(m.group(1)) if m else 0


def classify(line):
    """Return ('ex', text), ('def', text) or (None, None) for one <br>-separated line."""
    if line.startswith("  ● "):
        t = re.sub(r"^\.\.\.\s*", "", plain(line[4:]))
        t = re.sub(r"\s*\.\.\.$", ".", t).strip()
        # "be going to: see going" points to another entry; nothing to translate.
        return ("ex", t) if len(t) > 2 and not re.search(r":\s*see\b", t) else (None, None)
    if line.startswith("  ") and not line.startswith("  <FONT COLOR=\"#0091") and not line.startswith("  <FONT COLOR=\"#0090"):
        t = plain(line)
        if len(t) >= 15 and not SKIP_DEF.search(t):
            return ("def", t)
    return (None, None)


# Machine translation sometimes writes a consonant, virama and a separate vowel
# letter ("ಡಾಲರ್ಅನ್ನು"); written Kannada uses the vowel sign ("ಡಾಲರನ್ನು").
VOWEL_SIGN = {"ಅ": "", "ಆ": "ಾ", "ಇ": "ಿ", "ಈ": "ೀ", "ಉ": "ು", "ಊ": "ೂ", "ಋ": "ೃ",
              "ಎ": "ೆ", "ಏ": "ೇ", "ಐ": "ೈ", "ಒ": "ೊ", "ಓ": "ೋ", "ಔ": "ೌ"}
JOINED_VOWEL = re.compile("\u0CCD([" + "".join(VOWEL_SIGN) + "])")


def clean_kannada(text):
    return JOINED_VOWEL.sub(lambda m: VOWEL_SIGN[m.group(1)], text)
