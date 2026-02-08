from sqlalchemy import Column, Integer, Float, Boolean, String, JSON
from backend.core.database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, default=1)

    # --- Training ---
    daily_new_words = Column(Integer, default=10)              # 1-50
    session_duration_minutes = Column(Integer, default=15)     # 5-60
    max_reviews_per_session = Column(Integer, default=50)      # 10-200
    new_words_position = Column(String, default="end")         # start/middle/end
    exercise_direction = Column(String, default="mixed")       # en_to_ru/ru_to_en/mixed
    show_transcription = Column(Boolean, default=True)
    show_example_translation = Column(Boolean, default=True)
    auto_play_audio = Column(Boolean, default=False)
    hint_delay_seconds = Column(Integer, default=10)           # 5-30
    preferred_exercises = Column(JSON, default=list)

    # --- Interface ---
    keyboard_shortcuts = Column(Boolean, default=True)
    show_progress_details = Column(Boolean, default=True)      # Show FSRS stats
    session_end_summary = Column(Boolean, default=True)
    animation_speed = Column(String, default="normal")         # fast/normal/slow/none
    font_size = Column(String, default="normal")               # small/normal/large

    # --- TTS ---
    tts_enabled = Column(Boolean, default=True)
    tts_speed = Column(Float, default=1.0)                     # 0.5-1.5
    tts_voice = Column(String, default="default")
    tts_auto_play_exercises = Column(Boolean, default=False)

    # --- Daily Goal ---
    daily_goal_type = Column(String, default="words")          # words/minutes/exercises
    daily_goal_value = Column(Integer, default=20)             # target value

    # --- AI ---
    gemini_api_key = Column(String, nullable=True)
    ai_feedback_language = Column(String, default="ru")        # ru/en
    ai_difficulty_context = Column(String, default="simple")   # simple/medium/natural
