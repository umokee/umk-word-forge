def check_sentence_prompt(word: str, translation: str, sentence: str) -> str:
    """Build a prompt that asks the AI to check a user-written sentence."""
    return f"""You are an English language tutor helping a Russian-speaking student.

The student is learning the word "{word}" (translation: "{translation}").
They wrote this sentence: "{sentence}"

Analyze the sentence and return a JSON object with exactly these fields:
- "correct" (bool): true if the sentence is overall acceptable
- "grammar_ok" (bool): true if grammar is correct
- "word_usage_ok" (bool): true if the target word "{word}" is used correctly and appropriately
- "natural" (bool): true if the sentence sounds natural to a native speaker
- "feedback_ru" (str): brief feedback in Russian explaining any issues or praising the sentence
- "corrected" (str or null): a corrected version of the sentence if there are errors, null if the sentence is fine

Return ONLY the JSON object, no extra text or markdown formatting."""


def generate_contexts_prompt(word: str, part_of_speech: str, translations: list[str], count: int = 3, difficulty: str = "simple") -> str:
    """Build a prompt that asks the AI to generate example sentences."""

    level_guide = {
        "simple": "A1-A2 level (simple vocabulary, short sentences, everyday situations)",
        "medium": "B1 level (moderate vocabulary, compound sentences, common topics)",
        "natural": "B2+ level (natural, idiomatic usage as native speakers would use)",
    }

    level_desc = level_guide.get(difficulty, level_guide["simple"])
    translation_hint = ", ".join(translations[:3]) if translations else word

    return f"""You are creating example sentences for an English vocabulary learning app used by Russian speakers.

Word: "{word}"
Part of speech: {part_of_speech}
Translation: {translation_hint}

Generate {count} high-quality example sentences that:
1. Show REAL, NATURAL usage of "{word}" in context (not artificial textbook examples)
2. Are at {level_desc}
3. Each demonstrates a DIFFERENT meaning or usage pattern
4. Are memorable and useful for everyday communication

Guidelines:
- Use common collocations and phrases with "{word}"
- Include varied contexts (work, social, daily life, emotions, etc.)
- Make sentences interesting and relatable
- Translations should be natural Russian, not word-for-word

Return a JSON array with {count} objects, each having:
- "en": the English sentence (8-15 words ideal)
- "ru": natural Russian translation
- "difficulty": 1 for A1-A2, 2 for B1, 3 for B2+

Example format:
[
  {{"en": "I need to make a decision by tomorrow.", "ru": "Мне нужно принять решение до завтра.", "difficulty": 1}},
  ...
]

Return ONLY the JSON array, no markdown or extra text."""
