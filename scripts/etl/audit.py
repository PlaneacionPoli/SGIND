"""
scripts/etl/audit.py
Auditoría centralizada de ejecuciones del ETL.

RESPONSABILIDAD: Registrar quién, cuándo, qué cambió durante consolidación.
PRINCIPIO: Trazabilidad completa para auditar y reproducir cambios.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AuditTrail:
    """Gestor centralizado de audit trail de consolidaciones."""

    def __init__(self, audit_file: Optional[Path] = None):
        """
        Inicializa audit trail.

        Args:
            audit_file: Ruta a archivo JSON de auditoría.
                       Default: data/audit/consolidaciones.json
        """
        if audit_file is None:
            audit_file = (
                Path(__file__).parent.parent.parent
                / "data"
                / "audit"
                / "consolidaciones.json"
            )

        self.audit_file = Path(audit_file)
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)

        # Cargar histórico si existe
        if self.audit_file.exists():
            with open(self.audit_file) as f:
                self.entries = json.load(f)
        else:
            self.entries = []

    def registrar_ejecucion(
        self,
        evento: str,
        detalles: dict[str, Any],
        usuario: Optional[str] = None,
        exitoso: bool = True,
    ) -> None:
        """
        Registra evento de consolidación.

        Args:
            evento: Tipo de evento ("inicio_consolidación", "gate_validación",
                    "escritura_consolidado", etc.)
            detalles: Dict con detalles del evento
            usuario: Usuario que ejecutó (default: "sistema")
            exitoso: Si fue exitoso

        Example:
            trail.registrar_ejecucion(
                evento="gate_validacion",
                detalles={
                    "registros_entrada": 1500,
                    "validaciones_pasadas": True,
                    "warnings": ["2 duplicados", "1 fecha futura"]
                },
                usuario="etl_job",
                exitoso=True
            )
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "evento": evento,
            "usuario": usuario or "sistema",
            "exitoso": exitoso,
            "detalles": detalles,
        }

        self.entries.append(entry)
        self._guardar()

        nivel = logging.INFO if exitoso else logging.WARNING
        logger.log(
            nivel, f"[AUDIT] {evento} | usuario={usuario or 'sistema'} | ok={exitoso}"
        )

    def registrar_cambio_datos(
        self,
        tipo_cambio: str,
        tabla: str,
        registros_afectados: int,
        descripcion: str,
        usuario: Optional[str] = None,
    ) -> None:
        """
        Registra cambio en datos.

        Args:
            tipo_cambio: "insert" | "update" | "delete"
            tabla: Nombre de tabla/hoja (ej "Consolidado Historico")
            registros_afectados: Cantidad de registros modificados
            descripcion: Descripción del cambio
            usuario: Usuario que ejecutó cambio

        Example:
            trail.registrar_cambio_datos(
                tipo_cambio="insert",
                tabla="Consolidado Historico",
                registros_afectados=47,
                descripcion="Nuevos indicadores Kawak mayo 2026",
                usuario="etl_job"
            )
        """
        self.registrar_ejecucion(
            evento=f"cambio_datos_{tipo_cambio}",
            detalles={
                "tabla": tabla,
                "registros_afectados": registros_afectados,
                "descripcion": descripcion,
            },
            usuario=usuario,
            exitoso=True,
        )

    def registrar_error(
        self, evento: str, error: str, usuario: Optional[str] = None
    ) -> None:
        """
        Registra error durante consolidación.

        Args:
            evento: Tipo de evento donde ocurrió error
            error: Descripción del error
            usuario: Usuario que ejecutó
        """
        self.registrar_ejecucion(
            evento=f"{evento}_error",
            detalles={"error": error},
            usuario=usuario,
            exitoso=False,
        )

    def obtener_ultimo_consolidado_exitoso(self) -> Optional[dict]:
        """Retorna entrada de última consolidación exitosa."""
        for entry in reversed(self.entries):
            if (
                entry["evento"] == "consolidacion_completada"
                and entry["exitoso"]
            ):
                return entry
        return None

    def obtener_historial_cambios(self, tabla: str, ultimos_n: int = 10) -> list[dict]:
        """
        Retorna últimos N cambios de una tabla.

        Args:
            tabla: Nombre de tabla
            ultimos_n: Cantidad de cambios a retornar

        Returns:
            Lista de cambios ordenada por timestamp descendente
        """
        cambios = [
            e
            for e in self.entries
            if "tabla" in e.get("detalles", {})
            and e["detalles"]["tabla"] == tabla
        ]
        return cambios[-ultimos_n:]

    def _guardar(self) -> None:
        """Guarda entries a JSON."""
        with open(self.audit_file, "w") as f:
            json.dump(self.entries, f, indent=2, default=str)

    def resumen(self) -> dict[str, Any]:
        """Retorna resumen de auditoría."""
        exitosos = sum(1 for e in self.entries if e["exitoso"])
        errores = sum(1 for e in self.entries if not e["exitoso"])

        eventos = {}
        for entry in self.entries:
            evento = entry["evento"]
            eventos[evento] = eventos.get(evento, 0) + 1

        return {
            "total_eventos": len(self.entries),
            "eventos_exitosos": exitosos,
            "eventos_error": errores,
            "por_tipo": eventos,
            "ultimo_evento": self.entries[-1]["timestamp"] if self.entries else None,
        }
