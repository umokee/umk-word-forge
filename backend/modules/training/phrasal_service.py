"""Training service for phrasal verbs."""

import random
from datetime import datetime, timezone
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.sql.expression import func

from backend.shared.text_utils import normalize_text, levenshtein_distance

from . import repository
from .exceptions import SessionAlreadyEndedError
from .schemas import (
    PhrasalVerbAnswerResult,
    PhrasalVerbAnswerSubmit,
    PhrasalVerbExerciseResponse,
    PhrasalVerbSessionResponse,
    SessionProgress,
    SessionSummary,
)


# Common particles for distractor generation
COMMON_PARTICLES = [
    "up", "down", "in", "out", "on", "off", "over", "away",
    "back", "through", "around", "along", "across", "about",
    "after", "for", "into", "by", "at", "with",
]


def _generate_phrasal_verb_exercise(
    db: DBSession,
    phrasal_verb_id: int,
    mastery_level: int,
) -> PhrasalVerbExerciseResponse:
    """Generate an exercise for a phrasal verb based on mastery level.

    Exercise types (1-6):
    1. Introduction - Show phrase, meaning, example, separability
    2. Meaning Match - Choose correct meaning from 4 options
    3. Particle Fill - "I need to look ___ the word" (up/for/at/down)
    4. Context - Choose correct phrasal verb for situation
    5. Separability - "look it up" or "look up it"?
    6. Production - Write sentence with phrasal verb
    """
    from backend.modules.words.models import PhrasalVerb, PhrasalVerbContext

    pv = db.query(PhrasalVerb).filter(PhrasalVerb.id == phrasal_verb_id).first()
    if not pv:
        raise ValueError(f"PhrasalVerb {phrasal_verb_id} not found")

    context = (
        db.query(PhrasalVerbContext)
        .filter(PhrasalVerbContext.phrasal_verb_id == phrasal_verb_id)
        .first()
    )

    exercise_type = max(1, min(mastery_level, 6))

    exercise = PhrasalVerbExerciseResponse(
        phrasal_verb_id=phrasal_verb_id,
        exercise_type=exercise_type,
        phrase=pv.phrase,
        base_verb=pv.base_verb,
        particle=pv.particle,
        translations=pv.translations or [],
        definitions=pv.definitions or [],
        is_separable=pv.is_separable,
        sentence_en=context.sentence_en if context else None,
        sentence_ru=context.sentence_ru if context else None,
    )

    # Type 2: Meaning Match - multiple choice with meaning distractors
    if exercise_type == 2:
        correct_meaning = pv.translations[0] if pv.translations else ""
        distractors = _get_meaning_distractors(db, phrasal_verb_id, count=3)
        options = [correct_meaning] + distractors
        random.shuffle(options)
        exercise.options = options

    # Type 3: Particle Fill - choose correct particle
    if exercise_type == 3:
        correct_particle = pv.particle
        # Get particles from other phrasal verbs with same base verb
        other_particles = _get_particle_distractors(db, pv.base_verb, correct_particle, count=3)
        particle_options = [correct_particle] + other_particles
        random.shuffle(particle_options)
        exercise.particle_options = particle_options
        # Create sentence with blank for particle
        if context and context.sentence_en:
            exercise.hint = context.sentence_en.replace(pv.phrase, f"{pv.base_verb} ___")

    # Type 4: Context - choose correct phrasal verb for context
    if exercise_type == 4:
        distractors = _get_phrasal_verb_distractors(db, phrasal_verb_id, count=3)
        options = [pv.phrase] + distractors
        random.shuffle(options)
        exercise.options = options

    # Type 5: Separability - correct word order
    if exercise_type == 5 and pv.is_separable:
        # Create examples of correct and incorrect order
        correct = f"{pv.base_verb} it {pv.particle}"  # Separable: look it up
        incorrect = f"{pv.base_verb} {pv.particle} it"  # look up it (wrong for separable)
        exercise.separability_options = [correct, incorrect]
        random.shuffle(exercise.separability_options)
    elif exercise_type == 5 and not pv.is_separable:
        # For inseparable: "look at it" is correct
        correct = f"{pv.phrase} it"  # look at it
        incorrect = f"{pv.base_verb} it {pv.particle}"  # look it at (wrong)
        exercise.separability_options = [correct, incorrect]
        random.shuffle(exercise.separability_options)

    # Type 6: Production - write a sentence
    if exercise_type == 6:
        exercise.hint = f"Напишите предложение с фразовым глаголом '{pv.phrase}'"

    return exercise


