"""Subject areas for the topic vocabulary, with how to recognise them.

kn_cat: words in Kannada Wikipedia category names (ವರ್ಗ).
wikt:   topic labels on English Wiktionary meanings, e.g. "(medicine)".
"""
import re

DOMAINS = {
    "medical": {
        "kn": "ವೈದ್ಯಕೀಯ",
        "kn_cat": ["ರೋಗ", "ಕಾಯಿಲೆ", "ವೈದ್ಯ", "ಔಷಧ", "ಆರೋಗ್ಯ", "ಅಂಗರಚನ", "ಶರೀರ", "ಸೋಂಕು", "ಕ್ಯಾನ್ಸರ್", "ಜೀವಸತ್ವ",
                   "ವಿಟಮಿನ್", "ಲಸಿಕೆ", "ಹಾರ್ಮೋನ್", "ಕಿಣ್ವ", "ಮನೋರೋಗ", "ಪೋಷಣೆ"],
        "wikt": ["medicine", "pathology", "pharmacology", "anatomy", "physiology", "surgery", "disease",
                 "medical", "immunology", "oncology", "cardiology", "neurology", "psychiatry", "virology",
                 "epidemiology", "pharmacy", "dentistry", "obstetrics", "gynecology", "ophthalmology"],
    },
    "ayurveda": {
        "kn": "ಆಯುರ್ವೇದ",
        "kn_cat": ["ಆಯುರ್ವೇದ", "ಔಷಧೀಯ ಸಸ್ಯ", "ಗಿಡಮೂಲಿಕೆ", "ಯೋಗ", "ಪ್ರಾಣಾಯಾಮ"],
        "wikt": ["Ayurveda", "yoga"],
    },
    "purana": {
        "kn": "ಪುರಾಣ",
        "kn_cat": ["ಪುರಾಣ", "ಮಹಾಭಾರತ", "ರಾಮಾಯಣ", "ದೇವತೆ", "ದೇವರು", "ಹಿಂದೂ ಧರ್ಮ", "ವೇದ", "ಉಪನಿಷತ್",
                   "ಋಷಿ", "ಪೌರಾಣಿಕ", "ಭಾಗವತ", "ಹಿಂದೂ ಹಬ್ಬ"],
        "wikt": ["Hinduism", "Hindu mythology", "Buddhism", "Jainism"],
    },
    "computing": {
        "kn": "ಗಣಕ ವಿಜ್ಞಾನ",
        "kn_cat": ["ಕಂಪ್ಯೂಟರ್", "ಗಣಕ", "ತಂತ್ರಾಂಶ", "ಸಾಫ್ಟ್‌ವೇರ್", "ಅಂತರಜಾಲ", "ಇಂಟರ್ನೆಟ್", "ಪ್ರೋಗ್ರಾಮಿಂಗ್",
                   "ತಂತ್ರಜ್ಞಾನ", "ಎಲೆಕ್ಟ್ರಾನಿಕ್ಸ್", "ದತ್ತಾಂಶ", "ಜಾಲತಾಣ", "ಮೊಬೈಲ್"],
        "wikt": ["computing", "computer science", "programming", "software", "Internet", "networking",
                 "computer hardware", "cryptography", "databases", "operating systems", "electronics"],
    },
    "ai": {
        "kn": "ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ",
        "kn_cat": ["ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ", "ಯಂತ್ರ ಕಲಿಕೆ", "ರೊಬೊಟಿಕ್ಸ್", "ಯಂತ್ರಮಾನವ"],
        "wikt": ["artificial intelligence", "machine learning", "neural networks", "robotics",
                 "natural language processing"],
    },
    "maths": {
        "kn": "ಗಣಿತ",
        "kn_cat": ["ಗಣಿತ", "ಜ್ಯಾಮಿತಿ", "ಬೀಜಗಣಿತ", "ಸಂಖ್ಯಾಶಾಸ್ತ್ರ", "ಅಂಕಗಣಿತ", "ತ್ರಿಕೋನಮಿತಿ", "ಕಲನಶಾಸ್ತ್ರ"],
        "wikt": ["mathematics", "algebra", "geometry", "statistics", "calculus", "arithmetic", "trigonometry",
                 "probability theory", "number theory", "topology", "linear algebra", "set theory", "logic"],
    },
    "politics": {
        "kn": "ರಾಜಕೀಯ",
        "kn_cat": ["ರಾಜಕೀಯ", "ರಾಜಕಾರಣ", "ಸಂವಿಧಾನ", "ಸರ್ಕಾರ", "ಚುನಾವಣೆ", "ಕಾನೂನು", "ಆಡಳಿತ", "ಪ್ರಜಾಪ್ರಭುತ್ವ"],
        "wikt": ["politics", "government", "law", "legal", "diplomacy", "elections", "military"],
    },
    "socioeconomic": {
        "kn": "ಸಮಾಜ ಮತ್ತು ಅರ್ಥಶಾಸ್ತ್ರ",
        "kn_cat": ["ಅರ್ಥಶಾಸ್ತ್ರ", "ಆರ್ಥಿಕ", "ಸಮಾಜಶಾಸ್ತ್ರ", "ಸಾಮಾಜಿಕ", "ಹಣಕಾಸು", "ಬ್ಯಾಂಕ್", "ವ್ಯಾಪಾರ",
                   "ತೆರಿಗೆ", "ಕೃಷಿ", "ಕಾರ್ಮಿಕ"],
        "wikt": ["economics", "finance", "sociology", "business", "banking", "accounting", "marketing",
                 "trading", "taxation", "insurance"],
    },
    "kannada_genres": {
        "kn": "ಕನ್ನಡ ಸಾಹಿತ್ಯ ಮತ್ತು ಕಲೆ",
        "kn_cat": ["ಸಾಹಿತ್ಯ ಪ್ರಕಾರ", "ಸಾಹಿತ್ಯ ಚಳುವಳಿ", "ಕಾವ್ಯ ಪ್ರಕಾರ", "ಜಾನಪದ", "ಯಕ್ಷಗಾನ", "ರಂಗಭೂಮಿ",
                   "ಕರ್ನಾಟಕ ಸಂಗೀತ", "ವಚನ", "ದಾಸ ಸಾಹಿತ್ಯ", "ಛಂದಸ್ಸು", "ಕನ್ನಡ ಸಾಹಿತ್ಯ"],
        "wikt": [],  # English film or music labels are not Kannada genres
    },
    "genz": {
        "kn": "ಯುವ ಆಡುಭಾಷೆ",
        "kn_cat": [],
        "wikt": ["Gen Z", "Internet slang", "text messaging", "social media", "memes", "video games"],
    },
}

