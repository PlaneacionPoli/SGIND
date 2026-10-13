"""Indicadores con medición cada N años (app/data/periodicidad_especial.toml)."""

from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path

import pandas as pd

PERIODICIDAD_TOML_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "periodicidad_especial.toml"
)


@lru_cache(maxsize=1)
def _reglas() -> dict[str, tuple[int, int]]:
    with PERIODICIDAD_TOML_PATH.open("rb") as f:
        filas = tomllib.load(f).get("indicador", [])
    return {str(r["id"]): (int(r["cada_anios"]), int(r["anio_base"])) for r in filas}


def aplica_en_anio(id_indicador: object, anio: int) -> bool:
    """False solo si el indicador es de medición cada N años y `anio` no es de medición."""
    regla = _reglas().get(str(id_indicador).strip())
    if regla is None:
        return True
    cada, base = regla
    return (int(anio) - base) % cada == 0


def filtrar_por_anio(df: pd.DataFrame, anio: int) -> pd.DataFrame:
    """Quita los indicadores que no se miden en `anio`."""
    if df.empty or "Id" not in df.columns or not _reglas():
        return df
    mantener = df["Id"].map(lambda i: aplica_en_anio(i, anio))
    return df[mantener].reset_index(drop=True)
