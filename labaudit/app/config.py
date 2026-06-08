from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from typing import List
import os


class Settings(BaseSettings):
    # ─── Database ────────────────────────────────────────
    DATABASE_URL: str = "postgresql+pg8000://labaudit:labaudit_pass@db:5432/labaudit_db"

    # ─── Security ─────────────────────────────────────────
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480

    # ─── App ──────────────────────────────────────────────
    APP_NAME: str = "LabAudit"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # ─── File Storage ─────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_MB: int = 20
    ALLOWED_EXTENSIONS: str = "pdf,docx,xlsx"

    # ─── Seed ─────────────────────────────────────────────
    SEED_DEMO_DATA: bool = True

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
