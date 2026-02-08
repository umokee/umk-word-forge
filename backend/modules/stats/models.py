from sqlalchemy import Column, Integer, Float, Date
from backend.core.database import Base


class DailyStats(Base):
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True, index=True)
    words_reviewed = Column(Integer, default=0)
    words_learned = Column(Integer, default=0)
    time_spent = Column(Integer, default=0)
    accuracy = Column(Float, default=0)
    streak = Column(Integer, default=0)
