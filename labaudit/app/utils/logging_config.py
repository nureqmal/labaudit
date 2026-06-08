"""
Logging configuration for LabAudit.
Call setup_logging() once at app startup.
"""
import logging
import logging.handlers
import os
from pathlib import Path

from app.config import settings


def setup_logging() -> None:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Console handler ───────────────────────────────────
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    console.setLevel(level)

    # ── Rotating file handler ─────────────────────────────
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "labaudit.log",
        maxBytes=5 * 1024 * 1024,   # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(level)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(console)
    root.addHandler(file_handler)

    # Quiet noisy third-party loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("streamlit").setLevel(logging.WARNING)