def _get_meaning_distractors(
    db: DBSession,
    phrasal_verb_id: int,
    count: int = 3,
) -> list[str]:
    """Get distractor translations from other phrasal verbs."""
    from backend.modules.words.models import PhrasalVerb

    pvs = (
        db.query(PhrasalVerb)
        .filter(PhrasalVerb.id != phrasal_verb_id)
        .order_by(func.random())
        .limit(count)
        .all()
    )
    distractors = []
    for pv in pvs:
        if pv.translations:
            distractors.append(pv.translations[0])
    return distractors


def _get_particle_distractors(
    db: DBSession,
    base_verb: str,
    correct_particle: str,
    count: int = 3,
) -> list[str]:
    """Get distractor particles from other phrasal verbs."""
    from backend.modules.words.models import PhrasalVerb

    # First try to get particles from same base verb
    same_verb_particles = (
        db.query(PhrasalVerb.particle)
        .filter(PhrasalVerb.base_verb == base_verb)
        .filter(PhrasalVerb.particle != correct_particle)
        .distinct()
        .limit(count)
        .all()
    )
    particles = [p[0] for p in same_verb_particles]

    # Fill with common particles if needed
    while len(particles) < count:
        for p in COMMON_PARTICLES:
            if p != correct_particle and p not in particles:
                particles.append(p)
                if len(particles) >= count:
                    break

    return particles[:count]


def _get_phrasal_verb_distractors(
    db: DBSession,
    phrasal_verb_id: int,
    count: int = 3,
) -> list[str]:
    """Get distractor phrasal verbs."""
    from backend.modules.words.models import PhrasalVerb

    pvs = (
        db.query(PhrasalVerb)
        .filter(PhrasalVerb.id != phrasal_verb_id)
        .order_by(func.random())
        .limit(count)
        .all()
    )
    return [pv.phrase for pv in pvs]


