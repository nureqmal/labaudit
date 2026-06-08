from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower().strip())
        return self.db.scalar(stmt)

    def get_by_org(self, org_id: uuid.UUID, active_only: bool = True) -> list[User]:
        stmt = select(User).where(User.org_id == org_id)
        if active_only:
            stmt = stmt.where(User.is_active == True)  # noqa: E712
        stmt = stmt.order_by(User.full_name)
        return list(self.db.scalars(stmt).all())

    def get_by_role(self, org_id: uuid.UUID, role: UserRole) -> list[User]:
        stmt = (
            select(User)
            .where(User.org_id == org_id, User.role == role, User.is_active == True)  # noqa: E712
            .order_by(User.full_name)
        )
        return list(self.db.scalars(stmt).all())

    def email_exists(self, email: str, exclude_id: uuid.UUID | None = None) -> bool:
        stmt = select(User).where(User.email == email.lower().strip())
        if exclude_id:
            stmt = stmt.where(User.id != exclude_id)
        return self.db.scalar(stmt) is not None
