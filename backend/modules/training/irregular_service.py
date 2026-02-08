"""Training service for irregular verbs."""

import random
from datetime import datetime, timezone
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.sql.expression import func

from backend.shared.text_utils import normalize_text, levenshtein_distance

from . import repository
from .exceptions import SessionAlreadyEndedError
from .schemas import (
    IrregularVerbAnswerResult,
    IrregularVerbAnswerSubmit,
    IrregularVerbExerciseResponse,
    IrregularVerbSessionResponse,
    SessionProgress,
    SessionSummary,
)


def _generate_irregular_verb_exercise(
    db: DBSession,
    irregular_verb_id: int,
    mastery_level: int,
) -> IrregularVerbExerciseResponse:
    """Generate an exercise for an irregular verb based on mastery level.

    Exercise types (1-6):
    1. Introduction - Show all 3 forms with audio
    2. Form Recognition - go → choose past: went/gone/goed
    3. Type Form - Type the past simple of "go": ___
    4. Sentence Fill - "Yesterday I ___ to school" (go)
    5. Reverse - went → what's the base form?
    6. Pattern - Which verb follows the same pattern as "sing-sang-sung"?
    """
    from backend.modules.words.models import IrregularVerb, IrregularVerbContext

    iv = db.query(IrregularVerb).filter(IrregularVerb.id == irregular_verb_id).first()
    if not iv:
        raise ValueError(f"IrregularVerb {irregular_verb_id} not found")

    context = (
        db.query(IrregularVerbContext)
        .filter(IrregularVerbContext.irregular_verb_id == irregular_verb_id)
        .first()
    )

    exercise_type = max(1, min(mastery_level, 6))

    exercise = IrregularVerbExerciseResponse(
        irregular_verb_id=irregular_verb_id,
        exercise_type=exercise_type,
        base_form=iv.base_form,
        past_simple=iv.past_simple,
        past_participle=iv.past_participle,
        translations=iv.translations or [],
        verb_pattern=iv.verb_pattern or "",
        transcription_base=iv.transcription_base,
        transcription_past=iv.transcription_past,
        transcription_participle=iv.transcription_participle,
        sentence_en=context.sentence_en if context else None,
        sentence_ru=context.sentence_ru if context else None,
    )

    # Type 2: Form Recognition - multiple choice for past/participle
    if exercise_type == 2:
        # Randomly choose which form to ask for
        target = random.choice(["past", "participle"])
        if target == "past":
            correct_form = iv.past_simple
            exercise.target_form = "past"
            exercise.given_form = iv.base_form
        else:
            correct_form = iv.past_participle
            exercise.target_form = "participle"
            exercise.given_form = iv.base_form

        distractors = _get_form_distractors(db, irregular_verb_id, target, count=3)
        # Add a common error form (e.g., "goed" for "go")
        if len(distractors) < 3:
            fake_form = iv.base_form + "ed"
            if fake_form not in distractors and fake_form != correct_form:
                distractors.append(fake_form)

        options = [correct_form] + distractors[:3]
        random.shuffle(options)
        exercise.options = options

    # Type 3: Type Form - write the past simple
    if exercise_type == 3:
        target = random.choice(["past", "participle"])
        exercise.target_form = target
        exercise.given_form = iv.base_form
        exercise.hint = f"Напишите {_form_name(target)} от глагола '{iv.base_form}'"

    # Type 4: Sentence Fill - fill in the blank with correct form
    if exercise_type == 4:
        if context and context.sentence_en:
            # Create sentence with blank
            verb_form = context.verb_form_used or "past"
            form_value = _get_form_by_name(iv, verb_form)
            exercise.sentence_en = context.sentence_en.replace(form_value, "___")
            exercise.target_form = verb_form
            exercise.given_form = iv.base_form
        else:
            # Generate a simple template sentence
            exercise.sentence_en = f"Yesterday I ___ (base: {iv.base_form})"
            exercise.target_form = "past"
            exercise.given_form = iv.base_form

    # Type 5: Reverse - given a form, identify the base
    if exercise_type == 5:
        # Show past or participle, ask for base
        source_form = random.choice(["past", "participle"])
        if source_form == "past":
            exercise.given_form = iv.past_simple
        else:
            exercise.given_form = iv.past_participle
        exercise.target_form = "base"

        distractors = _get_base_form_distractors(db, irregular_verb_id, count=3)
        options = [iv.base_form] + distractors
        random.shuffle(options)
        exercise.options = options

    # Type 6: Pattern Recognition - find verbs with same pattern
    if exercise_type == 6:
        same_pattern = _get_verbs_by_pattern(db, iv.verb_pattern, exclude_id=irregular_verb_id, count=1)
        different_pattern = _get_verbs_different_pattern(db, iv.verb_pattern, count=3)

        if same_pattern:
            correct_verb = same_pattern[0]
            options = [correct_verb.base_form] + [v.base_form for v in different_pattern[:3]]
            random.shuffle(options)
            exercise.options = options
            exercise.hint = f"Какой глагол образует формы так же, как {iv.base_form}-{iv.past_simple}-{iv.past_participle}?"
        else:
            # Fallback to type 3 if no same-pattern verb found
            exercise.exercise_type = 3
            exercise.target_form = "past"
            exercise.given_form = iv.base_form

    return exercise