# Articles about people, places, films and organisations are not vocabulary.
EXCLUDE_WORDS = ["ಜೀವಂತ", "ಜನನ", "ನಿಧನ", "ಸಾಹಿತಿ", "ಕವಿಗಳು", "ಲೇಖಕ", "ಕ್ರೀಡಾಪಟು", "ವಿಜ್ಞಾನಿ", "ರಾಜಕಾರಣಿ",
                 "ನಟರು", "ನಟಿಯರು", "ನಟ ", "ಗಾಯಕ", "ನಿರ್ದೇಶಕ", "ಚಲನಚಿತ್ರಗಳು", "ಧಾರಾವಾಹಿ", "ಜಿಲ್ಲೆ", "ಗ್ರಾಮ", "ಹಳ್ಳಿ",
                 "ನಗರ", "ತಾಲೂಕು", "ಪಟ್ಟಣ", "ರಾಜ್ಯಗಳು", "ದೇಶಗಳು", "ಸಂಸ್ಥೆಗಳು", "ಕಂಪನಿ", "ವಿಶ್ವವಿದ್ಯಾಲಯ", "ಕಾಲೇಜು",
                 "ಶಾಲೆಗಳು", "ವಿಶ್ವವಿದ್ಯಾನಿಲಯಗಳು", "ದೇವಾಲಯ", "ದೇವಸ್ಥಾನ", "ಪ್ರಶಸ್ತಿ", "ಪುಸ್ತಕಗಳು", "ವ್ಯಕ್ತಿ", "ಮಂತ್ರಿ", "ಮುಖ್ಯಮಂತ್ರಿ", "ಪ್ರಧಾನಿ",
                 "ಅಧ್ಯಕ್ಷ", "ಆಟಗಾರ", "ಕ್ರಿಕೆಟ್", "ಚಲನಚಿತ್ರ ನಟ"]
