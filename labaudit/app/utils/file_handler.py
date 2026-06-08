"""
File handler utilities — validation, safe naming, MIME detection.
Used by DocumentService and the Streamlit upload widgets.
"""
from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path

from app.config import settings

# Allowed MIME types mapped to extensions
ALLOWED_MIME: dict[str, str] = {
    "application/pdf":                                                      "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":    "xlsx",
    "application/msword":                                                   "docx",
    "application/vnd.ms-excel":                                             "xlsx",
}


def validate_upload(file_bytes: bytes, file_name: str) -> tuple[bool, str]:
    """
    Returns (is_valid, error_message).
    Checks size and extension.
    """
    if len(file_bytes) > settings.max_upload_bytes:
        return False, f"File exceeds {settings.MAX_UPLOAD_MB} MB limit."

    ext = Path(file_name).suffix.lower().lstrip(".")
    if ext not in settings.allowed_extensions_list:
        allowed = ", ".join(f".{e}" for e in settings.allowed_extensions_list)
        return False, f"File type .{ext} not allowed. Accepted: {allowed}"

    return True, ""


def safe_filename(original: str, doc_id: str) -> str:
    """Return a filesystem-safe filename: {doc_id}.{ext}"""
    ext = Path(original).suffix.lower()
    return f"{doc_id}{ext}"


def file_checksum(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def human_file_size(size_bytes: int | None) -> str:
    if not size_bytes:
        return "—"
    for unit in ("B", "KB", "MB"):
        if size_bytes < 1024:
            return f"{size_bytes:.0f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} MB"


def get_file_icon(file_type: str | None) -> str:
    icons = {"pdf": "📄", "docx": "📝", "xlsx": "📊"}
    return icons.get((file_type or "").lower(), "📎")