def _form_name(form_type: str) -> str:
    """Get human-readable form name in Russian."""
    names = {
        "base": "инфинитив",
        "past": "past simple",
        "participle": "past participle",
    }
    return names.get(form_type, form_type)


def _get_form_by_name(iv, form_name: str) -> str:
    """Get form value by name."""
    if form_name == "base":
        return iv.base_form
    elif form_name == "past":
        return iv.past_simple
    else:
        return iv.past_participle


def _get_form_distractors(
    db: DBSession,
    irregular_verb_id: int,
    form_type: str,
    count: int = 3,
) -> list[str]:
    """Get distractor forms from other irregular verbs."""
    from backend.modules.words.models import IrregularVerb

    ivs = (
        db.query(IrregularVerb)
        .filter(IrregularVerb.id != irregular_verb_id)
        .order_by(func.random())
        .limit(count)
        .all()
    )
    forms = []
    for iv in ivs:
        if form_type == "past":
            forms.append(iv.past_simple)
        else:
            forms.append(iv.past_participle)
    return forms


def _get_base_form_distractors(
    db: DBSession,
    irregular_verb_id: int,
    count: int = 3,
) -> list[str]:
    """Get distractor base forms from other irregular verbs."""
    from backend.modules.words.models import IrregularVerb

    ivs = (
        db.query(IrregularVerb)
        .filter(IrregularVerb.id != irregular_verb_id)
        .order_by(func.random())
        .limit(count)
        .all()
    )
    return [iv.base_form for iv in ivs]


def _get_verbs_by_pattern(
    db: DBSession,
    pattern: str,
    exclude_id: int,
    count: int = 1,
) -> list:
    """Get verbs with the same conjugation pattern."""
    from backend.modules.words.models import IrregularVerb

    return (
        db.query(IrregularVerb)
        .filter(IrregularVerb.verb_pattern == pattern)
        .filter(IrregularVerb.id != exclude_id)
        .order_by(func.random())
        .limit(count)
        .all()
    )


def _get_verbs_different_pattern(
    db: DBSession,
    pattern: str,
    count: int = 3,
) -> list:
    """Get verbs with different conjugation patterns."""
    from backend.modules.words.models import IrregularVerb

    return (
        db.query(IrregularVerb)
        .filter(IrregularVerb.verb_pattern != pattern)
        .order_by(func.random())
        .limit(count)
        .all()
    )


