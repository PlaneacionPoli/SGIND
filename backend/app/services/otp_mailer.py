"""Envío del código OTP por SMTP (stdlib, sin dependencias nuevas)."""

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from fastapi import HTTPException, status

from app.core.config import Settings

logger = logging.getLogger(__name__)


def _send_sync(settings: Settings, to: str, code: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = "Tu código de acceso a SGIND"
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = to
    msg.set_content(
        f"Tu código de acceso a SGIND es: {code}\n\n"
        f"Vence en {settings.otp_ttl_minutes} minutos. "
        "Si no lo solicitaste, ignora este mensaje."
    )
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
        smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)


async def send_otp(settings: Settings, to: str, code: str) -> None:
    if not settings.smtp_host:
        if settings.environment == "development":
            logger.warning("SMTP no configurado (solo dev): código OTP de %s = %s", to, code)
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Envío de correo no configurado.",
        )
    try:
        await asyncio.to_thread(_send_sync, settings, to, code)
    except (smtplib.SMTPException, OSError) as exc:
        logger.exception("No se pudo enviar el OTP a %s", to)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo enviar el código. Inténtalo más tarde.",
        ) from exc
