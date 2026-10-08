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

# Líneas del PDI 2026-2030 (después de las del 2022-2026; nunca conviven en una misma vista).
LINEA_ORDER_2026: list[str] = [
    "Calidad e Innovación Educativa",
    "Experiencia Centrada en las Personas",
    "Expansión con Compromiso Social",
    "Desarrollo Sostenible",
]
_ORDER_MAP.update({_normalize(ln): len(LINEA_ORDER) + i for i, ln in enumerate(LINEA_ORDER_2026)})


def linea_sort_key(linea: str) -> int:
    """Índice canónico de la línea; desconocidas van al final."""
    return _ORDER_MAP.get(_normalize(linea), len(LINEA_ORDER) + len(LINEA_ORDER_2026))
