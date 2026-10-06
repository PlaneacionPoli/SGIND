"""Asociación indicador ↔ marco (PDI): consulta para filtros y fichas. Módulo puro
(DataFrames), sin Excel ni FastAPI. La fuente de cada PDI es su propia hoja del catálogo
(PDI_2022_2026, PDI_2026_2030…), con códigos numéricos. Ver impact_report.md §4.1.
"""

from __future__ import annotations

import pandas as pd

from app.domain.marcos import get_marcos
from app.domain.taxonomia import load_taxonomia, norm_texto


def ids_de_linea(validas: pd.DataFrame, version_id: str, linea: str | None) -> set[str] | None:
    """Ids de indicadores asociados a una línea del marco (por nombre o id).

    None = sin filtro (linea vacía o 'Todos'). Línea desconocida → conjunto vacío.
    """
    if not linea or linea == "Todos":
        return None
    tax = load_taxonomia(version_id)
    buscado = norm_texto(linea)
    linea_id = next(
        (ln.id for ln in tax.lineas if buscado in (norm_texto(ln.nombre), norm_texto(ln.id))), None
    )
    if linea_id is None or validas.empty:
        return set()
    sel = validas[(validas["version_id"] == version_id) & (validas["linea_id"] == linea_id)]
    return set(sel["Id"].astype(str))


def asociaciones_ficha(
    validas: pd.DataFrame,
    indicador_id: str,
    desde: int | None,
    hasta: int | None,
    tipo: str = "PDI",
) -> list[dict]:
    """Asociaciones del indicador en cada PDI cuya vigencia cruza la del indicador
    (año de inicio `desde`, año de fin `hasta`; None = sin límite). Un indicador
    iniciado en 2023 muestra el PDI 2022-2026 y el 2026-2030; uno iniciado en 2027,
    solo el segundo (impact_report.md D7)."""
    if validas.empty:
        return []
    propias = validas[validas["Id"].astype(str) == str(indicador_id)]
    resultado: list[dict] = []
    for marco in get_marcos(tipo):
        if not marco.taxonomia or not marco.se_traslapa(desde if desde is not None else 0, hasta):
            continue
        filas = propias[propias["version_id"] == marco.version_id]
        if filas.empty:
            continue
        tax = load_taxonomia(marco.taxonomia)
        nombres_l = {ln.id: ln.nombre for ln in tax.lineas}
        nombres_o = {o.id: o.nombre for ln in tax.lineas for o in ln.objetivos}
        nombres_m = {m.id: m.nombre for _, _, m in tax.iter_metas()}
        for _, f in filas.iterrows():
            resultado.append(
                {
                    "version_id": marco.version_id,
                    "pdi": marco.nombre,
                    "linea": nombres_l.get(f["linea_id"]),
                    "objetivo": nombres_o.get(f["objetivo_id"]),
                    "meta": nombres_m.get(f["meta_id"]),
                }
            )
    return resultado
