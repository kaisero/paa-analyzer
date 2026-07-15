"""Application settings."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    upload_dir: Path = Path("uploads")
    max_upload_bytes: int = 500 * 1024 * 1024  # 500 MB
    default_page_size: int = 100
    max_page_size: int = 500

    model_config = {"env_prefix": "PAA_"}


settings = Settings()
