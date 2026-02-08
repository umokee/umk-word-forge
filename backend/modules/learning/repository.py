from datetime import datetime, timezone
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from backend.modules.learning.models import (
    UserWord,
    Review,
    UserPhrasalVerb,
    PhrasalVerbReview,
    UserIrregularVerb,
    IrregularVerbReview,
)
from backend.modules.learning.schemas import ReviewCreate
from backend.modules.words.models import Word, PhrasalVerb, IrregularVerb


class LearningRepository:

    @staticmethod
    def get_user_word(db: Session, word_id: int) -> UserWord | None:
        return (
            db.query(UserWord)
            .filter(UserWord.word_id == word_id)
            .first()
        )

    @staticmethod
    def get_user_words(
        db: Session,
        page: int = 1,
        per_page: int = 20,
        level_filter: int | None = None,
        state_filter: int | None = None,
    ) -> tuple[list[UserWord], int]:
        query = db.query(UserWord)

        if level_filter is not None:
            query = query.filter(UserWord.mastery_level == level_filter)

        if state_filter is not None:
            query = query.filter(UserWord.fsrs_state == state_filter)

        total = query.count()

        items = (
            query.order_by(UserWord.next_review_at.asc().nullsfirst(), UserWord.id.asc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return items, total

    @staticmethod
    def get_due_words(db: Session, limit: int = 50) -> list[UserWord]:
        now = datetime.now(timezone.utc)

        return (
            db.query(UserWord)
            .filter(
                (UserWord.next_review_at <= now)
                | (UserWord.fsrs_state.in_([1, 3]))  # Learning or Relearning
            )
            .order_by(UserWord.next_review_at.asc().nullsfirst())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_new_word_ids(db: Session, limit: int = 10) -> list[int]:
        existing_word_ids = db.query(UserWord.word_id).subquery()

        new_words = (
            db.query(Word.id)
            .filter(Word.id.notin_(existing_word_ids))
            .order_by(Word.frequency_rank.asc().nullslast(), Word.id.asc())
            .limit(limit)
            .all()
        )

        return [row[0] for row in new_words]

    @staticmethod
    def create_user_word(db: Session, word_id: int, **kwargs) -> UserWord:
        user_word = UserWord(word_id=word_id, **kwargs)
        db.add(user_word)
        db.commit()
        db.refresh(user_word)
        return user_word

    @staticmethod
    def update_user_word(db: Session, user_word: UserWord) -> UserWord:
        db.commit()
        db.refresh(user_word)
        return user_word

    @staticmethod
    def create_review(db: Session, user_word_id: int, review_data: ReviewCreate) -> Review:
        review = Review(
            user_word_id=user_word_id,
            exercise_type=review_data.exercise_type,
            rating=review_data.rating,
            response_time_ms=review_data.response_time_ms,
            correct=review_data.correct,
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return review

    @staticmethod
    def get_learning_stats(db: Session) -> dict:
        total = db.query(func.count(UserWord.id)).scalar() or 0
        return {"total_words": total}

    @staticmethod
    def count_by_level(db: Session) -> dict[int, int]:
        rows = (
            db.query(UserWord.mastery_level, func.count(UserWord.id))
            .group_by(UserWord.mastery_level)
            .all()
        )
        return {level: count for level, count in rows}

    @staticmethod
    def count_by_state(db: Session) -> dict[int, int]:
        rows = (
            db.query(UserWord.fsrs_state, func.count(UserWord.id))
            .group_by(UserWord.fsrs_state)
            .all()
        )
        return {state: count for state, count in rows}


class PhrasalVerbLearningRepository:
    """Repository for UserPhrasalVerb progress tracking."""

    @staticmethod
    def get_user_phrasal_verb(db: Session, phrasal_verb_id: int) -> UserPhrasalVerb | None:
        return (
            db.query(UserPhrasalVerb)
            .filter(UserPhrasalVerb.phrasal_verb_id == phrasal_verb_id)
            .first()
        )

    @staticmethod
    def get_user_phrasal_verbs(
        db: Session,
        page: int = 1,
        per_page: int = 20,
        level_filter: int | None = None,
        state_filter: int | None = None,
    ) -> tuple[list[UserPhrasalVerb], int]:
        query = db.query(UserPhrasalVerb)

        if level_filter is not None:
            query = query.filter(UserPhrasalVerb.mastery_level == level_filter)

        if state_filter is not None:
            query = query.filter(UserPhrasalVerb.fsrs_state == state_filter)

        total = query.count()

        items = (
            query.order_by(
                UserPhrasalVerb.next_review_at.asc().nullsfirst(), UserPhrasalVerb.id.asc()
            )
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return items, total

    @staticmethod
    def get_due_phrasal_verbs(db: Session, limit: int = 50) -> list[UserPhrasalVerb]:
        now = datetime.now(timezone.utc)

        return (
            db.query(UserPhrasalVerb)
            .filter(
                (UserPhrasalVerb.next_review_at <= now)
                | (UserPhrasalVerb.fsrs_state.in_([1, 3]))
            )
            .order_by(UserPhrasalVerb.next_review_at.asc().nullsfirst())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_new_phrasal_verb_ids(db: Session, limit: int = 10) -> list[int]:
        existing_ids = db.query(UserPhrasalVerb.phrasal_verb_id).subquery()

        new_items = (
            db.query(PhrasalVerb.id)
            .filter(PhrasalVerb.id.notin_(existing_ids))
            .order_by(
                PhrasalVerb.frequency_rank.asc().nullslast(), PhrasalVerb.id.asc()
            )
            .limit(limit)
            .all()
        )

        return [row[0] for row in new_items]

    @staticmethod
    def create_user_phrasal_verb(
        db: Session, phrasal_verb_id: int, **kwargs
    ) -> UserPhrasalVerb:
        user_pv = UserPhrasalVerb(phrasal_verb_id=phrasal_verb_id, **kwargs)
        db.add(user_pv)
        db.commit()
        db.refresh(user_pv)
        return user_pv

    @staticmethod
    def update_user_phrasal_verb(
        db: Session, user_pv: UserPhrasalVerb
    ) -> UserPhrasalVerb:
        db.commit()
        db.refresh(user_pv)
        return user_pv

    @staticmethod
    def create_review(
        db: Session,
        user_phrasal_verb_id: int,
        exercise_type: int,
        rating: int,
        response_time_ms: int,
        correct: bool,
    ) -> PhrasalVerbReview:
        review = PhrasalVerbReview(
            user_phrasal_verb_id=user_phrasal_verb_id,
            exercise_type=exercise_type,
            rating=rating,
            response_time_ms=response_time_ms,
            correct=correct,
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return review

    @staticmethod
    def get_learning_stats(db: Session) -> dict:
        total = db.query(func.count(UserPhrasalVerb.id)).scalar() or 0
        return {"total_phrasal_verbs": total}

    @staticmethod
    def count_by_level(db: Session) -> dict[int, int]:
        rows = (
            db.query(UserPhrasalVerb.mastery_level, func.count(UserPhrasalVerb.id))
            .group_by(UserPhrasalVerb.mastery_level)
            .all()
        )
        return {level: count for level, count in rows}

    @staticmethod
    def count_by_state(db: Session) -> dict[int, int]:
        rows = (
            db.query(UserPhrasalVerb.fsrs_state, func.count(UserPhrasalVerb.id))
            .group_by(UserPhrasalVerb.fsrs_state)
            .all()
        )
        return {state: count for state, count in rows}


class IrregularVerbLearningRepository:
    """Repository for UserIrregularVerb progress tracking."""

    @staticmethod
    def get_user_irregular_verb(
        db: Session, irregular_verb_id: int
    ) -> UserIrregularVerb | None:
        return (
            db.query(UserIrregularVerb)
            .filter(UserIrregularVerb.irregular_verb_id == irregular_verb_id)
            .first()
        )

    @staticmethod
    def get_user_irregular_verbs(
        db: Session,
        page: int = 1,
        per_page: int = 20,
        level_filter: int | None = None,
        state_filter: int | None = None,
    ) -> tuple[list[UserIrregularVerb], int]:
        query = db.query(UserIrregularVerb)

        if level_filter is not None:
            query = query.filter(UserIrregularVerb.mastery_level == level_filter)

        if state_filter is not None:
            query = query.filter(UserIrregularVerb.fsrs_state == state_filter)

        total = query.count()

        items = (
            query.order_by(
                UserIrregularVerb.next_review_at.asc().nullsfirst(),
                UserIrregularVerb.id.asc(),
            )
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return items, total

    @staticmethod
    def get_due_irregular_verbs(db: Session, limit: int = 50) -> list[UserIrregularVerb]:
        now = datetime.now(timezone.utc)

        return (
            db.query(UserIrregularVerb)
            .filter(
                (UserIrregularVerb.next_review_at <= now)
                | (UserIrregularVerb.fsrs_state.in_([1, 3]))
            )
            .order_by(UserIrregularVerb.next_review_at.asc().nullsfirst())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_new_irregular_verb_ids(db: Session, limit: int = 10) -> list[int]:
        existing_ids = db.query(UserIrregularVerb.irregular_verb_id).subquery()

        new_items = (
            db.query(IrregularVerb.id)
            .filter(IrregularVerb.id.notin_(existing_ids))
            .order_by(
                IrregularVerb.frequency_rank.asc().nullslast(), IrregularVerb.id.asc()
            )
            .limit(limit)
            .all()
        )

        return [row[0] for row in new_items]

    @staticmethod
    def create_user_irregular_verb(
        db: Session, irregular_verb_id: int, **kwargs
    ) -> UserIrregularVerb:
        user_iv = UserIrregularVerb(irregular_verb_id=irregular_verb_id, **kwargs)
        db.add(user_iv)
        db.commit()
        db.refresh(user_iv)
        return user_iv

    @staticmethod
    def update_user_irregular_verb(
        db: Session, user_iv: UserIrregularVerb
    ) -> UserIrregularVerb:
        db.commit()
        db.refresh(user_iv)
        return user_iv

    @staticmethod
    def create_review(
        db: Session,
        user_irregular_verb_id: int,
        exercise_type: int,
        rating: int,
        response_time_ms: int,
        correct: bool,
    ) -> IrregularVerbReview:
        review = IrregularVerbReview(
            user_irregular_verb_id=user_irregular_verb_id,
            exercise_type=exercise_type,
            rating=rating,
            response_time_ms=response_time_ms,
            correct=correct,
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return review

    @staticmethod
    def get_learning_stats(db: Session) -> dict:
        total = db.query(func.count(UserIrregularVerb.id)).scalar() or 0
        return {"total_irregular_verbs": total}

    @staticmethod
    def count_by_level(db: Session) -> dict[int, int]:
        rows = (
            db.query(UserIrregularVerb.mastery_level, func.count(UserIrregularVerb.id))
            .group_by(UserIrregularVerb.mastery_level)
            .all()
        )
        return {level: count for level, count in rows}

    @staticmethod
    def count_by_state(db: Session) -> dict[int, int]:
        rows = (
            db.query(UserIrregularVerb.fsrs_state, func.count(UserIrregularVerb.id))
            .group_by(UserIrregularVerb.fsrs_state)
            .all()
        )
        return {state: count for state, count in rows}
