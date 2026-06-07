"""
Auth service — login, token management, and RBAC permission checks.
Streamlit keeps the current user in st.session_state["current_user"].
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.utils.security import verify_password, create_access_token, decode_access_token

logger = logging.getLogger(__name__)


class AuthError(Exception):
    pass


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.log_repo = AuditLogRepository(db)

    # ─── Login ────────────────────────────────────────────────────────────────

    def login(self, email: str, password: str, ip: str | None = None) -> tuple[User, str]:
        """
        Authenticate user. Returns (user, jwt_token) or raises AuthError.
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            raise AuthError("Invalid email or password.")
        if not user.is_active:
            raise AuthError("This account has been deactivated.")
        if not verify_password(password, user.hashed_password):
            logger.warning("Failed login attempt for %s from %s", email, ip)
            self.log_repo.log(
                action="user.login_failed",
                org_id=user.org_id,
                summary=f"Failed login for {email}",
                ip_address=ip,
            )
            raise AuthError("Invalid email or password.")

        # Update last_login
        user.last_login = datetime.now(timezone.utc)
        self.db.flush()

        token = create_access_token({
            "sub": str(user.id),
            "org_id": str(user.org_id),
            "role": user.role.value,
        })

        self.log_repo.log(
            action="user.login",
            org_id=user.org_id,
            user_id=user.id,
            summary=f"{user.full_name} logged in",
            ip_address=ip,
        )
        logger.info("User %s logged in", email)
        return user, token

    def get_user_from_token(self, token: str) -> User | None:
        payload = decode_access_token(token)
        if not payload:
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        return self.user_repo.get_by_id(__import__("uuid").UUID(user_id))

    # ─── RBAC helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def require_role(user: User, minimum_role: UserRole) -> None:
        """Raise AuthError if user doesn't meet the minimum role level."""
        hierarchy = {UserRole.VIEWER: 0, UserRole.MANAGER: 1, UserRole.ADMIN: 2}
        if hierarchy.get(user.role, -1) < hierarchy.get(minimum_role, 99):
            raise AuthError(
                f"Permission denied. Required role: {minimum_role.value}. "
                f"Your role: {user.role.value}."
            )

    @staticmethod
    def can_write(user: User) -> bool:
        return user.role in (UserRole.ADMIN, UserRole.MANAGER)

    @staticmethod
    def can_admin(user: User) -> bool:
        return user.role == UserRole.ADMIN

    # ─── User management ──────────────────────────────────────────────────────

    def create_user(
        self,
        *,
        org_id,
        email: str,
        password: str,
        full_name: str,
        role: UserRole,
        job_title: str | None = None,
        department: str | None = None,
        created_by: User,
    ) -> User:
        AuthService.require_role(created_by, UserRole.ADMIN)

        if self.user_repo.email_exists(email):
            raise AuthError(f"Email {email} is already registered.")

        from app.utils.security import hash_password
        import uuid
        user = User(
            id=uuid.uuid4(),
            org_id=org_id,
            email=email.lower().strip(),
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
            job_title=job_title,
            department=department,
            is_active=True,
        )
        self.user_repo.create(user)
        self.log_repo.log(
            action="user.create",
            org_id=org_id,
            user_id=created_by.id,
            entity_type="user",
            entity_id=str(user.id),
            summary=f"Created user {email} with role {role.value}",
        )
        return user

    def change_password(
        self, user: User, old_password: str, new_password: str
    ) -> None:
        if not verify_password(old_password, user.hashed_password):
            raise AuthError("Current password is incorrect.")
        from app.utils.security import hash_password
        user.hashed_password = hash_password(new_password)
        self.db.flush()
        self.log_repo.log(
            action="user.password_change",
            org_id=user.org_id,
            user_id=user.id,
            summary="Password changed",
        )
