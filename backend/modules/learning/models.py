from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from backend.core.database import Base


class UserWord(Base):
    __tablename__ = "user_words"

    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False, unique=True, index=True)
    mastery_level = Column(Integer, default=0)
    consecutive_correct = Column(Integer, default=0)
    consecutive_wrong = Column(Integer, default=0)
    fsrs_stability = Column(Float, default=0)
    fsrs_difficulty = Column(Float, default=0)
    fsrs_elapsed_days = Column(Integer, default=0)
    fsrs_scheduled_days = Column(Integer, default=0)
    fsrs_reps = Column(Integer, default=0)
    fsrs_lapses = Column(Integer, default=0)
    fsrs_state = Column(Integer, default=0)  # 0=New, 1=Learning, 2=Review, 3=Relearning
    fsrs_last_review = Column(DateTime, nullable=True)
    next_review_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())

    reviews = relationship("Review", back_populates="user_word", cascade="all,delete")

    def __repr__(self) -> str:
        return f"<UserWord id={self.id} word_id={self.word_id} level={self.mastery_level}>"


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    user_word_id = Column(Integer, ForeignKey("user_words.id"), nullable=False)
    exercise_type = Column(Integer)
    rating = Column(Integer)  # 1=Again, 2=Hard, 3=Good, 4=Easy
    response_time_ms = Column(Integer)
    correct = Column(Boolean)
    created_at = Column(DateTime, default=func.now())

    user_word = relationship("UserWord", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<Review id={self.id} user_word_id={self.user_word_id} rating={self.rating}>"


class UserPhrasalVerb(Base):
    """User's learning progress for phrasal verbs with FSRS scheduling."""

    __tablename__ = "user_phrasal_verbs"

    id = Column(Integer, primary_key=True)
    phrasal_verb_id = Column(
        Integer, ForeignKey("phrasal_verbs.id"), nullable=False, unique=True, index=True
    )
    mastery_level = Column(Integer, default=0)  # 0-6 for phrasal verb exercises
    consecutive_correct = Column(Integer, default=0)
    consecutive_wrong = Column(Integer, default=0)
    fsrs_stability = Column(Float, default=0)
    fsrs_difficulty = Column(Float, default=0)
    fsrs_elapsed_days = Column(Integer, default=0)
    fsrs_scheduled_days = Column(Integer, default=0)
    fsrs_reps = Column(Integer, default=0)
    fsrs_lapses = Column(Integer, default=0)
    fsrs_state = Column(Integer, default=0)  # 0=New, 1=Learning, 2=Review, 3=Relearning
    fsrs_last_review = Column(DateTime, nullable=True)
    next_review_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())

    reviews = relationship(
        "PhrasalVerbReview", back_populates="user_phrasal_verb", cascade="all,delete"
    )

    def __repr__(self) -> str:
        return f"<UserPhrasalVerb id={self.id} phrasal_verb_id={self.phrasal_verb_id} level={self.mastery_level}>"


class PhrasalVerbReview(Base):
    """Individual review record for a phrasal verb exercise."""

    __tablename__ = "phrasal_verb_reviews"

    id = Column(Integer, primary_key=True)
    user_phrasal_verb_id = Column(
        Integer, ForeignKey("user_phrasal_verbs.id"), nullable=False
    )
    exercise_type = Column(Integer)  # 1-6 for phrasal verb exercise types
    rating = Column(Integer)  # 1=Again, 2=Hard, 3=Good, 4=Easy
    response_time_ms = Column(Integer)
    correct = Column(Boolean)
    created_at = Column(DateTime, default=func.now())

    user_phrasal_verb = relationship("UserPhrasalVerb", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<PhrasalVerbReview id={self.id} user_phrasal_verb_id={self.user_phrasal_verb_id} rating={self.rating}>"


class UserIrregularVerb(Base):
    """User's learning progress for irregular verbs with FSRS scheduling."""

    __tablename__ = "user_irregular_verbs"

    id = Column(Integer, primary_key=True)
    irregular_verb_id = Column(
        Integer, ForeignKey("irregular_verbs.id"), nullable=False, unique=True, index=True
    )
    mastery_level = Column(Integer, default=0)  # 0-6 for irregular verb exercises
    consecutive_correct = Column(Integer, default=0)
    consecutive_wrong = Column(Integer, default=0)
    fsrs_stability = Column(Float, default=0)
    fsrs_difficulty = Column(Float, default=0)
    fsrs_elapsed_days = Column(Integer, default=0)
    fsrs_scheduled_days = Column(Integer, default=0)
    fsrs_reps = Column(Integer, default=0)
    fsrs_lapses = Column(Integer, default=0)
    fsrs_state = Column(Integer, default=0)  # 0=New, 1=Learning, 2=Review, 3=Relearning
    fsrs_last_review = Column(DateTime, nullable=True)
    next_review_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())

    reviews = relationship(
        "IrregularVerbReview", back_populates="user_irregular_verb", cascade="all,delete"
    )

    def __repr__(self) -> str:
        return f"<UserIrregularVerb id={self.id} irregular_verb_id={self.irregular_verb_id} level={self.mastery_level}>"


class IrregularVerbReview(Base):
    """Individual review record for an irregular verb exercise."""

    __tablename__ = "irregular_verb_reviews"

    id = Column(Integer, primary_key=True)
    user_irregular_verb_id = Column(
        Integer, ForeignKey("user_irregular_verbs.id"), nullable=False
    )
    exercise_type = Column(Integer)  # 1-6 for irregular verb exercise types
    rating = Column(Integer)  # 1=Again, 2=Hard, 3=Good, 4=Easy
    response_time_ms = Column(Integer)
    correct = Column(Boolean)
    created_at = Column(DateTime, default=func.now())

    user_irregular_verb = relationship("UserIrregularVerb", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<IrregularVerbReview id={self.id} user_irregular_verb_id={self.user_irregular_verb_id} rating={self.rating}>"
