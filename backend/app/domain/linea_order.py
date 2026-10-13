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


# Orden institucional de los indicadores dentro de cada línea (aplica a ambos PDI).
# Clave: prefijo normalizado de la línea; valor: indicadores en el orden deseado.
INDICADORES_ORDER: dict[tuple[str, ...], list[str]] = {
    ("expansion",): [
        "Total Población",
        "Total estudiantes nuevos",
        "Total estudiantes antiguos",
        "Estudiantes Presencial",
        "Estudiantes Virtual",
        "Estudiantes Pregrado",
        "Estudiantes Posgrado",
        "Lanzamiento de nuevos programas presencial",
        "Lanzamiento de nuevos programas virtual",
        "Brand equity",
        "Conocimiento espontáneo",
    ],
    ("sostenibilidad", "desarrollo sostenible"): [
        "Cumplimiento de Ingresos",
        "Cumplimiento EBITDA",
        "Utilidad Neta",
        "Inversión en CAPEX de la utilidad anterior",
        "Caja",
        "Nivel de Cumplimiento Opex",
        "CAPEX",
        "Compensación de Gases de Efecto Invernadero",
        "GreenMetric - Nacional",
        "Índice de Inclusión",
        "Estudiantes con Becas",
        "Participación de POLI- voluntariados (Estudiantes- Colaboradores)",
        "Impacto de actividades de Responsabilidad y proyección",
        "Nivel de empleabilidad del graduado",
    ],
}
# Variantes de escritura presentes en la fuente (ya normalizadas) -> nombre canónico normalizado.
_ALIAS: dict[str, str] = {
    "cumplimiento ebidta": "cumplimiento ebitda",
    "cumplimiento total estudiantes antiguos": "total estudiantes antiguos",
}

# Nombre con que se muestra un indicador cuyo nombre en la fuente no es el institucional.
NOMBRE_VISIBLE: dict[str, str] = {
    "cumplimiento total estudiantes antiguos": "Total estudiantes antiguos",
}


def _indicador_key(nombre: str) -> str:
    clean = _normalize(nombre).replace("*", "")
    clean = " ".join(clean.split())
    return _ALIAS.get(clean, clean)


_INDICADOR_MAPS: list[tuple[tuple[str, ...], dict[str, int], int]] = [
    (prefijos, {_indicador_key(n): i for i, n in enumerate(orden)}, len(orden))
    for prefijos, orden in INDICADORES_ORDER.items()
]


def indicador_sort_key(linea: str, indicador: str) -> int:
    """Posición del indicador dentro de su línea; sin orden definido va al final (orden estable)."""
    linea_n = _normalize(linea)
    for prefijos, mapa, n in _INDICADOR_MAPS:
        if linea_n.startswith(prefijos):
            return mapa.get(_indicador_key(indicador), n)
    return 0


def nombre_visible(indicador: str) -> str:
    """Nombre institucional para mostrar; si no hay renombre, el original."""
    return NOMBRE_VISIBLE.get(" ".join(_normalize(indicador).split()), indicador)
