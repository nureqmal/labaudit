import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from sqlalchemy.pool import QueuePool

from app.config import settings

logger = logging.getLogger(__name__)


# ─── Declarative Base ─────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ─── Engine ───────────────────────────────────────────────────────────────────

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,          # reconnect on stale connections
    pool_recycle=3600,           # recycle connections every hour
    echo=settings.DEBUG,
)


# ─── Session Factory ──────────────────────────────────────────────────────────

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,      # keep objects usable after commit
)


# ─── Dependency / Context Manager ─────────────────────────────────────────────

def get_db() -> Generator[Session, None, None]:
    """FastAPI-style dependency — use as a context manager in Streamlit."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Explicit context manager for use in service/repository layers."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("DB session rollback due to: %s", e)
        raise
    finally:
        db.close()


def init_db() -> None:
    """Create all tables (used in dev / first-run). Prod uses Alembic."""
    logger.info("Initialising database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")


def check_db_connection() -> bool:
    """Health check — returns True if DB is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("DB connection check failed: %s", e)
        return False
