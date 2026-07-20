from urllib.parse import urlencode

import httpx
import msal
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import RoleName, Settings
from app.core.security import create_access_token
from app.models.user import Role, User

SCOPES = ["openid", "profile", "email", "User.Read"]


class AuthService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._msal_app = None

    @property
    def oidc_configured(self) -> bool:
        return bool(self.settings.azure_client_id and self.settings.azure_tenant_id)

    def _get_msal_app(self):
        if not self.oidc_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OIDC no configurado. Defina AZURE_CLIENT_ID y AZURE_TENANT_ID.",
            )
        if self._msal_app is None:
            self._msal_app = msal.ConfidentialClientApplication(
                client_id=self.settings.azure_client_id,
                client_credential=self.settings.azure_client_secret,
                authority=self.settings.azure_authority,
            )
        return self._msal_app

    def get_login_url(self, state: str = "sgind") -> str:
        return self._get_msal_app().get_authorization_request_url(
            scopes=SCOPES,
            redirect_uri=self.settings.azure_redirect_uri,
            state=state,
        )

    async def handle_callback(self, code: str, db: AsyncSession) -> tuple[str, User]:
        result = self._get_msal_app().acquire_token_by_authorization_code(
            code=code,
            scopes=SCOPES,
            redirect_uri=self.settings.azure_redirect_uri,
        )
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error_description", "Error en autenticación OIDC"),
            )

        async with httpx.AsyncClient() as client:
            graph = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {result['access_token']}"},
            )
            graph.raise_for_status()
            profile = graph.json()

        email = (profile.get("mail") or profile.get("userPrincipalName", "")).lower()
        name = profile.get("displayName")
        azure_oid = profile.get("id")

        if self.settings.allowed_emails_set and email not in self.settings.allowed_emails_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email no autorizado",
            )

        user = await self._get_or_create_user(db, email=email, name=name, azure_oid=azure_oid)
        token = create_access_token(
            email,
            settings=self.settings,
            extra={"role": user.role.name, "name": name},
        )
        return token, user

    async def _get_or_create_user(
        self,
        db: AsyncSession,
        *,
        email: str,
        name: str | None,
        azure_oid: str | None,
        default_role: RoleName = "procesos",
    ) -> User:
        result = await db.execute(
            select(User).options(selectinload(User.role)).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        if user:
            if name and user.name != name:
                user.name = name
            if azure_oid and user.azure_oid != azure_oid:
                user.azure_oid = azure_oid
            return user

        role_result = await db.execute(select(Role).where(Role.name == default_role))
        role = role_result.scalar_one_or_none()
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Rol '{default_role}' no existe en la base de datos",
            )

        user = User(email=email, name=name, role_id=role.id, azure_oid=azure_oid)
        db.add(user)
        await db.flush()
        await db.refresh(user, attribute_names=["role"])
        return user

    async def ensure_dev_user(
        self,
        db: AsyncSession,
        *,
        email: str,
        role_name: RoleName = "calidad",
        name: str | None = "Usuario desarrollo",
    ) -> User:
        return await self._get_or_create_user(
            db,
            email=email.lower(),
            name=name,
            azure_oid=None,
            default_role=role_name,
        )

    def get_logout_url(self) -> str:
        params = urlencode(
            {
                "post_logout_redirect_uri": self.settings.cors_origins_list[0]
                if self.settings.cors_origins_list
                else "http://localhost:3000",
            }
        )
        return f"{self.settings.azure_authority}/oauth2/v2.0/logout?{params}"
