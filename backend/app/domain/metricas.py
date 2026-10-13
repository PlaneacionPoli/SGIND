"""Marca como métrica los indicadores listados en app/data/metricas.toml."""

from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path

import pandas as pd

METRICAS_TOML_PATH = Path(__file__).resolve().parent.parent / "data" / "metricas.toml"


@lru_cache(maxsize=1)
def _ids_metrica() -> frozenset[str]:
    with METRICAS_TOML_PATH.open("rb") as f:
        return frozenset(str(i).strip() for i in tomllib.load(f).get("ids", []))


def marcar_metricas(df: pd.DataFrame) -> pd.DataFrame:
    """Pone Tipo_Registro = "Metrica" a los Id configurados (ensure_nivel_cumplimiento los
    rotula "Métrica" en vez de "Pendiente de reporte")."""
    if df.empty or "Id" not in df.columns:
        return df
    es_metrica = df["Id"].astype(str).str.strip().isin(_ids_metrica())
    if not es_metrica.any():
        return df
    out = df.copy()
    if "Tipo_Registro" not in out.columns:
        out["Tipo_Registro"] = pd.NA
    out["Tipo_Registro"] = out["Tipo_Registro"].astype("object")
    out.loc[es_metrica, "Tipo_Registro"] = "Metrica"
    return out
