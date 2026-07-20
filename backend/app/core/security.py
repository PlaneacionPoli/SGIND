from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import RoleName, Settings, get_settings
from app.core.database import get_db
from app.models.user import User

security = HTTPBearer(auto_error=False)

ADMIN_ROLES: set[RoleName] = {"calidad", "desempeno"}


def create_access_token(
    subject: str,
    *,
    settings: Settings,
    extra: dict[str, Any] | None = None,
) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        ) from exc


def _dev_user_from_payload(payload: dict[str, Any]) -> Any:
    """Construye un objeto user-like desde el payload JWT sin consultar la BD."""
    email = payload.get("sub", "dev@poligran.edu.co")
    role_name = payload.get("role", "calidad")
    name = payload.get("name", f"Dev {role_name.capitalize()}")
    role = SimpleNamespace(name=role_name)
    return SimpleNamespace(email=email, name=name, role=role, is_active=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Any:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida",
        )

    payload = decode_token(credentials.credentials, settings)
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    if settings.environment == "development":
        return _dev_user_from_payload(payload)

    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.email == email.lower())
    )
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autorizado")
    return user


def require_roles(*roles: RoleName):
    async def checker(user: User = Depends(get_current_user)) -> User:
        role_name = user.role.name if user.role else None
        if role_name not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permisos insuficientes",
            )
        return user

    return checker


require_admin = require_roles("calidad", "desempeno")
require_reader = require_roles("procesos", "calidad", "desempeno")
