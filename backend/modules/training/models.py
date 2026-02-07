from sqlalchemy import Column, Integer, DateTime, func

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

    def __repr__(self) -> str:
        return f"<TrainingSession id={self.id} total={self.total_count}>"
