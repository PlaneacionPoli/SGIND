import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.config import Settings
from app.schemas.common import ExcelFileInfo

# Archivos Excel principales del sistema legacy
PRIMARY_EXCEL_FILES = [
    "output/Resultados Consolidados.xlsx",
    "output/Consolidado_API_Kawak.xlsx",
    "raw/Excel_Entrada/CMI.xlsx",
]


class ExcelReaderService:
    """Lee archivos Excel del sistema Streamlit (solo lectura)."""

    def __init__(self, settings: Settings) -> None:
        self._root = Path(settings.sgind_data_path).resolve()
        self._ttl = settings.excel_cache_ttl_seconds
        self._cache: dict[str, tuple[float, Any]] = {}

    @property
    def data_root(self) -> Path:
        return self._root

    def _resolve(self, relative_path: str) -> Path:
        path = (self._root / relative_path).resolve()
        if not str(path).startswith(str(self._root)):
            raise ValueError("Ruta fuera del directorio de datos permitido")
        return path

    def list_available_files(self) -> list[ExcelFileInfo]:
        files: list[ExcelFileInfo] = []
        if not self._root.exists():
            return files
        for pattern in ("**/*.xlsx", "**/*.xls"):
            for path in self._root.glob(pattern):
                stat = path.stat()
                files.append(
                    ExcelFileInfo(
                        name=path.name,
                        path=str(path.relative_to(self._root)),
                        size_bytes=stat.st_size,
                        modified_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                    )
                )
        return sorted(files, key=lambda f: f.path)

    def read_excel(
        self,
        relative_path: str,
        *,
        sheet_name: str | int | None = 0,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        cache_key = f"{relative_path}:{sheet_name}"
        if use_cache and cache_key in self._cache:
            cached_at, df = self._cache[cache_key]
            if time.time() - cached_at < self._ttl:
                return df.copy()

        path = self._resolve(relative_path)
        if not path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {relative_path}")

        df = pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")
        self._cache[cache_key] = (time.time(), df)
        return df.copy()

    def read_consolidado(self) -> pd.DataFrame:
        for candidate in PRIMARY_EXCEL_FILES:
            path = self._root / candidate
            if path.exists():
                try:
                    return self.read_excel(candidate, sheet_name="Consolidado Semestral")
                except (ValueError, KeyError):
                    return self.read_excel(candidate)
        raise FileNotFoundError(
            "No se encontró archivo consolidado. Verifique SGIND_DATA_PATH."
        )

    def get_dashboard_kpis(self, anio: int | None = None, periodo: str | None = None) -> list[dict]:
        """Deprecated: usar DashboardService.get_kpis()."""
        from app.services.dashboard_service import DashboardService

        return DashboardService(self).get_kpis(anio=anio, periodo=periodo)
