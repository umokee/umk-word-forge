from pydantic import BaseModel, Field


class SettingsResponse(BaseModel):
    daily_new_words: int
    session_duration_minutes: int
    preferred_exercises: list
    tts_enabled: bool
    tts_speed: float
    keyboard_shortcuts: bool

    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    daily_new_words: int | None = None
    session_duration_minutes: int | None = None
    preferred_exercises: list | None = None
    tts_enabled: bool | None = None
    tts_speed: float | None = Field(default=None, ge=0.5, le=2.0)
    keyboard_shortcuts: bool | None = None
