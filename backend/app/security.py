"""Autenticación (JWT) y autorización (RBAC con ámbito)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .enums import Role
from .models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# auto_error=False: permite que la UI (cookies) y la API (header) convivan.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user: User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user.id), "role": user.role.value, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email, User.active.is_(True)).first()
    if user and verify_password(password, user.hashed_password):
        return user
    return None


def _decode_user(token: str | None, db: Session) -> User | None:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        return None
    return db.get(User, user_id)


def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    # Acepta el token del header Authorization (API) o de la cookie (UI Jinja).
    token = token or request.cookies.get("access_token")
    user = _decode_user(token, db)
    if not user or not user.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No autenticado")
    return user


def require_roles(*roles: Role):
    """Dependencia que exige uno de los roles dados."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role != Role.ADMIN and user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Permiso insuficiente para esta acción")
        return user

    return checker


def in_scope(user: User, *, company_id: int | None, department_id: int | None) -> bool:
    """¿Está la entidad dentro del ámbito del usuario? ADMIN/HR/ACCOUNTING => global."""
    if user.role in (Role.ADMIN, Role.HR, Role.ACCOUNTING, Role.VIEWER):
        return True
    if user.scope_company_id and user.scope_company_id != company_id:
        return False
    if user.scope_department_id and user.scope_department_id != department_id:
        return False
    return True
