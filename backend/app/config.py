"""
Configuration and Environment Management for AURA-Rx Backend
Uses Pydantic BaseSettings to read environment variables with strict typing.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API Metadata
    PROJECT_NAME: str = "AURA-Rx Backend - Explainable Multimodal AI for Handwritten Prescription Understanding"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Server Network Binding
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS Settings
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    # File Storage (Original Prescription Image Preservation)
    UPLOAD_DIR: Path = Path("backend/uploads")
    MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB
    ALLOWED_IMAGE_TYPES: List[str] = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/tiff",
        "image/bmp",
        "image/svg+xml",
    ]

    # Pipeline Mode (Phase 2 Mock Pipeline vs Future AI Modules)
    USE_MOCK_PIPELINE: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://localhost:8000",
        ]

    def ensure_upload_dir_exists(self) -> Path:
        """Guarantees that the upload directory exists for image storage."""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        return self.UPLOAD_DIR


@lru_cache()
def get_settings() -> Settings:
    """Returns cached singleton configuration instance."""
    settings = Settings()
    settings.ensure_upload_dir_exists()
    return settings
