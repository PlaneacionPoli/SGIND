"""Calendario laboral de Colombia: festivos nacionales (Ley 51 de 1983, «Ley Emiliani») y días hábiles."""

from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache

from dateutil.easter import easter


def _siguiente_lunes(d: date) -> date:
    """Traslado al lunes siguiente; si ya es lunes, se queda."""
    return d + timedelta(days=(7 - d.weekday()) % 7)


@lru_cache(maxsize=32)
def festivos(anio: int) -> frozenset[date]:
    pascua = easter(anio)
    fijos = [
        date(anio, 1, 1),  # Año Nuevo
        date(anio, 5, 1),  # Día del Trabajo
        date(anio, 7, 20),  # Independencia
        date(anio, 8, 7),  # Batalla de Boyacá
        date(anio, 12, 8),  # Inmaculada Concepción
        date(anio, 12, 25),  # Navidad
        pascua - timedelta(days=3),  # Jueves Santo
        pascua - timedelta(days=2),  # Viernes Santo
    ]
    trasladados = [
        *([date(anio, 7, 9)] if anio >= 2026 else []),  # Virgen de Chiquinquirá (Ley 2578 de 2026)
        date(anio, 1, 6),  # Reyes Magos
        date(anio, 3, 19),  # San José
        date(anio, 6, 29),  # San Pedro y San Pablo
        date(anio, 8, 15),  # Asunción
        date(anio, 10, 12),  # Día de la Raza
        date(anio, 11, 1),  # Todos los Santos
        date(anio, 11, 11),  # Independencia de Cartagena
        pascua + timedelta(days=39),  # Ascensión
        pascua + timedelta(days=60),  # Corpus Christi
        pascua + timedelta(days=68),  # Sagrado Corazón
    ]
    return frozenset(fijos + [_siguiente_lunes(d) for d in trasladados])


def es_habil(d: date) -> bool:
    return d.weekday() < 5 and d not in festivos(d.year)


def habil_anterior(d: date) -> date:
    """`d` si es día hábil; si no, el día hábil inmediatamente anterior."""
    while not es_habil(d):
        d -= timedelta(days=1)
    return d
