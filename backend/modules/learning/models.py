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
