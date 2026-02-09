"""Daily training session tracking model."""

from sqlalchemy import Column, Integer, String, Date, DateTime

from backend.core.database import Base


class DailyTrainingSession(Base):
    """Tracks completed training sessions per category per day."""

    __tablename__ = "daily_training_sessions"

    id = Column(Integer, primary_key=True)
    category = Column(String, index=True)  # "words", "phrasal", "irregular"
    training_date = Column(Date, index=True)
    session_id = Column(Integer, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<DailyTrainingSession id={self.id} category='{self.category}' date={self.training_date}>"
