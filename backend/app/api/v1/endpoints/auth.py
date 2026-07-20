from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import get_current_user, require_reader
from app.models.user import User
from app.schemas.common import LoginResponse, MessageResponse, TokenResponse, UserResponse
from app.services.auth_service import AuthService
from sqlalchemy.ext.asyncio import AsyncSession

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
    code: str = Query(...),
    db: AsyncSession = Depends(get_db),
    auth: AuthService = Depends(_auth_service),
    settings: Settings = Depends(get_settings),
):
    token, _user = await auth.handle_callback(code, db)
    frontend = settings.cors_origins_list[0] if settings.cors_origins_list else "http://localhost:3000"
    return RedirectResponse(url=f"{frontend}/auth/callback?token={token}")


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
    """Solo desarrollo — genera JWT sin OIDC ni BD."""
    if settings.environment == "production":
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    from app.core.config import RoleName
    from app.core.security import create_access_token

    role_name: RoleName = role if role in ("procesos", "calidad", "desempeno") else "calidad"
    name = f"Dev {role_name.capitalize()}"
    token = create_access_token(
        email,
        settings=settings,
        extra={"role": role_name, "name": name},
    )
    return TokenResponse(access_token=token, expires_in=settings.jwt_expire_minutes * 60)
