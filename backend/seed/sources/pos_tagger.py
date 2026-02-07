POS_MAP = {
    "NOUN": "noun",
    "VERB": "verb",
    "ADJ": "adj",
    "ADV": "adv",
    "ADP": "prep",
    "CCONJ": "conj",
    "SCONJ": "conj",
    "PRON": "pron",
    "DET": "det",
    "INTJ": "intj",
    "PROPN": "noun",
    "AUX": "verb",
    "NUM": "det",
    "PART": "adv",
}


def get_pos_tags(words: list[str]) -> dict[str, str]:
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("Using spaCy for POS tagging...")
        result = {}
        batch_size = 500
        for i in range(0, len(words), batch_size):
            batch = words[i:i + batch_size]
            text = " . ".join(batch)
            doc = nlp(text)
            word_set = set(batch)
            for token in doc:
                if token.text.lower() in word_set and token.text.lower() not in result:
                    result[token.text.lower()] = POS_MAP.get(token.pos_, "noun")
        for w in words:
            if w not in result:
                result[w] = "noun"
        return result
    except (ImportError, OSError):
        print("spaCy not available, using basic POS heuristics...")
        return {w: _guess_pos(w) for w in words}


def _guess_pos(word: str) -> str:
    if word.endswith("ly"):
        return "adv"
    if word.endswith(("tion", "sion", "ment", "ness", "ity", "ance", "ence")):
        return "noun"
    if word.endswith(("ful", "less", "ous", "ive", "able", "ible", "al", "ial")):
        return "adj"
    if word.endswith(("ize", "ise", "ate", "ify", "en")):
        return "verb"
    if word in ("the", "a", "an", "this", "that", "these", "those", "my", "your", "his", "her", "its", "our", "their"):
        return "det"
    if word in ("i", "you", "he", "she", "it", "we", "they", "me", "him", "us", "them"):
        return "pron"
    if word in ("in", "on", "at", "to", "for", "with", "by", "from", "of", "about"):
        return "prep"
    if word in ("and", "but", "or", "nor", "so", "yet"):
        return "conj"
    if word in ("be", "is", "am", "are", "was", "were", "have", "has", "had", "do", "does", "did",
                 "will", "would", "shall", "should", "may", "might", "can", "could", "must"):
        return "verb"
    return "noun"
