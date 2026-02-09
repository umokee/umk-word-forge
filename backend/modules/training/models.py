from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship

from backend.core.database import Base


class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, default=func.now())
    ended_at = Column(DateTime, nullable=True)
    words_reviewed = Column(Integer, default=0)
    words_new = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    duration_seconds = Column(Integer, default=0)

    # Relationship to new word progress tracking
    new_word_progress = relationship("SessionNewWordProgress", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<TrainingSession id={self.id} total={self.total_count}>"


class SessionNewWordProgress(Base):
    """Tracks progress for new words within a training session.

    New words must complete all 4 exercise types (Intro, Recognition, Recall, Context)
    and get at least 3 correct before being added to UserWord.
    """
    __tablename__ = "session_new_word_progress"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("training_sessions.id"), nullable=False, index=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False, index=True)

    # Track each exercise type result (NULL = not attempted, True/False = result)
    exercise_1_correct = Column(Boolean, nullable=True)  # Introduction
    exercise_2_correct = Column(Boolean, nullable=True)  # Recognition
    exercise_3_correct = Column(Boolean, nullable=True)  # Recall
    exercise_4_correct = Column(Boolean, nullable=True)  # Context

    # Whether the word was "learned" (added to UserWord) after session
    learned = Column(Boolean, default=False)

    session = relationship("TrainingSession", back_populates="new_word_progress")

    def __repr__(self) -> str:
        return f"<SessionNewWordProgress session={self.session_id} word={self.word_id}>"

    def get_correct_count(self) -> int:
        """Count how many exercises were answered correctly."""
        results = [
            self.exercise_1_correct,
            self.exercise_2_correct,
            self.exercise_3_correct,
            self.exercise_4_correct,
        ]
        return sum(1 for r in results if r is True)

    def is_complete(self) -> bool:
        """Check if all 4 exercise types have been attempted."""
        return all([
            self.exercise_1_correct is not None,
            self.exercise_2_correct is not None,
            self.exercise_3_correct is not None,
            self.exercise_4_correct is not None,
        ])
