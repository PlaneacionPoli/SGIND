"""
scripts/etl/versioning.py
Versionado de artefactos intermedios del ETL.

RESPONSABILIDAD: Crear backups versionados, permitir rollback.
PRINCIPIO: "No perder datos" — siempre tener versión anterior.
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class VersionManager:
    """Gestor de versiones para artefactos intermedios."""

    def __init__(self, base_file: Path, versions_dir: Optional[Path] = None, max_versions: int = 5):
        """
        Inicializa gestor de versiones.

        Args:
            base_file: Archivo principal a versionar (ej: Resultados_Consolidados.xlsx)
            versions_dir: Directorio para guardar versiones
                         Default: base_file.parent / ".versiones"
            max_versions: Máximo de versiones a retener (default 5)
        """
        self.base_file = Path(base_file)
        self.versions_dir = Path(versions_dir or self.base_file.parent / ".versiones")
        self.max_versions = max_versions

        self.versions_dir.mkdir(parents=True, exist_ok=True)

    def crear_version(self, tag: Optional[str] = None) -> Path:
        """
        Crea versión (backup) del archivo base.

        Args:
            tag: Etiqueta descriptiva (opcional)
                 Si no se proporciona, usa timestamp

        Returns:
            Path al archivo de versión creado

        Raises:
            FileNotFoundError: Si base_file no existe
        """
        if not self.base_file.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {self.base_file}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if tag:
            nombre_version = f"{self.base_file.stem}_v{timestamp}_{tag}{self.base_file.suffix}"
        else:
            nombre_version = f"{self.base_file.stem}_v{timestamp}{self.base_file.suffix}"

        version_path = self.versions_dir / nombre_version

        try:
            shutil.copy2(self.base_file, version_path)
            logger.info(f"  ✅ Versión guardada: {version_path.name}")
        except Exception as e:
            logger.error(f"  ❌ Error creando versión: {e}")
            raise

        # Limpiar versiones antiguas
        self._limpiar_antiguas()

        return version_path

    def restaurar_ultima_version(self) -> bool:
        """
        Restaura última versión al archivo base.

        Returns:
            True si exitoso, False si no hay versiones o error
        """
        versiones = sorted(self.versions_dir.glob(f"{self.base_file.stem}_v*{self.base_file.suffix}"))

        if not versiones:
            logger.error("  No hay versiones guardadas para restaurar")
            return False

        ultima = versiones[-1]

        try:
            shutil.copy2(ultima, self.base_file)
            logger.info(f"  ✅ Restaurado desde: {ultima.name}")
            return True
        except Exception as e:
            logger.error(f"  ❌ Error restaurando: {e}")
            return False

    def restaurar_version_especifica(self, version_timestamp: str) -> bool:
        """
        Restaura versión específica.

        Args:
            version_timestamp: Timestamp de versión (ej "20260509_143015")

        Returns:
            True si exitoso
        """
        version_path = self.versions_dir / f"{self.base_file.stem}_v{version_timestamp}{self.base_file.suffix}"

        if not version_path.exists():
            logger.error(f"  Versión no encontrada: {version_timestamp}")
            return False

        try:
            shutil.copy2(version_path, self.base_file)
            logger.info(f"  ✅ Restaurado desde: {version_path.name}")
            return True
        except Exception as e:
            logger.error(f"  ❌ Error restaurando: {e}")
            return False

    def listar_versiones(self) -> list[dict]:
        """
        Retorna lista de versiones disponibles.

        Returns:
            Lista ordenada de dicts con {nombre, timestamp, tamaño_kb}
        """
        versiones = sorted(self.versions_dir.glob(f"{self.base_file.stem}_v*{self.base_file.suffix}"))

        resultado = []
        for v in reversed(versiones):  # más recientes primero
            size_kb = v.stat().st_size / 1024
            # Extraer timestamp del nombre (formato: _v20260509_143015)
            nombre_partes = v.stem.split("_v")
            timestamp = nombre_partes[1] if len(nombre_partes) > 1 else "desconocido"

            resultado.append({
                "nombre": v.name,
                "timestamp": timestamp,
                "tamaño_kb": size_kb,
                "path": str(v),
            })

        return resultado

    def _limpiar_antiguas(self) -> None:
        """Elimina versiones más antiguas que max_versions."""
        versiones = sorted(self.versions_dir.glob(f"{self.base_file.stem}_v*{self.base_file.suffix}"))

        if len(versiones) > self.max_versions:
            para_eliminar = versiones[: len(versiones) - self.max_versions]
            for v in para_eliminar:
                try:
                    v.unlink()
                    logger.info(f"  Versión antigua eliminada: {v.name}")
                except Exception as e:
                    logger.warning(f"  Error eliminando versión antigua {v.name}: {e}")

    def limpiar_versiones_anteriores_a(self, dias: int = 14) -> int:
        """
        Elimina versiones anteriores a N días.

        Args:
            dias: Cantidad de días

        Returns:
            Cantidad de versiones eliminadas
        """
        cutoff = datetime.now() - timedelta(days=dias)
        versiones = list(self.versions_dir.glob(f"{self.base_file.stem}_v*{self.base_file.suffix}"))

        eliminadas = 0
        for v in versiones:
            mtime = datetime.fromtimestamp(v.stat().st_mtime)
            if mtime < cutoff:
                try:
                    v.unlink()
                    eliminadas += 1
                except Exception as e:
                    logger.warning(f"  Error eliminando {v.name}: {e}")

        if eliminadas > 0:
            logger.info(f"  Eliminadas {eliminadas} versiones anteriores a {dias} días")

        return eliminadas

    def tamano_total_versiones(self) -> float:
        """Retorna tamaño total de todas las versiones en MB."""
        total_bytes = sum(v.stat().st_size for v in self.versions_dir.glob(f"{self.base_file.stem}_v*{self.base_file.suffix}"))
        return total_bytes / (1024 * 1024)
