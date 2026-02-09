def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def normalize_text(text: str) -> str:
    return text.strip().lower()


def parse_json_field(value) -> list | dict | None:
    """Safely parse a JSON field that might be a string or already parsed.

    SQLite JSON columns sometimes return strings instead of parsed objects.
    This handles both cases.
    """
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, str):
        import json
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return None
    return None


def get_translations(word) -> list[str]:
    """Get translations as a list, handling JSON parsing."""
    translations = parse_json_field(word.translations)
    if isinstance(translations, list):
        return translations
    return []


def get_first_translation(word) -> str:
    """Get the first translation safely."""
    translations = get_translations(word)
    return translations[0] if translations else ""
