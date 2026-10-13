"""
Configuration and Environment Management for DawaAI Backend
Uses Pydantic BaseSettings to read environment variables with strict typing.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Union, Optional
from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine project root and load environment variables early
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / ".env")


class Settings(BaseSettings):
    # API Metadata
    PROJECT_NAME: str = "DawaAI Backend - Explainable Multimodal AI for Handwritten Prescription Understanding"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Server Network Binding - defaults to port 8001 per DawaAI local development standard
    HOST: str = "127.0.0.1"
    PORT: int = 8001

    # Model Credentials (Optional in mock/evaluation mode)
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API Key")

    # CORS Settings
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
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

    # Pipeline Mode (Mock Pipeline vs Multimodal AI Modules)
    USE_MOCK_PIPELINE: bool = True

    model_config = SettingsConfigDict(
        env_file=(str(ROOT_DIR / ".env"), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        default_local = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:8001",
            "http://127.0.0.1:8001",
        ]
        if isinstance(v, str) and not v.startswith("["):
            origins = [i.strip() for i in v.split(",") if i.strip()]
            for loc in default_local:
                if loc not in origins:
                    origins.append(loc)
            return origins
        elif isinstance(v, list):
            origins = list(v)
            for loc in default_local:
                if loc not in origins:
                    origins.append(loc)
            return origins
        return default_local

    def ensure_upload_dir_exists(self) -> Path:
        """Guarantees that the upload and samples directories exist for image storage."""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        samples_dir = self.UPLOAD_DIR / "samples"
        samples_dir.mkdir(parents=True, exist_ok=True)
        return self.UPLOAD_DIR


@lru_cache()
def get_settings() -> Settings:
    """Returns cached singleton configuration instance."""
    settings = Settings()
    settings.ensure_upload_dir_exists()
    return settings

