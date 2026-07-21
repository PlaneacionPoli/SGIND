#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_notifications_config.py
=============================
Script para validar la configuración de notificaciones en producción.

Uso:
    python test_notifications_config.py  [--smtp] [--slack] [--both]

Ejemplos:
    python test_notifications_config.py --smtp
    python test_notifications_config.py --slack
    python test_notifications_config.py --both  (ejecuta ambos)
    python test_notifications_config.py          (ejecuta ambos por defecto)
"""

import os
import sys
import argparse
from pathlib import Path

# Agregar raíz del proyecto al path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _check_smtp_config() -> bool:
    """Validar que la configuración SMTP es correcta y que se puede enviar un email de prueba."""
    logger.info("=" * 60)
    logger.info("🔌 PRUEBA SMTP")
    logger.info("=" * 60)

    try:
        from scripts.etl.notifications import EmailNotifier

        # Intentar instanciar EmailNotifier
        notifier = EmailNotifier()

        if not notifier.enabled:
            logger.warning("⚠️  EmailNotifier DESHABILITADO: falta configuración .env")
            logger.info("   Variables requeridas: SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAILS")
            return False

        logger.info("✅ EmailNotifier habilitado")
        logger.info(f"   Servidor: {notifier.smtp_server}:{notifier.smtp_port}")
        logger.info(f"   De: {notifier.sender_email}")
        logger.info(f"   Para: {', '.join(notifier.recipient_emails)}")

        # Enviar email de prueba
        logger.info("\n📧 Enviando email de prueba...")
        try:
            notifier.send_pipeline_failure_alert(
                error=Exception("TEST: Email de prueba SGIND"),
                operation="test_notifications_config.py",
                audit_summary={"eventos_total": 1, "eventos_error": 0},
                timestamp="2026-05-09 12:00:00",
            )
            logger.info("✅ Email de prueba ENVIADO")
            logger.info("   Verifica tu bandeja de entrada/spam")
            return True

        except Exception as e:
            logger.error(f"❌ Error al enviar email: {e}")
            return False

    except Exception as e:
        logger.error(f"❌ Error en configuración SMTP: {e}")
        return False


def _check_slack_config() -> bool:
    """Validar que la configuración Slack es correcta y que se puede enviar un mensaje de prueba."""
    logger.info("\n" + "=" * 60)
    logger.info("🔔 PRUEBA SLACK")
    logger.info("=" * 60)

    try:
        from scripts.etl.notifications import SlackNotifier

        # Intentar instanciar SlackNotifier
        notifier = SlackNotifier()

        if not notifier.enabled:
            logger.warning("⚠️  SlackNotifier DESHABILITADO: falta SLACK_WEBHOOK_URL en .env")
            logger.info("   Variable requerida: SLACK_WEBHOOK_URL")
            return False

        logger.info("✅ SlackNotifier habilitado")
        logger.info(f"   Webhook: {notifier.webhook_url[:50]}...")

        # Enviar mensaje de prueba
        logger.info("\n💬 Enviando mensaje de prueba a Slack...")
        try:
            notifier.send_pipeline_failure_alert(
                error=Exception("TEST: Mensaje de prueba SGIND"),
                operation="test_notifications_config.py",
                audit_summary={"eventos_total": 1},
                timestamp="2026-05-09 12:00:00",
            )
            logger.info("✅ Mensaje de prueba ENVIADO")
            logger.info("   Verifica el canal de Slack #sgind-alerts")
            return True

        except Exception as e:
            logger.error(f"❌ Error al enviar mensaje Slack: {e}")
            return False

    except Exception as e:
        logger.error(f"❌ Error en configuración Slack: {e}")
        return False


def test_smtp_config():
    """Prueba pytest: no debe retornar valores."""
    _check_smtp_config()


def test_slack_config():
    """Prueba pytest: no debe retornar valores."""
    _check_slack_config()


def main():
    """Ejecutar pruebas según argumentos."""
    parser = argparse.ArgumentParser(
        description="Validar configuración de notificaciones (SMTP/Slack)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
    python test_notifications_config.py --smtp
    python test_notifications_config.py --slack
    python test_notifications_config.py --both
    python test_notifications_config.py  (ejecuta ambos por defecto)
        """,
    )

    parser.add_argument(
        "--smtp",
        action="store_true",
        help="Probar solo SMTP",
    )
    parser.add_argument(
        "--slack",
        action="store_true",
        help="Probar solo Slack",
    )
    parser.add_argument(
        "--both",
        action="store_true",
        help="Probar ambos (default si no se especifica)",
    )

    args = parser.parse_args()

    # Si no se especifica nada, probar ambos
    test_both = (
        not args.smtp
        and not args.slack
        or args.both
    )
    test_smtp_only = args.smtp and not test_both
    test_slack_only = args.slack and not test_both

    results = {}

    if test_smtp_only or test_both:
        results["SMTP"] = _check_smtp_config()

    if test_slack_only or test_both:
        results["Slack"] = _check_slack_config()

    # Resumen
    logger.info("\n" + "=" * 60)
    logger.info("📊 RESUMEN")
    logger.info("=" * 60)
    for service, passed in results.items():
        status = "✅ PASÓ" if passed else "❌ FALLÓ"
        logger.info(f"{service:10} {status}")

    # Exit code
    all_passed = all(results.values())
    exit_code = 0 if all_passed else 1

    logger.info("=" * 60)
    if all_passed:
        logger.info("✅ TODAS LAS PRUEBAS PASARON")
    else:
        logger.info("❌ ALGUNAS PRUEBAS FALLARON — Revisar configuración .env")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
