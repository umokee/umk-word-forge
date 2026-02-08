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


def generate_contexts_prompt(word: str, part_of_speech: str, count: int = 3) -> str:
    """Build a prompt that asks the AI to generate example sentences."""
    return f"""You are an English language tutor creating example sentences for a Russian-speaking student at A1-A2 level.

Generate {count} example sentences using the word "{word}" (part of speech: {part_of_speech}).

Requirements:
- Sentences should be at A1-A2 difficulty level (simple, everyday vocabulary)
- Each sentence should demonstrate a different common usage of the word
- Include a Russian translation for each sentence
- Rate difficulty as "A1" or "A2"

Return a JSON array where each element has exactly these fields:
- "en" (str): the English sentence
- "ru" (str): the Russian translation
- "difficulty" (str): "A1" or "A2"

Return ONLY the JSON array, no extra text or markdown formatting."""
