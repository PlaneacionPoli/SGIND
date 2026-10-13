"""Normaliza a pesos los indicadores en "$" que la fuente trae en millones.

Parámetros en app/data/escala_moneda.toml (signos, umbral_pesos, factor).
"""

from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path

import pandas as pd

ESCALA_TOML_PATH = Path(__file__).resolve().parent.parent / "data" / "escala_moneda.toml"


@lru_cache(maxsize=1)
def _config() -> dict:
    with ESCALA_TOML_PATH.open("rb") as f:
        return tomllib.load(f)


def normalizar_pesos(df: pd.DataFrame) -> pd.DataFrame:
    """Multiplica por `factor` Meta/Ejecucion de las filas en "$" expresadas en millones."""
    if df.empty or not {"Meta", "Ejecucion", "Meta_Signo"}.issubset(df.columns):
        return df
    cfg = _config()
    es_pesos = df["Meta_Signo"].astype(str).str.strip().isin(cfg["signos"])
    meta = pd.to_numeric(df["Meta"], errors="coerce")
    ejec = pd.to_numeric(df["Ejecucion"], errors="coerce")
    magnitud = pd.concat([meta.abs(), ejec.abs()], axis=1).max(axis=1)
    en_millones = es_pesos & magnitud.notna() & (magnitud > 0) & (magnitud < cfg["umbral_pesos"])
    if not en_millones.any():
        return df
    out = df.copy()
    out.loc[en_millones, "Meta"] = meta[en_millones] * cfg["factor"]
    out.loc[en_millones, "Ejecucion"] = ejec[en_millones] * cfg["factor"]
    return out
