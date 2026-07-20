"""Cargadores para CMI por Procesos — mapa maestro y catálogo CMI."""

from __future__ import annotations

import pandas as pd

from app.core.ttl_cache import cache_get
from app.services.excel_reader import ExcelReaderService

_PROCESS_MAP_PATHS = [
    "raw/Subproceso-Proceso-Area.xlsx",
    "raw/Excel_Entrada/Subproceso-Proceso-Area.xlsx",
]

_PROCESS_MAP_CACHE: dict[str, tuple[float, pd.DataFrame]] = {}


def load_process_map(excel: ExcelReaderService) -> pd.DataFrame:
    """Carga hoja Proceso del mapa Subproceso-Proceso-Area.xlsx."""
    root = str(excel.data_root.resolve())

    def _load() -> pd.DataFrame:
        for rel in _PROCESS_MAP_PATHS:
            path = excel.data_root / rel
            if not path.exists():
                continue
            try:
                xl = pd.ExcelFile(path, engine="openpyxl")
                if "Proceso" not in xl.sheet_names:
                    continue
                df = xl.parse("Proceso")
                df.columns = [str(c).strip() for c in df.columns]
                cols = [c for c in ["Unidad", "Proceso", "Subproceso", "Tipo de proceso"] if c in df.columns]
                if not cols:
                    continue
                return df[cols].dropna(how="all")
            except Exception:
                continue
        return pd.DataFrame()

    return cache_get(_PROCESS_MAP_CACHE, root, _load)