def create_phrasal_verb_session(
    db: DBSession, duration_minutes: int | None = None
) -> PhrasalVerbSessionResponse:
    """Start a new training session for phrasal verbs."""
    from backend.modules.learning.models import UserPhrasalVerb
    from backend.modules.words.models import PhrasalVerb
    from backend.modules.settings.repository import get_settings

    settings = get_settings(db)
    max_reviews = settings.max_reviews_per_session or 50
    daily_new = settings.daily_new_words or 10
    new_position = settings.new_words_position or "end"

    session = repository.create_session(db)

    now = datetime.now(timezone.utc)
    review_exercises: list[PhrasalVerbExerciseResponse] = []
    new_exercises: list[PhrasalVerbExerciseResponse] = []

    # Get overdue phrasal verbs
    overdue = (
        db.query(UserPhrasalVerb)
        .filter(UserPhrasalVerb.next_review_at <= now)
        .order_by(UserPhrasalVerb.next_review_at.asc())
        .limit(max_reviews)
        .all()
    )

    # Get phrasal verbs in learning state
    learning_ids = {upv.phrasal_verb_id for upv in overdue}
    learning = (
        db.query(UserPhrasalVerb)
        .filter(UserPhrasalVerb.fsrs_state.in_([1, 3]))
        .filter(UserPhrasalVerb.phrasal_verb_id.notin_(learning_ids))
        .limit(max_reviews // 2)
        .all()
    )

    # Get new phrasal verbs
    existing_ids = db.query(UserPhrasalVerb.phrasal_verb_id).subquery()
    new_pvs = (
        db.query(PhrasalVerb)
        .filter(PhrasalVerb.id.notin_(existing_ids))
        .order_by(PhrasalVerb.frequency_rank.asc().nullslast())
        .limit(daily_new)
        .all()
    )

    # Generate review exercises
    for upv in overdue:
        if len(review_exercises) >= max_reviews:
            break
        try:
            ex = _generate_phrasal_verb_exercise(db, upv.phrasal_verb_id, upv.mastery_level)
            review_exercises.append(ex)
        except Exception:
            continue

    for upv in learning:
        if len(review_exercises) >= max_reviews:
            break
        try:
            ex = _generate_phrasal_verb_exercise(db, upv.phrasal_verb_id, upv.mastery_level)
            review_exercises.append(ex)
        except Exception:
            continue

    # Generate new phrasal verb exercises
    for pv in new_pvs:
        try:
            ex = _generate_phrasal_verb_exercise(db, pv.id, 1)
            new_exercises.append(ex)
        except Exception:
            continue

    # Combine exercises
    exercises: list[PhrasalVerbExerciseResponse] = []
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

    return PhrasalVerbSessionResponse(
        session_id=session.id,
        exercises=exercises,
        total_items=len(exercises),
    )


def record_phrasal_verb_answer(
    db: DBSession,
    session_id: int,
    answer: PhrasalVerbAnswerSubmit,
) -> PhrasalVerbAnswerResult:
    """Evaluate a learner's answer for a phrasal verb exercise."""
    from backend.modules.words.models import PhrasalVerb
    from backend.modules.learning.service import PhrasalVerbLearningService
    from backend.modules.learning.schemas import PhrasalVerbReviewCreate
    from backend.modules.learning.repository import PhrasalVerbLearningRepository

    session = repository.get_session(db, session_id)
    if session.ended_at is not None:
        raise SessionAlreadyEndedError(session_id)

    pv = db.query(PhrasalVerb).filter(PhrasalVerb.id == answer.phrasal_verb_id).first()

    # Determine correct answer based on exercise type
    if answer.exercise_type == 1:
        # Introduction
        is_correct = True
        fsrs_rating = 4
        correct_answer = pv.phrase
    elif answer.exercise_type == 2:
        # Meaning match
        correct_answer = pv.translations[0] if pv and pv.translations else ""
        is_correct, score = _evaluate_answer(answer.answer, correct_answer)
        fsrs_rating = _score_to_rating(is_correct, score)
    elif answer.exercise_type == 3:
        # Particle fill
        correct_answer = pv.particle if pv else ""
        is_correct = normalize_text(answer.answer) == normalize_text(correct_answer)
        fsrs_rating = 4 if is_correct else 1
    elif answer.exercise_type == 4:
        # Context
        correct_answer = pv.phrase if pv else ""
        is_correct = normalize_text(answer.answer) == normalize_text(correct_answer)
        fsrs_rating = 4 if is_correct else 1
    elif answer.exercise_type == 5:
        # Separability
        if pv and pv.is_separable:
            correct_answer = f"{pv.base_verb} it {pv.particle}"
        else:
            correct_answer = f"{pv.phrase} it"
        is_correct = normalize_text(answer.answer) == normalize_text(correct_answer)
        fsrs_rating = 4 if is_correct else 1
    else:
        # Production - more lenient, check if phrase is in answer
        correct_answer = pv.phrase if pv else ""
        norm_answer = normalize_text(answer.answer)
        is_correct = normalize_text(correct_answer) in norm_answer
        fsrs_rating = 3 if is_correct else 1

    # Update session counters
    update_data: dict = {"total_count": session.total_count + 1}
    if is_correct:
        update_data["correct_count"] = session.correct_count + 1
    repository.update_session(db, session_id, update_data)

    # Initialize or update learning progress
    learning_service = PhrasalVerbLearningService()
    learning_repo = PhrasalVerbLearningRepository()

    user_pv = learning_repo.get_user_phrasal_verb(db, answer.phrasal_verb_id)
    if not user_pv:
        user_pv = learning_service.initialize_phrasal_verb(db, answer.phrasal_verb_id)

    review = PhrasalVerbReviewCreate(
        exercise_type=answer.exercise_type,
        rating=fsrs_rating,
        response_time_ms=answer.response_time_ms,
        correct=is_correct,
    )
    mastery_result = learning_service.record_review(db, answer.phrasal_verb_id, review)

    feedback = None
    if not is_correct:
        feedback = f"Правильный ответ: {correct_answer}"

    return PhrasalVerbAnswerResult(
        correct=is_correct,
        rating=fsrs_rating,
        correct_answer=correct_answer,
        feedback=feedback,
        mastery_level=mastery_result.new_level,
        level_changed=mastery_result.level_changed,
    )


def _evaluate_answer(submitted: str, correct: str) -> tuple[bool, int]:
    """Compare submitted answer to expected one with typo tolerance."""
    norm_submitted = normalize_text(submitted)
    norm_correct = normalize_text(correct)

    if norm_submitted == norm_correct:
        return True, 5

    distance = levenshtein_distance(norm_submitted, norm_correct)
    if distance <= 1 and len(norm_correct) > 3:
        return True, 3

    return False, 0


def _score_to_rating(is_correct: bool, score: int) -> int:
    """Convert score to FSRS rating (1-4)."""
    if not is_correct:
        return 1
    elif score >= 5:
        return 4
    elif score >= 3:
        return 3
    else:
        return 2
