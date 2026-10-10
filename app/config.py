import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application configuration settings loaded from .env with fallback defaults."""
    APP_NAME: str = "Bulk Certificate Generator Backend"
    DATABASE_URL: str = "sqlite:///./certificates.db"
    OUTPUT_DIR: Path = Path("generated")
    TEMPLATE_DIR: Path = Path("app/templates")
    MAX_RECIPIENTS_PER_REQUEST: int = 1000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure output directory exists
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
