#!/usr/bin/env python3
"""
scripts/etl_utils.py
Utilidades para interactuar con auditoría y versionado del pipeline ETL.

USO:
    python scripts/etl_utils.py audit-trail      # mostrar historial de consolidaciones
    python scripts/etl_utils.py versions list     # listar versiones disponibles
    python scripts/etl_utils.py versions restore  # restaurar última versión
    python scripts/etl_utils.py versions restore <timestamp>  # restaurar versión específica
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from tabulate import tabulate

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.etl.config import OUTPUT_FILE
from scripts.etl.audit import AuditTrail
from scripts.etl.versioning import VersionManager

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


def cmd_audit_trail() -> None:
    """Mostrar historial de auditoría."""
    trail = AuditTrail()

    if not trail.entries:
        logger.info("No hay eventos registrados en auditoría.")
        return

    # Crear tabla
    rows = []
    for entry in trail.entries[-20:]:  # últimos 20
        rows.append([
            entry["timestamp"][-8:],  # HH:MM:SS
            entry["evento"],
            entry["usuario"],
            "✅" if entry["exitoso"] else "❌",
        ])

    logger.info("\n📋 HISTORIAL DE AUDITORÍA (últimos 20 eventos)\n")
    print(tabulate(rows, headers=["Hora", "Evento", "Usuario", "OK"], tablefmt="grid"))

    # Resumen
    summary = trail.resumen()
    logger.info(f"\n📊 RESUMEN: {summary['total_eventos']} eventos ({summary['eventos_exitosos']} OK, {summary['eventos_error']} ERROR)")


def cmd_audit_details() -> None:
    """Mostrar detalles de última consolidación."""
    trail = AuditTrail()

    ultimo = trail.obtener_ultimo_consolidado_exitoso()
    if not ultimo:
        logger.info("No hay consolidación exitosa registrada.")
        return

    logger.info("\n✅ ÚLTIMA CONSOLIDACIÓN EXITOSA\n")
    logger.info(f"Timestamp: {ultimo['timestamp']}")
    logger.info(f"Usuario: {ultimo['usuario']}")
    logger.info("\nDetalles:")
    for key, value in ultimo["detalles"].items():
        logger.info(f"  {key}: {value}")


def cmd_versions_list() -> None:
    """Listar versiones disponibles."""
    vm = VersionManager(OUTPUT_FILE)

    versiones = vm.listar_versiones()
    if not versiones:
        logger.info("No hay versiones guardadas.")
        return

    logger.info(f"\n📦 VERSIONES DISPONIBLES ({len(versiones)}/{vm.max_versions})\n")

    rows = []
    for v in versiones[:10]:  # mostrar máximo 10
        rows.append([
            v["nombre"],
            v["timestamp"],
            f"{v['tamaño_kb']:.1f} KB",
        ])

    print(tabulate(rows, headers=["Archivo", "Timestamp", "Tamaño"], tablefmt="grid"))

    total_size = vm.tamano_total_versiones()
    logger.info(f"\nTamaño total: {total_size:.2f} MB")


def cmd_versions_restore(timestamp: str = None) -> None:
    """Restaurar versión."""
    vm = VersionManager(OUTPUT_FILE)

    if timestamp:
        logger.info(f"Restaurando versión {timestamp}…")
        if vm.restaurar_version_especifica(timestamp):
            logger.info("✅ Versión restaurada exitosamente")
        else:
            logger.error("❌ Error restaurando versión")
            sys.exit(1)
    else:
        logger.info("Restaurando última versión…")
        if vm.restaurar_ultima_version():
            logger.info("✅ Última versión restaurada exitosamente")
        else:
            logger.error("❌ Error restaurando versión")
            sys.exit(1)


def cmd_versions_cleanup(days: int = 14) -> None:
    """Limpiar versiones antiguas."""
    vm = VersionManager(OUTPUT_FILE)

    logger.info(f"Eliminando versiones anteriores a {days} días…")
    eliminated = vm.limpiar_versiones_anteriores_a(dias=days)
    logger.info(f"✅ {eliminated} versiones eliminadas")


def cmd_stats() -> None:
    """Mostrar estadísticas de auditoría y versionado."""
    trail = AuditTrail()
    vm = VersionManager(OUTPUT_FILE)

    summary = trail.resumen()
    versiones = vm.listar_versiones()

    logger.info("\n📊 ESTADÍSTICAS DEL PIPELINE ETL\n")
    logger.info(f"Total eventos auditoría: {summary['total_eventos']}")
    logger.info(f"  - Exitosos: {summary['eventos_exitosos']}")
    logger.info(f"  - Errores: {summary['eventos_error']}")
    logger.info(f"\nTotal versiones: {len(versiones)}/{vm.max_versions}")
    logger.info(f"Espacio versiones: {vm.tamano_total_versiones():.2f} MB")

    # Top eventos
    if summary.get("por_tipo"):
        logger.info("\nEventos por tipo:")
        for evento, count in sorted(summary["por_tipo"].items(), key=lambda x: -x[1])[:5]:
            logger.info(f"  {evento}: {count}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Utilidades de auditoría y versionado para ETL SGIND"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # audit-trail
    subparsers.add_parser("audit-trail", help="Mostrar historial de auditoría")
    subparsers.add_parser("audit-details", help="Detalles de última consolidación")

    # versions
    versions_parser = subparsers.add_parser("versions", help="Gestionar versiones")
    versions_subparsers = versions_parser.add_subparsers(dest="subcommand")
    versions_subparsers.add_parser("list", help="Listar versiones")
    restore_parser = versions_subparsers.add_parser("restore", help="Restaurar versión")
    restore_parser.add_argument("timestamp", nargs="?", help="Timestamp específico (opcional)")
    cleanup_parser = versions_subparsers.add_parser("cleanup", help="Limpiar versiones antiguas")
    cleanup_parser.add_argument("--days", type=int, default=14, help="Días de retención (default 14)")

    # stats
    subparsers.add_parser("stats", help="Estadísticas generales")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "audit-trail":
        cmd_audit_trail()
    elif args.command == "audit-details":
        cmd_audit_details()
    elif args.command == "versions":
        if not args.subcommand:
            parser.parse_args(["versions", "--help"])
        elif args.subcommand == "list":
            cmd_versions_list()
        elif args.subcommand == "restore":
            cmd_versions_restore(args.timestamp if hasattr(args, "timestamp") else None)
        elif args.subcommand == "cleanup":
            cmd_versions_cleanup(args.days if hasattr(args, "days") else 14)
    elif args.command == "stats":
        cmd_stats()


if __name__ == "__main__":
    main()
