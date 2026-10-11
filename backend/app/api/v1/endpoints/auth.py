from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import get_current_user, require_reader
from app.models.user import User
from app.schemas.common import (
    EmailLoginRequest,
    EmailOtpVerify,
    LoginResponse,
    MessageResponse,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter()


def _auth_service(settings: Settings = Depends(get_settings)) -> AuthService:
    return AuthService(settings)


@router.get("/login")
async def login(
    auth: AuthService = Depends(_auth_service),
):
    """Redirige al navegador directamente a Azure AD OAuth."""
    return RedirectResponse(url=auth.get_login_url())


@router.get("/login-url", response_model=LoginResponse)
async def login_url(
    auth: AuthService = Depends(_auth_service),
) -> LoginResponse:
    """Devuelve la URL de Azure AD para flujos que necesitan el JSON (SPA, tests)."""
    return LoginResponse(authorization_url=auth.get_login_url())


@router.get("/callback")
async def callback(
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    auth: AuthService = Depends(_auth_service),
    settings: Settings = Depends(get_settings),
):
    frontend = (
        settings.cors_origins_list[0] if settings.cors_origins_list else "http://localhost:3000"
    )
    if error or not code:
        # p. ej. el usuario canceló, o el admin del tenant no permite el consentimiento
        return RedirectResponse(url=f"{frontend}/login?error=access_denied")
    auth.verify_state(state)
    token, _user = await auth.handle_callback(code, db)
    return RedirectResponse(url=f"{frontend}/auth/callback?token={token}")


@router.post("/email-login/request", response_model=MessageResponse)
async def email_login_request(
    payload: EmailLoginRequest,
    db: AsyncSession = Depends(get_db),
    auth: AuthService = Depends(_auth_service),
) -> MessageResponse:
    """Paso 1: envía un código de 6 dígitos al correo institucional."""
    await auth.request_otp(db, email=payload.email)
    return MessageResponse(message="Si el correo está autorizado, recibirás un código.")


@router.post("/email-login/verify", response_model=TokenResponse)
async def email_login_verify(
    payload: EmailOtpVerify,
    db: AsyncSession = Depends(get_db),
    auth: AuthService = Depends(_auth_service),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Paso 2: valida el código (un solo uso) y emite el JWT."""
    token, _user = await auth.verify_otp(db, email=payload.email, code=payload.code)
    return TokenResponse(access_token=token, expires_in=settings.jwt_expire_minutes * 60)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/logout", response_model=MessageResponse)
async def logout(
    _user: User = Depends(require_reader),
    auth: AuthService = Depends(_auth_service),
) -> MessageResponse:
    return MessageResponse(message="Sesión cerrada", detail={"logout_url": auth.get_logout_url()})


@router.post("/dev-token", response_model=TokenResponse, include_in_schema=False)
async def dev_token(
    email: str = Query("dev@poligran.edu.co"),
    role: str = Query("calidad"),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Solo desarrollo — genera JWT sin OIDC ni BD.

    Requiere ENABLE_DEV_AUTH=true explícito. Antes se bloqueaba solo si
    environment=="production", lo que dejaba el endpoint activo en
    cualquier staging/QA con otro nombre de entorno (ver G-04)."""
    if not settings.enable_dev_auth:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    from app.core.config import RoleName
    from app.core.security import create_access_token

    role_name: RoleName = (
        role
        if role in ("procesos", "calidad", "desempeno", "administrador", "auditor_ia")
        else "calidad"
    )
    name = f"Dev {role_name.capitalize()}"
    token = create_access_token(
        email,
        settings=settings,
        extra={"role": role_name, "name": name},
    )
    return TokenResponse(access_token=token, expires_in=settings.jwt_expire_minutes * 60)
