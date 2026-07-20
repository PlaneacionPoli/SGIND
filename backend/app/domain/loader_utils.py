"""Utilidades de carga Excel — portado desde services/loaders/utils.py."""

import unicodedata

import pandas as pd

_RENAME = {
    "Año": "Anio",
    "Ejecución": "Ejecucion",
    "Clasificación": "Clasificacion",
    "Ejecución s": "Ejecucion_s",
    "Meta s": "Meta_Signo",
}


def ascii_lower(s: str) -> str:
    return unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().lower()


def renombrar_columnas(df: pd.DataFrame, mapa: dict | None = None) -> pd.DataFrame:
    if mapa is None:
        mapa = _RENAME

    df.columns = [str(c).strip() for c in df.columns]
    mapping: dict[str, str] = {}
    for col in df.columns:
        for orig, dest in mapa.items():
            if ascii_lower(col) == ascii_lower(orig):
                mapping[col] = dest
                break
    return df.rename(columns=mapping)


def id_a_str(x) -> str:
    if pd.isna(x):
        return ""
    try:
        f = float(x)
        return str(int(f)) if f == int(f) else str(f)
    except (ValueError, TypeError):
        return str(x)


def obtener_rename_map() -> dict:
    return _RENAME.copy()


def find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols_norm = {ascii_lower(c): c for c in df.columns}
    for name in candidates:
        hit = cols_norm.get(ascii_lower(name))
        if hit:
            return hit
    return None


# El archivo fuente "Catalogo de Indicadores.xlsx" tiene celdas de "Linea" con
# el caracter de reemplazo Unicode (�) en lugar de tildes, producto de una
# corrupción de encoding ocurrida antes de que los datos entraran al repo (la
# tilde original ya no existe en el archivo). Sin este arreglo, "Expansión" y
# "Educación_para_toda_la_vida" no calzan contra las claves normalizadas
# usadas para agrupar/mostrar cumplimiento por línea estratégica.
_LINEA_REPAIR_MAP = {
    "Expansi�n": "Expansión",
    "Transformaci�n_Organizacional": "Transformación_Organizacional",
    "Educaci�n_para_toda_la_vida": "Educación_para_toda_la_vida",
}


def repair_linea_encoding(series: pd.Series) -> pd.Series:
    """Corrige valores de 'Linea' con el caracter de reemplazo Unicode conocido."""
    return series.replace(_LINEA_REPAIR_MAP)
