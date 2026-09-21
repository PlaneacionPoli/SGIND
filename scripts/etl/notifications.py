"""
scripts/etl/notifications.py
Notificaciones para fallos del pipeline ETL.

RESPONSABILIDAD: Enviar alertas por email/Slack cuando pipeline falla
PRINCIPIO: "Informar al equipo inmediatamente de problemas críticos"

Soporta:
- Email via SMTP (Gmail, Outlook, servidor corporativo)
- Slack webhooks (opcional)
- Métricas del error (qué falló, cuándo, impacto)
"""

from __future__ import annotations

import logging
import smtplib
import os
import traceback
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Servicio de notificaciones por email."""

    def __init__(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        sender_email: Optional[str] = None,
        sender_password: Optional[str] = None,
        recipient_emails: Optional[list[str]] = None,
    ):
        """
        Inicializa notificador de email.

        Parámetros pueden venir de:
        1. Argumentos de función
        2. Variables de entorno (SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAILS)
        3. Valores por defecto

        Args:
            smtp_server: Servidor SMTP (ej: smtp.gmail.com)
            smtp_port: Puerto SMTP (ej: 587)
            sender_email: Email remitente
            sender_password: Contraseña/token del remitente
            recipient_emails: Lista de emails destinatarios
        """
        self.smtp_server = smtp_server or os.getenv("SMTP_SERVER", "")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = sender_email or os.getenv("SENDER_EMAIL", "")
        self.sender_password = sender_password or os.getenv("SENDER_PASSWORD", "")

        recipient_str = os.getenv("RECIPIENT_EMAILS", "")
        self.recipient_emails = (
            recipient_emails or (recipient_str.split(",") if recipient_str else [])
        )

        self.enabled = bool(
            self.smtp_server and self.sender_email and self.recipient_emails
        )

        if not self.enabled:
            logger.warning(
                "⚠️  Email notifications deshabilitado: falta configuración SMTP. "
                "Configure SMTP_SERVER, SENDER_EMAIL, RECIPIENT_EMAILS y SENDER_PASSWORD."
            )

    def send_pipeline_failure_alert(
        self,
        error: Exception,
        operation: str = "Consolidación ETL",
        audit_summary: Optional[dict] = None,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Envía alerta de fallo en pipeline.

        Args:
            error: Excepción que ocurrió
            operation: Nombre de operación que falló (default: "Consolidación ETL")
            audit_summary: Resumen de auditoría (opcional)
            timestamp: Timestamp del error (default: ahora)

        Returns:
            True si se envió exitosamente, False si no
        """
        if not self.enabled:
            logger.debug(
                "Email notifications deshabilitado, omitiendo alerta de fallo"
            )
            return False

        timestamp = timestamp or datetime.now()
        subject = f"❌ [{timestamp.strftime('%H:%M:%S')}] Fallo en {operation}"

        # Construir cuerpo del email
        body = self._build_failure_body(
            error=error,
            operation=operation,
            audit_summary=audit_summary,
            timestamp=timestamp,
        )

        return self._send_email(subject=subject, body=body, is_html=True)

    def send_recovery_success_alert(
        self,
        operation: str = "Consolidación ETL",
        recovery_method: str = "Rollback automático",
        audit_summary: Optional[dict] = None,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Envía alerta de recuperación exitosa.

        Args:
            operation: Nombre de operación recuperada
            recovery_method: Cómo se recuperó (ej: "Rollback automático")
            audit_summary: Resumen de auditoría
            timestamp: Timestamp de recuperación

        Returns:
            True si se envió exitosamente
        """
        if not self.enabled:
            return False

        timestamp = timestamp or datetime.now()
        subject = f"✅ [{timestamp.strftime('%H:%M:%S')}] {operation} — Recuperado"

        body = self._build_recovery_body(
            operation=operation,
            recovery_method=recovery_method,
            audit_summary=audit_summary,
            timestamp=timestamp,
        )

        return self._send_email(subject=subject, body=body, is_html=True)

    def _build_failure_body(
        self,
        error: Exception,
        operation: str,
        audit_summary: Optional[dict],
        timestamp: datetime,
    ) -> str:
        """Construye cuerpo HTML del email de fallo."""
        error_type = type(error).__name__
        error_msg = str(error)
        traceback_str = traceback.format_exc()

        html = f"""
        <html>
        <head><style>
            body {{ font-family: Arial, sans-serif; }}
            .header {{ background: #d32f2f; color: white; padding: 15px; }}
            .section {{ margin: 15px 0; padding: 10px; background: #f5f5f5; }}
            .code {{ background: #fff; padding: 10px; border-left: 3px solid #d32f2f; font-family: monospace; white-space: pre-wrap; overflow-x: auto; }}
            .audit {{ color: #666; font-size: 12px; }}
        </style></head>
        <body>
            <div class="header">
                <h2>🚨 ALERTA: Fallo en Pipeline ETL</h2>
            </div>
            
            <div class="section">
                <strong>Operación:</strong> {operation}<br>
                <strong>Timestamp:</strong> {timestamp.isoformat()}<br>
                <strong>Error:</strong> {error_type}
            </div>
            
            <div class="section">
                <strong>Mensaje:</strong><br>
                <div class="code">{error_msg}</div>
            </div>
            
            <div class="section">
                <strong>Stack Trace:</strong><br>
                <div class="code">{traceback_str}</div>
            </div>
        """

        if audit_summary:
            html += f"""
            <div class="section audit">
                <strong>Resumen de Auditoría:</strong><br>
                Total eventos: {audit_summary.get('total_eventos', '?')}<br>
                Exitosos: {audit_summary.get('eventos_exitosos', '?')}<br>
                Errores: {audit_summary.get('eventos_error', '?')}
            </div>
            """

        html += """
        </body>
        </html>
        """
        return html

    def _build_recovery_body(
        self,
        operation: str,
        recovery_method: str,
        audit_summary: Optional[dict],
        timestamp: datetime,
    ) -> str:
        """Construye cuerpo HTML del email de recuperación."""
        html = f"""
        <html>
        <head><style>
            body {{ font-family: Arial, sans-serif; }}
            .header {{ background: #4caf50; color: white; padding: 15px; }}
            .section {{ margin: 15px 0; padding: 10px; background: #f5f5f5; }}
            .audit {{ color: #666; font-size: 12px; }}
        </style></head>
        <body>
            <div class="header">
                <h2>✅ RECUPERACIÓN EXITOSA: {operation}</h2>
            </div>
            
            <div class="section">
                <strong>Método de recuperación:</strong> {recovery_method}<br>
                <strong>Timestamp:</strong> {timestamp.isoformat()}<br>
            </div>
        """

        if audit_summary:
            html += f"""
            <div class="section audit">
                <strong>Estado Final:</strong><br>
                Total eventos: {audit_summary.get('total_eventos', '?')}<br>
                Exitosos: {audit_summary.get('eventos_exitosos', '?')}<br>
                Errores: {audit_summary.get('eventos_error', '?')}
            </div>
            """

        html += """
        </body>
        </html>
        """
        return html

    def _send_email(self, subject: str, body: str, is_html: bool = False) -> bool:
        """
        Envía email via SMTP.

        Args:
            subject: Asunto del email
            body: Cuerpo del mensaje
            is_html: Si el cuerpo es HTML

        Returns:
            True si se envió exitosamente
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = ", ".join(self.recipient_emails)

            if is_html:
                part = MIMEText(body, "html")
            else:
                part = MIMEText(body, "plain")

            msg.attach(part)

            logger.debug(
                f"Enviando email a {self.recipient_emails} vía {self.smtp_server}:{self.smtp_port}"
            )

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            logger.info(f"✅ Email enviado: {subject}")
            return True

        except smtplib.SMTPException as e:
            logger.error(f"❌ Error SMTP enviando email: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado enviando email: {e}")
            return False


class SlackNotifier:
    """Servicio de notificaciones por Slack (mínimal)."""

    def __init__(self, webhook_url: Optional[str] = None):
        """
        Inicializa notificador Slack.

        Args:
            webhook_url: URL del webhook de Slack (o variable de entorno SLACK_WEBHOOK_URL)
        """
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL", "")
        self.enabled = bool(self.webhook_url)

        if not self.enabled:
            logger.debug("Slack notifications deshabilitado")

    def send_pipeline_failure_alert(
        self,
        error: Exception,
        operation: str = "Consolidación ETL",
        audit_summary: Optional[dict] = None,
    ) -> bool:
        """Envía alerta de fallo a Slack."""
        if not self.enabled:
            return False

        try:
            import requests

            timestamp = datetime.now().isoformat()
            message = {
                "text": f":x: Fallo en {operation}",
                "attachments": [
                    {
                        "color": "danger",
                        "fields": [
                            {
                                "title": "Error",
                                "value": f"{type(error).__name__}: {str(error)[:100]}",
                                "short": False,
                            },
                            {
                                "title": "Timestamp",
                                "value": timestamp,
                                "short": True,
                            },
                        ],
                    }
                ],
            }

            response = requests.post(self.webhook_url, json=message, timeout=10)
            if response.status_code == 200:
                logger.info("✅ Alerta Slack enviada")
                return True
            else:
                logger.warning(
                    f"⚠️ Error Slack: {response.status_code} {response.text}"
                )
                return False

        except Exception as e:
            logger.warning(f"⚠️ Error enviando a Slack: {e}")
            return False


def get_notifier(
    provider: str = "email",
) -> EmailNotifier | SlackNotifier | None:
    """
    Factory para obtener notificador según provider.

    Args:
        provider: "email" o "slack"

    Returns:
        Instancia de notificador o None si no configurado
    """
    if provider == "email":
        return EmailNotifier()
    elif provider == "slack":
        return SlackNotifier()
    else:
        logger.warning(f"Unknown notifier provider: {provider}")
        return None
