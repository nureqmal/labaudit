import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)

# Fix bcrypt 4.x + passlib compatibility
try:
    import bcrypt as _bcrypt
    if not hasattr(_bcrypt, '__about__'):
        _bcrypt.__about__ = type('a', (), {'__version__': _bcrypt.__version__})()
except Exception:
    pass

from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    import bcrypt as _bcrypt
    pw = plain.encode("utf-8")[:72]
    return _bcrypt.hashpw(pw, _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    import bcrypt as _bcrypt
    pw = plain.encode("utf-8")[:72]
    return _bcrypt.checkpw(pw, hashed.encode("utf-8"))


def create_access_token(data: dict[str, Any], expires_minutes: int | None = None) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.JWT_EXPIRE_MINUTES
    )
    payload.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as e:
        logger.warning("JWT decode failed: %s", e)
        return None