def create_irregular_verb_session(
    db: DBSession, duration_minutes: int | None = None
) -> IrregularVerbSessionResponse:
    """Start a new training session for irregular verbs."""
    from backend.modules.learning.models import UserIrregularVerb
    from backend.modules.words.models import IrregularVerb
    from backend.modules.settings.repository import get_settings

    settings = get_settings(db)
    max_reviews = settings.max_reviews_per_session or 50
    daily_new = settings.daily_new_words or 10
    new_position = settings.new_words_position or "end"

    session = repository.create_session(db)

    now = datetime.now(timezone.utc)
    review_exercises: list[IrregularVerbExerciseResponse] = []
    new_exercises: list[IrregularVerbExerciseResponse] = []

    # Get overdue irregular verbs
    overdue = (
        db.query(UserIrregularVerb)
        .filter(UserIrregularVerb.next_review_at <= now)
        .order_by(UserIrregularVerb.next_review_at.asc())
        .limit(max_reviews)
        .all()
    )

    # Get irregular verbs in learning state
    learning_ids = {uiv.irregular_verb_id for uiv in overdue}
    learning = (
        db.query(UserIrregularVerb)
        .filter(UserIrregularVerb.fsrs_state.in_([1, 3]))
        .filter(UserIrregularVerb.irregular_verb_id.notin_(learning_ids))
        .limit(max_reviews // 2)
        .all()
    )

    # Get new irregular verbs
    existing_ids = db.query(UserIrregularVerb.irregular_verb_id).subquery()
    new_ivs = (
        db.query(IrregularVerb)
        .filter(IrregularVerb.id.notin_(existing_ids))
        .order_by(IrregularVerb.frequency_rank.asc().nullslast())
        .limit(daily_new)
        .all()
    )

    # Generate review exercises
    for uiv in overdue:
        if len(review_exercises) >= max_reviews:
            break
        try:
            ex = _generate_irregular_verb_exercise(db, uiv.irregular_verb_id, uiv.mastery_level)
            review_exercises.append(ex)
        except Exception:
            continue

    for uiv in learning:
        if len(review_exercises) >= max_reviews:
            break
        try:
            ex = _generate_irregular_verb_exercise(db, uiv.irregular_verb_id, uiv.mastery_level)
            review_exercises.append(ex)
        except Exception:
            continue

    # Generate new irregular verb exercises
    for iv in new_ivs:
        try:
            ex = _generate_irregular_verb_exercise(db, iv.id, 1)
            new_exercises.append(ex)
        except Exception:
            continue

    # Combine exercises
    exercises: list[IrregularVerbExerciseResponse] = []
    if new_position == "start":
        exercises = new_exercises + review_exercises
    elif new_position == "middle":
        mid = len(review_exercises) // 2
        exercises = review_exercises[:mid] + new_exercises + review_exercises[mid:]
    else:
        exercises = review_exercises + new_exercises

    repository.update_session(db, session.id, {
        "words_reviewed": len(review_exercises),
        "words_new": len(new_exercises),
    })

    return IrregularVerbSessionResponse(
        session_id=session.id,
        exercises=exercises,
        total_items=len(exercises),
    )


def record_irregular_verb_answer(
    db: DBSession,
    session_id: int,
    answer: IrregularVerbAnswerSubmit,
) -> IrregularVerbAnswerResult:
    """Evaluate a learner's answer for an irregular verb exercise."""
    from backend.modules.words.models import IrregularVerb
    from backend.modules.learning.service import IrregularVerbLearningService
    from backend.modules.learning.schemas import IrregularVerbReviewCreate
    from backend.modules.learning.repository import IrregularVerbLearningRepository

    session = repository.get_session(db, session_id)
    if session.ended_at is not None:
        raise SessionAlreadyEndedError(session_id)

    iv = db.query(IrregularVerb).filter(IrregularVerb.id == answer.irregular_verb_id).first()

    # Determine correct answer based on exercise type
    if answer.exercise_type == 1:
        # Introduction
        is_correct = True
        fsrs_rating = 4
        correct_answer = f"{iv.base_form} - {iv.past_simple} - {iv.past_participle}"
    elif answer.exercise_type in (2, 3, 4):
        # Form recognition, type form, sentence fill
        # Correct answer depends on target_form (stored client-side, passed in answer)
        # For simplicity, accept any correct form
        norm_answer = normalize_text(answer.answer)
        possible_correct = [
            normalize_text(iv.past_simple),
            normalize_text(iv.past_participle),
        ]
        # Handle forms with slashes like "was/were"
        for form in [iv.past_simple, iv.past_participle]:
            if "/" in form:
                possible_correct.extend([normalize_text(f) for f in form.split("/")])

        is_correct = norm_answer in possible_correct
        correct_answer = iv.past_simple  # Default to past simple
        fsrs_rating = 4 if is_correct else 1
    elif answer.exercise_type == 5:
        # Reverse - identify base form
        correct_answer = iv.base_form
        is_correct = normalize_text(answer.answer) == normalize_text(correct_answer)
        fsrs_rating = 4 if is_correct else 1
    elif answer.exercise_type == 6:
        # Pattern recognition
        # Answer should be the base form of another verb with same pattern
        same_pattern_verbs = (
            db.query(IrregularVerb)
            .filter(IrregularVerb.verb_pattern == iv.verb_pattern)
            .filter(IrregularVerb.id != iv.id)
            .all()
        )
        correct_bases = [normalize_text(v.base_form) for v in same_pattern_verbs]
        is_correct = normalize_text(answer.answer) in correct_bases
        correct_answer = same_pattern_verbs[0].base_form if same_pattern_verbs else iv.base_form
        fsrs_rating = 4 if is_correct else 1
    else:
        is_correct = False
        fsrs_rating = 1
        correct_answer = iv.base_form

    # Update session counters
    update_data: dict = {"total_count": session.total_count + 1}
    if is_correct:
        update_data["correct_count"] = session.correct_count + 1
    repository.update_session(db, session_id, update_data)

    # Initialize or update learning progress
    learning_service = IrregularVerbLearningService()
    learning_repo = IrregularVerbLearningRepository()

    user_iv = learning_repo.get_user_irregular_verb(db, answer.irregular_verb_id)
    if not user_iv:
        user_iv = learning_service.initialize_irregular_verb(db, answer.irregular_verb_id)

    review = IrregularVerbReviewCreate(
        exercise_type=answer.exercise_type,
        rating=fsrs_rating,
        response_time_ms=answer.response_time_ms,
        correct=is_correct,
    )
    mastery_result = learning_service.record_review(db, answer.irregular_verb_id, review)

    feedback = None
    if not is_correct:
        feedback = f"Правильный ответ: {correct_answer}"

    return IrregularVerbAnswerResult(
        correct=is_correct,
        rating=fsrs_rating,
        correct_answer=correct_answer,
        feedback=feedback,
        mastery_level=mastery_result.new_level,
        level_changed=mastery_result.level_changed,
    )
