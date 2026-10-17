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
_JERARQUIA_CACHE: dict[str, tuple[float, pd.DataFrame]] = {}

_CATALOGO_PATH = "raw/Catalogo de Indicadores.xlsx"
_CATALOGO_SHEET = "Catalogo Indicadores"
JERARQUIA_COLS = ["Id", "Proceso_cat", "Subproceso_cat", "TipoCalculo", "Estado_cat"]


def _limpia(valor: object) -> str:
    """Quita espacios finales/dobles y no separables (p. ej. 'BIENESTAR INSTITUCIONAL ')."""
    if valor is None or pd.isna(valor):
        return ""
    return " ".join(str(valor).replace("\xa0", " ").split())


def load_jerarquia_catalogo(excel: ExcelReaderService) -> pd.DataFrame:
    """Id → Proceso, Subproceso, TipoCalculo y Estado según el catálogo maestro.

    Es el vínculo indicador→proceso/subproceso: se une por Id, nunca por nombre.
    """
    root = str(excel.data_root.resolve())

    def _load() -> pd.DataFrame:
        path = excel.data_root / _CATALOGO_PATH
        if not path.exists():
            return pd.DataFrame(columns=JERARQUIA_COLS)
        try:
            df = pd.read_excel(path, sheet_name=_CATALOGO_SHEET, dtype=str, engine="openpyxl")
        except Exception:
            return pd.DataFrame(columns=JERARQUIA_COLS)
        df.columns = [str(c).strip() for c in df.columns]
        if "Id" not in df.columns:
            return pd.DataFrame(columns=JERARQUIA_COLS)
        out = pd.DataFrame(
            {
                "Id": df["Id"].map(_limpia),
                "Proceso_cat": df.get("Proceso", pd.Series("", index=df.index)).map(_limpia),
                "Subproceso_cat": df.get("Subproceso", pd.Series("", index=df.index)).map(_limpia),
                "TipoCalculo": df.get("TipoCalculo", pd.Series("", index=df.index)).map(_limpia),
                "Estado_cat": df.get("Estado", pd.Series("", index=df.index)).map(_limpia),
            }
        )
        return out[out["Id"] != ""].drop_duplicates(subset=["Id"], keep="last")

    return cache_get(_JERARQUIA_CACHE, root, _load)


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
                cols = [
                    c
                    for c in ["Unidad", "Proceso", "Subproceso", "Tipo de proceso"]
                    if c in df.columns
                ]
                if not cols:
                    continue
                return df[cols].dropna(how="all")
            except Exception:
                continue
        return pd.DataFrame()

    return cache_get(_PROCESS_MAP_CACHE, root, _load)
