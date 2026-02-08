from datetime import datetime, timezone
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from backend.modules.learning.models import UserWord, Review
from backend.modules.learning.schemas import ReviewCreate
from backend.modules.words.models import Word


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