# People, places, films and organisations are not vocabulary. A word must start
# a word of the category name: "ನಟ" (actor) must not match "ಸಂಘಟನೆ".
EXCLUDE_CAT = re.compile(r"(?:^|\s)(?:" + "|".join(map(re.escape, EXCLUDE_WORDS)) + ")")


# Kannada joins words into compounds (ರೇಖಾಗಣಿತ = geometry), so a keyword may sit
# inside a word; these short ones only count at the start of a word, because
# they also occur inside unrelated words (ಯೋಗ in ಉದ್ಯೋಗ "employment").
WORD_START_ONLY = {"ಯೋಗ", "ವೇದ", "ಋಷಿ", "ವಚನ", "ಶರೀರ", "ರೋಗ", "ಗಣಕ", "ನೃತ್ಯ", "ವೈದ್ಯ"}


def _matches(category, keyword):
    if keyword in WORD_START_ONLY:
        return re.search(r"(?:^|\s)" + re.escape(keyword), category) is not None
    return keyword in category


def domain_of_categories(categories):
    """The first subject whose Kannada category words match, or None (also for people, places...)."""
    if any(EXCLUDE_CAT.search(c) for c in categories):
        return None
    for name, d in DOMAINS.items():
        if any(_matches(c, k) for c in categories for k in d["kn_cat"]):
            return name
    return None


STOP = {"a", "an", "the", "of", "in", "on", "at", "to", "for", "and", "or", "by", "with", "from", "up", "down",
        "out", "off", "over", "it", "is", "be", "as", "if", "all", "any", "one", "do", "get", "go", "that",
        "this", "what", "who", "me", "you", "i", "we", "my", "your", "like", "not", "no", "so", "but", "let",
        "come", "put", "make", "take", "time", "first", "new", "old", "good", "back", "end", "right", "way"}


def looks_like_term(word):
    """Not a phrase of everyday words ("for all", "I would", "get well")."""
    from wordfreq import zipf_frequency
    parts = [p for p in re.split(r"[\s-]+", word.lower()) if p]
    if len(parts) == 1:
        return True
    # A part is "everyday" if it is a stop word or among the ~1,000 commonest English words.
    content = sum(p not in STOP and zipf_frequency(p, "en") < 5.8 for p in parts)
    return content >= max(1, len(parts) - 1)


def domain_of_label(label):
    """Subject of a Wiktionary topic label like "(medicine, informal)", or None."""
    parts = [p.strip() for p in re.split(r"[,;]", label)]
    for name, d in DOMAINS.items():
        if any(p.lower() == w.lower() for p in parts for w in d["wikt"]):
            return name
    return None


def is_term(english, domain, wiktionary_words):
    """True if an English article title names a term (not a person, organisation or event).

    Puranic figures are names but belong in the Purana vocabulary."""
    title = re.sub(r"\s*\([^)]*\)$", "", english).strip()
    if not title or re.search(r"[\d/]", title) or len(title.split()) > 4:
        return False
    if domain == "purana":
        return True
    if title.lower() in wiktionary_words or title in wiktionary_words:
        return True
    words = title.split()
    if len(words) > 1 and all(w[:1].isupper() for w in words):
        return False  # "Rukmini Vijayakumar", "Michael Kors"
    return len(words) > 1  # "Fiscal year", "Motion sickness"
