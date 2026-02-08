from sqlalchemy import Column, Integer, Float, Boolean, JSON
from backend.core.database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, default=1)
    daily_new_words = Column(Integer, default=10)
    session_duration_minutes = Column(Integer, default=15)
    preferred_exercises = Column(JSON, default=list)
    tts_enabled = Column(Boolean, default=True)
    tts_speed = Column(Float, default=1.0)
    keyboard_shortcuts = Column(Boolean, default=True)
