"""
Configuration and Environment Management for DawaAI Backend
Uses Pydantic BaseSettings to read environment variables with strict typing.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Union, Optional
from dotenv import load_dotenv
from pydantic import Field, field_validator, model_validator
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

    # Runtime Environment & Inference Mode Enforcement
    ENV: str = Field(default="development", description="Runtime environment: 'development', 'staging', 'production', or 'test'")
    ENVIRONMENT: Optional[str] = Field(default=None, description="Alias for ENV")
    INFERENCE_MODE: Optional[str] = Field(default=None, description="Inference mode: 'live' or 'mock'. Overrides USE_MOCK_PIPELINE if set.")

    # Server Network Binding - binds to 0.0.0.0 for container/PaaS routing compatibility
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    # Model Credentials and Multimodal Configuration
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API Key")
    GOOGLE_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API Key Fallback")
    GEMINI_MODEL: str = Field(default="gemini-3.5-flash-lite", description="Google Gemini Model Identifier")
    MULTIMODAL_MODEL_ID: Optional[str] = Field(default="gemini-3.5-flash-lite", description="Multimodal Model Identifier")
    MULTIMODAL_MAX_TOKENS: int = Field(default=4096, description="Max Output Generation Tokens")
    MULTIMODAL_TIMEOUT_SECONDS: float = Field(default=50.0, description="Inference Timeout Seconds")

    # CORS Settings
    CORS_ORIGINS: Union[List[str], str] = [
        "https://dawaai-prescription-decoder.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ]

    # File Storage & Ephemeral PHI Retention (Zero-Retention by default)
    UPLOAD_DIR: Path = Path("backend/uploads")
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB strict limit
    RETENTION_TTL_SECONDS: int = Field(
        default=3600,
        description="Ephemeral PHI retention TTL in seconds. 0 indicates zero-retention (immediate deletion after request). Defaults to 0 in production.",
    )
    ALLOWED_IMAGE_TYPES: List[str] = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/tiff",
        "image/bmp",
        "image/svg+xml",
    ]

    # API Authentication & Rate Limiting
    API_KEY: Optional[str] = Field(default=None, description="Optional API key for protected endpoints")
    REQUIRE_API_KEY: bool = Field(default=False, description="Whether API key authentication is strictly required")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Max requests per minute per client IP")

    # Pipeline Mode (Mock Pipeline vs Multimodal AI Modules)
    USE_MOCK_PIPELINE: bool = False

    model_config = SettingsConfigDict(
        env_file=(str(ROOT_DIR / ".env"), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def sync_inference_mode_and_validate(self) -> "Settings":
        # Resolve active environment identifier
        env_val = (self.ENVIRONMENT or self.ENV or os.environ.get("ENV") or os.environ.get("ENVIRONMENT") or "development").strip()
        object.__setattr__(self, "ENV", env_val)

        # Synchronize INFERENCE_MODE if provided
        if self.INFERENCE_MODE:
            inf = self.INFERENCE_MODE.lower().strip()
            if inf == "live":
                object.__setattr__(self, "USE_MOCK_PIPELINE", False)
            elif inf == "mock":
                object.__setattr__(self, "USE_MOCK_PIPELINE", True)

        # Strict security constraint: Mock pipeline execution is forbidden in production
        env_str = env_val.lower()
        is_mock = self.USE_MOCK_PIPELINE or (self.INFERENCE_MODE and self.INFERENCE_MODE.lower().strip() == "mock")
        if env_str == "production" and is_mock:
            raise ValueError(
                "Configuration Validation Error: Mock pipeline execution is strictly forbidden in production environment (ENV=production)."
            )

        # Strict security constraint: Disallow wildcard CORS and strip localhost/127.0.0.1 when in production with custom origins
        if env_str == "production" and isinstance(self.CORS_ORIGINS, list):
            custom_non_local = [
                o for o in self.CORS_ORIGINS
                if o.strip() != "*" and not o.startswith("http://localhost") and not o.startswith("http://127.0.0.1")
            ]
            if custom_non_local:
                object.__setattr__(self, "CORS_ORIGINS", custom_non_local)
            else:
                sanitized_origins = [o for o in self.CORS_ORIGINS if o.strip() != "*"]
                object.__setattr__(self, "CORS_ORIGINS", sanitized_origins)

        # Default RETENTION_TTL_SECONDS to 0 in production unless explicitly overridden in environment
        if env_str == "production" and "RETENTION_TTL_SECONDS" not in os.environ:
            object.__setattr__(self, "RETENTION_TTL_SECONDS", 0)

        return self

    @property
    def is_live_mode(self) -> bool:
        if self.INFERENCE_MODE:
            return self.INFERENCE_MODE.lower().strip() == "live"
        return not self.USE_MOCK_PIPELINE

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        default_local = [
            "https://dawaai-prescription-decoder.vercel.app",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:8001",
            "http://127.0.0.1:8001",
        ]
        active_env = (os.environ.get("ENV") or os.environ.get("ENVIRONMENT") or "development").strip().lower()
        is_prod = active_env == "production"

        if isinstance(v, str) and not v.startswith("["):
            origins = [i.strip() for i in v.split(",") if i.strip()]
            if not is_prod:
                for loc in default_local:
                    if loc not in origins:
                        origins.append(loc)
            return origins
        elif isinstance(v, list):
            origins = list(v)
            if not is_prod:
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

