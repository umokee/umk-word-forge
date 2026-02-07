from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///data/wordforge.db"
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    API_KEY: str = ""
    CORS_ORIGINS: str = "http://localhost:5173"
    DEBUG: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
