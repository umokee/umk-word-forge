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


def enrich_word_prompt(word: str, part_of_speech: str, translations: list[str]) -> str:
    """Build a prompt to generate comprehensive linguistic data for a word."""
    translation_hint = ", ".join(translations[:3]) if translations else ""

    return f"""You are a linguistic expert creating data for an English vocabulary learning app for Russian speakers.

Word: "{word}"
Part of speech: {part_of_speech}
Russian translation: {translation_hint}

Generate comprehensive linguistic information about this word.

Return a JSON object with these fields (use null for inapplicable fields):

1. "verb_forms" (object or null): For verbs only
   - "past": past tense ("went")
   - "past_participle": past participle ("gone")
   - "present_participle": present participle ("going")
   - "third_person": third person singular ("goes")

2. "collocations" (array): 3-5 common collocations/word combinations
   Each: {{"en": "make a decision", "ru": "принять решение"}}

3. "phrasal_verbs" (array or null): For words that form phrasal verbs
   Each: {{"phrase": "look for", "meaning_en": "to search", "meaning_ru": "искать"}}

4. "usage_notes" (array): 2-4 important usage notes in Russian
   Examples: "часто используется с артиклем 'the'", "исчисляемое существительное", "неправильный глагол"

5. "common_mistakes" (array): 1-2 common mistakes Russian speakers make
   Each: {{"wrong": "I want go", "correct": "I want to go", "explanation_ru": "После want нужен инфинитив с to"}}

Focus on practical information that helps Russian speakers use the word correctly.
Return ONLY the JSON object, no markdown or extra text."""


def generate_function_word_prompt(word: str, part_of_speech: str) -> str:
    """Build a prompt to generate rich context for function words (the, a, to, in, etc.).

    Function words don't have direct translations and require explanation of usage rules.
    """
    return f"""You are a linguistic expert creating learning materials for Russian speakers studying English.

The word "{word}" (part of speech: {part_of_speech}) is a FUNCTION WORD that has no direct Russian translation.
Russian speakers often struggle with these words because they work differently from Russian grammar.

Generate comprehensive learning materials for "{word}".

Return a JSON object with these fields:

1. "usage_rules" (array): 4-6 key rules for when to use "{word}"
   Each: {{
     "rule": "Clear rule description in Russian",
     "example": "English example sentence demonstrating this rule"
   }}
   Focus on the most important and common usage patterns.

2. "comparisons" (array): 2-3 comparisons with similar/confusing words
   Each: {{
     "vs": "the other word (e.g., 'a/an' if word is 'the')",
     "difference": "Explanation of the difference in Russian"
   }}
   Compare with words that Russian speakers often confuse.

3. "common_errors" (array): 3-4 typical mistakes Russian speakers make
   Each: {{
     "wrong": "Incorrect usage example",
     "correct": "Correct version",
     "why": "Brief explanation in Russian why this is wrong"
   }}
   Focus on errors that come from Russian language interference.

4. "context_examples" (array): 3-5 example sentences showing different contexts
   Each: {{
     "en": "English sentence using the word naturally",
     "ru": "Russian translation (may omit the word if Russian doesn't use it)",
     "note": "Brief note in Russian about why the word is used here"
   }}

Make all explanations clear and practical for intermediate (B1) Russian-speaking learners.
Return ONLY the JSON object, no markdown or extra text."""
