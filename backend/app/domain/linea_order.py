"""Orden canónico institucional de las líneas estratégicas."""

from __future__ import annotations

import unicodedata

LINEA_ORDER: list[str] = [
    "Calidad",
    "Expansión",
    "Educación para toda la vida",
    "Experiencia",
    "Transformación Organizacional",
    "Sostenibilidad",
]


def _normalize(s: str) -> str:
    """Minúsculas sin tildes ni guiones bajos para comparación tolerante."""
    clean = str(s).strip().lower().replace("_", " ")
    return unicodedata.normalize("NFD", clean).encode("ascii", "ignore").decode()


_ORDER_MAP: dict[str, int] = {_normalize(ln): i for i, ln in enumerate(LINEA_ORDER)}


def linea_sort_key(linea: str) -> int:
    """Índice canónico de la línea; desconocidas van al final."""
    return _ORDER_MAP.get(_normalize(linea), len(LINEA_ORDER))
