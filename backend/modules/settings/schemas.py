from pydantic import BaseModel, Field


class SettingsResponse(BaseModel):
    # Training
    daily_new_words: int
    session_duration_minutes: int
    max_reviews_per_session: int
    new_words_position: str
    exercise_direction: str
    show_transcription: bool
    show_example_translation: bool
    auto_play_audio: bool
    hint_delay_seconds: int
    preferred_exercises: list

    # Interface
    keyboard_shortcuts: bool
    show_progress_details: bool
    session_end_summary: bool
    animation_speed: str
    font_size: str

    # TTS
    tts_enabled: bool
    tts_speed: float
    tts_voice: str
    tts_auto_play_exercises: bool

    # Daily Goal
    daily_goal_type: str
    daily_goal_value: int

    # AI
    gemini_api_key: str | None
    ai_feedback_language: str
    ai_difficulty_context: str

    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    # Training
    daily_new_words: int | None = Field(default=None, ge=1, le=50)
    session_duration_minutes: int | None = Field(default=None, ge=5, le=60)
    max_reviews_per_session: int | None = Field(default=None, ge=10, le=200)
    new_words_position: str | None = None
    exercise_direction: str | None = None
    show_transcription: bool | None = None
    show_example_translation: bool | None = None
    auto_play_audio: bool | None = None
    hint_delay_seconds: int | None = Field(default=None, ge=5, le=30)
    preferred_exercises: list | None = None

    # Interface
    keyboard_shortcuts: bool | None = None
    show_progress_details: bool | None = None
    session_end_summary: bool | None = None
    animation_speed: str | None = None
    font_size: str | None = None

    # TTS
    tts_enabled: bool | None = None
    tts_speed: float | None = Field(default=None, ge=0.5, le=1.5)
    tts_voice: str | None = None
    tts_auto_play_exercises: bool | None = None

    # Daily Goal
    daily_goal_type: str | None = None
    daily_goal_value: int | None = Field(default=None, ge=1, le=100)

    # AI
    gemini_api_key: str | None = None
    ai_feedback_language: str | None = None
    ai_difficulty_context: str | None = None
