import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
import msal
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import RoleName, Settings
from app.core.security import create_access_token, decode_token
from app.models.login_otp import LoginOtp
from app.models.user import Role, User
from app.services.otp_mailer import send_otp

# Mismas descripciones que database/migrations/001 y 004.
_ROLE_DESCRIPTIONS: dict[str, str] = {
    "procesos": "Lectura de dashboards e indicadores",
    "calidad": "Administración y gestión OM",
    "desempeno": "Administración y gestión OM",
    "administrador": "Acceso total: todas las pantallas y edicion de OM",
    "auditor_ia": "Auditoria y publicacion de narrativas IA",
}

# MSAL añade openid/profile por su cuenta y rechaza pasarlos (son scopes reservados).
SCOPES = ["User.Read"]


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

    def get_login_url(self) -> str:
        # state firmado y con vencimiento: el callback solo acepta flujos que iniciamos nosotros
        state = create_access_token(
            secrets.token_urlsafe(16),
            settings=self.settings,
            extra={"typ": "oauth_state"},
        )
        return self._get_msal_app().get_authorization_request_url(
            scopes=SCOPES,
            redirect_uri=self.settings.azure_redirect_uri,
            state=state,
        )

    def verify_state(self, state: str | None) -> None:
        payload = decode_token(state or "", self.settings)
        if payload.get("typ") != "oauth_state":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="State inválido")

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

        # Con AZURE_TENANT_ID=organizations entra cualquier organización: el dominio
        # institucional ya no lo garantiza el tenant, hay que exigirlo aquí.
        self._check_domain(email)
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
        es_admin = email.lower() in self.settings.admin_emails_set
        if user:
            if name and user.name != name:
                user.name = name
            if azure_oid and user.azure_oid != azure_oid:
                user.azure_oid = azure_oid
            # "administrador" lo gobierna solo ADMIN_EMAILS: se asigna al entrar
            # en la lista y se revierte a "procesos" al salir. Otros roles
            # (calidad, desempeno, procesos) no se tocan.
            current = user.role.name if user.role else None
            target = (
                "administrador"
                if es_admin
                else ("procesos" if current == "administrador" else None)
            )
            if target and target != current:
                role = await self._get_role(db, target)
                user.role_id = role.id
                await db.flush()
                await db.refresh(user, attribute_names=["role"])
            return user

        role = await self._get_role(db, "administrador" if es_admin else default_role)
        user = User(email=email, name=name, role_id=role.id, azure_oid=azure_oid)
        db.add(user)
        await db.flush()
        await db.refresh(user, attribute_names=["role"])
        return user

    async def _get_role(self, db: AsyncSession, role_name: RoleName) -> Role:
        role_result = await db.execute(select(Role).where(Role.name == role_name))
        role = role_result.scalar_one_or_none()
        if role is None:
            # Bases nuevas o sin las migraciones 004+ (p. ej. un Postgres recién creado en
            # Render): los roles del sistema se crean al primer uso en vez de fallar.
            role = Role(name=role_name, description=_ROLE_DESCRIPTIONS[role_name])
            db.add(role)
            await db.flush()
        return role

    def _otp_hash(self, email: str, code: str) -> str:
        return hmac.new(
            self.settings.secret_key.encode(), f"{email}:{code}".encode(), hashlib.sha256
        ).hexdigest()

    def _check_domain(self, email: str) -> None:
        if not email.endswith(f"@{self.settings.email_login_domain}"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Solo se permiten correos @{self.settings.email_login_domain}",
            )

    async def request_otp(self, db: AsyncSession, *, email: str) -> None:
        """Genera y envía un OTP. Responde igual para correos no autorizados (sin enumeración)."""
        email = email.lower().strip()
        self._check_domain(email)
        allowed = self.settings.allowed_emails_set
        if allowed and email not in allowed and email not in self.settings.admin_emails_set:
            return

        now = datetime.now(UTC)
        current = await db.get(LoginOtp, email)
        if current is not None:
            elapsed = (now - current.created_at).total_seconds()
            if elapsed < self.settings.otp_resend_seconds:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Espera un momento antes de solicitar otro código.",
                )

        code = f"{secrets.randbelow(1_000_000):06d}"
        expires = now + timedelta(minutes=self.settings.otp_ttl_minutes)
        if current is None:
            db.add(
                LoginOtp(
                    email=email,
                    code_hash=self._otp_hash(email, code),
                    expires_at=expires,
                    attempts=0,
                    created_at=now,
                )
            )
        else:
            current.code_hash = self._otp_hash(email, code)
            current.expires_at = expires
            current.attempts = 0
            current.created_at = now
        await db.flush()
        await send_otp(self.settings, email, code)

    async def verify_otp(self, db: AsyncSession, *, email: str, code: str) -> tuple[str, User]:
        email = email.lower().strip()
        self._check_domain(email)
        invalid = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Código inválido o vencido"
        )
        otp = await db.get(LoginOtp, email)
        if otp is None or otp.expires_at < datetime.now(UTC):
            raise invalid
        if otp.attempts >= self.settings.otp_max_attempts:
            raise invalid
        if not hmac.compare_digest(otp.code_hash, self._otp_hash(email, code)):
            otp.attempts += 1
            await db.commit()  # persistir el intento fallido pese al HTTPException
            raise invalid

        await db.delete(otp)  # un solo uso
        user = await self._get_or_create_user(db, email=email, name=None, azure_oid=None)
        token = create_access_token(
            email,
            settings=self.settings,
            extra={"role": user.role.name, "name": user.name},
        )
        return token, user

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
