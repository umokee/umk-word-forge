"""Private exercise generators for each mastery level.

Each function builds an ExerciseResponse tailored to a specific exercise type
(level 1-7). These are internal helpers consumed by the training service and
should not be imported outside this module.
"""

import random

from backend.shared.text_utils import get_translations, get_first_translation
from .schemas import ExerciseResponse


def _shuffle_options(correct: str, distractors: list[str], count: int = 4) -> list[str]:
    """Pick distractors, add the correct answer, and shuffle."""
    pool = [d for d in distractors if d != correct]
    chosen = random.sample(pool, min(count - 1, len(pool)))
    options = chosen + [correct]
    random.shuffle(options)
    return options


def _scramble_sentence(sentence: str) -> list[str]:
    """Split a sentence into words and shuffle their order."""
    words = sentence.split()
    scrambled = words[:]
    # Ensure the scrambled order differs from original when possible
    for _ in range(10):
        random.shuffle(scrambled)
        if scrambled != words:
            break
    return scrambled


# ---------------------------------------------------------------------------
# Level 1 -- Introduction
# ---------------------------------------------------------------------------

def generate_introduction(word, contexts: list | None = None) -> ExerciseResponse:
    """Show the word with its translation and example context.

    The learner is presented the full card; no response is expected beyond
    acknowledging they have seen the word.
    """
    sentence_en = None
    sentence_ru = None
    if contexts:
        ctx = random.choice(contexts)
        sentence_en = ctx.sentence_en
        sentence_ru = getattr(ctx, "sentence_ru", None)

    return ExerciseResponse(
        word_id=word.id,
        exercise_type=1,
        english=word.english,
        transcription=word.transcription,
        translations=get_translations(word),
        part_of_speech=word.part_of_speech,
        sentence_en=sentence_en,
        sentence_ru=sentence_ru,
        hint="Study the word and its meaning.",
    )


# ---------------------------------------------------------------------------
# Level 2 -- Recognition (multiple choice)
# ---------------------------------------------------------------------------

def generate_recognition(word, distractors: list[str]) -> ExerciseResponse:
    """Multiple-choice: match the word to its translation (or vice versa).

    ~30 % of the time the exercise is reversed (given translation, pick the
    English word).
    """
    reverse = random.random() < 0.3
    primary_translation = get_first_translation(word)

    if reverse:
        # Given the Russian translation, choose the correct English word
        options = _shuffle_options(word.english, distractors)
        return ExerciseResponse(
            word_id=word.id,
            exercise_type=2,
            english=word.english,
            transcription=word.transcription,
            translations=get_translations(word),
            part_of_speech=word.part_of_speech,
            options=options,
            reverse=True,
            hint="Choose the correct English word.",
        )
    else:
        # Given the English word, choose the correct translation
        options = _shuffle_options(primary_translation, distractors)
        return ExerciseResponse(
            word_id=word.id,
            exercise_type=2,
            english=word.english,
            transcription=word.transcription,
            translations=get_translations(word),
            part_of_speech=word.part_of_speech,
            options=options,
            reverse=False,
            hint="Choose the correct translation.",
        )


# ---------------------------------------------------------------------------
# Level 3 -- Recall (type the answer)
# ---------------------------------------------------------------------------

def generate_recall(word) -> ExerciseResponse:
    """The learner must type the translation from memory."""
    return ExerciseResponse(
        word_id=word.id,
        exercise_type=3,
        english=word.english,
        transcription=word.transcription,
        translations=get_translations(word),
        part_of_speech=word.part_of_speech,
        hint="Type the translation for this word.",
    )


# ---------------------------------------------------------------------------
# Level 4 -- Context (multiple choice with sentence)
# ---------------------------------------------------------------------------

def generate_context(word, context, distractors: list[str]) -> ExerciseResponse:
    """Choose the correct word to fill a gap in a sentence."""
    primary_translation = get_first_translation(word)
    options = _shuffle_options(primary_translation, distractors)

    sentence_en = context.sentence_en if context else None
    sentence_ru = getattr(context, "sentence_ru", None) if context else None

    return ExerciseResponse(
        word_id=word.id,
        exercise_type=4,
        english=word.english,
        transcription=word.transcription,
        translations=get_translations(word),
        part_of_speech=word.part_of_speech,
        options=options,
        sentence_en=sentence_en,
        sentence_ru=sentence_ru,
        hint="Choose the correct translation in this context.",
    )


# ---------------------------------------------------------------------------
# Level 5 -- Sentence Builder
# ---------------------------------------------------------------------------

def generate_sentence_builder(word, context) -> ExerciseResponse:
    """Rearrange scrambled words to form a correct sentence."""
    sentence_en = context.sentence_en if context else word.english
    sentence_ru = getattr(context, "sentence_ru", None) if context else None
    scrambled = _scramble_sentence(sentence_en)

    return ExerciseResponse(
        word_id=word.id,
        exercise_type=5,
        english=word.english,
        transcription=word.transcription,
        translations=get_translations(word),
        part_of_speech=word.part_of_speech,
        sentence_en=sentence_en,
        sentence_ru=sentence_ru,
        scrambled_words=scrambled,
        hint="Arrange the words to form the correct sentence.",
    )


# ---------------------------------------------------------------------------
# Level 6 -- Free Production
# ---------------------------------------------------------------------------

def generate_free_production(word) -> ExerciseResponse:
    """The learner writes their own sentence using the target word."""
    return ExerciseResponse(
        word_id=word.id,
        exercise_type=6,
        english=word.english,
        transcription=word.transcription,
        translations=get_translations(word),
        part_of_speech=word.part_of_speech,
        hint="Write a sentence using this word.",
    )


# ---------------------------------------------------------------------------
# Level 7 -- Listening (context-based)
# ---------------------------------------------------------------------------

def generate_listening(word, context) -> ExerciseResponse:
    """The learner listens (or reads a context) and types the target word."""
    sentence_en = context.sentence_en if context else None
    sentence_ru = getattr(context, "sentence_ru", None) if context else None

    return ExerciseResponse(
        word_id=word.id,
        exercise_type=7,
        english=word.english,
        transcription=word.transcription,
        translations=get_translations(word),
        part_of_speech=word.part_of_speech,
        sentence_en=sentence_en,
        sentence_ru=sentence_ru,
        hint="Listen to the context and type the target word.",
    )
