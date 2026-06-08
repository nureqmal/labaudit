"""
Generic base repository — all entity repositories inherit from this.
Provides standard CRUD + pagination without repeating boilerplate.
"""
from __future__ import annotations

import uuid
import logging
from typing import Any, Generic, TypeVar, Type

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.database import Base

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Usage:
        class DocumentRepository(BaseRepository[Document]):
            model = Document
    """

    model: Type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    # ─── Read ─────────────────────────────────────────────────────────────────

    def get_by_id(self, record_id: uuid.UUID) -> ModelT | None:
        return self.db.get(self.model, record_id)

    def get_all(
        self,
        org_id: uuid.UUID,
        *,
        limit: int = 50,
        offset: int = 0,
        filters: list[Any] | None = None,
        order_by: Any | None = None,
    ) -> list[ModelT]:
        stmt = select(self.model).where(self.model.org_id == org_id)
        if filters:
            stmt = stmt.where(and_(*filters))
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        stmt = stmt.limit(limit).offset(offset)
        return list(self.db.scalars(stmt).all())

    def count(
        self,
        org_id: uuid.UUID,
        filters: list[Any] | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(self.model).where(
            self.model.org_id == org_id
        )
        if filters:
            stmt = stmt.where(and_(*filters))
        return self.db.scalar(stmt) or 0

    # ─── Write ────────────────────────────────────────────────────────────────

    def create(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        self.db.flush()
        logger.debug("Created %s id=%s", self.model.__name__, obj.id)
        return obj

    def update(self, obj: ModelT, **kwargs: Any) -> ModelT:
        for field, value in kwargs.items():
            if hasattr(obj, field):
                setattr(obj, field, value)
        self.db.flush()
        return obj

    def delete(self, obj: ModelT) -> None:
        self.db.delete(obj)
        self.db.flush()

    # ─── Pagination helper ────────────────────────────────────────────────────

    def paginate(
        self,
        org_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        filters: list[Any] | None = None,
        order_by: Any | None = None,
    ) -> tuple[list[ModelT], int]:
        """Returns (items, total_count) for the requested page."""
        offset = (page - 1) * page_size
        items = self.get_all(
            org_id,
            limit=page_size,
            offset=offset,
            filters=filters,
            order_by=order_by,
        )
        total = self.count(org_id, filters=filters)
        return items, total
