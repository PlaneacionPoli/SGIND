"""Categorización de cumplimiento — portado desde core/domain/categorization.py."""

import logging

import pandas as pd

from app.domain.constants import (
    IDS_NEGATIVO_PCT,
    IDS_PLAN_ANUAL_DEFAULT,
    UMBRAL_ALERTA,
    UMBRAL_ALERTA_NEG_PCT,
    UMBRAL_ALERTA_PA,
    UMBRAL_PELIGRO,
    UMBRAL_PELIGRO_NEG_PCT,
    UMBRAL_SOBRECUMPLIMIENTO,
    UMBRAL_SOBRECUMPLIMIENTO_PA,
    CategoriaCumplimiento,
)

logger = logging.getLogger(__name__)

_ids_plan_anual: frozenset[str] | None = None


def set_ids_plan_anual(ids: frozenset[str]) -> None:
    global _ids_plan_anual
    _ids_plan_anual = ids


def get_ids_plan_anual() -> frozenset[str]:
    return _ids_plan_anual if _ids_plan_anual is not None else IDS_PLAN_ANUAL_DEFAULT


def categorizar_cumplimiento(cumplimiento, id_indicador=None, regimen=None) -> str:
    """Categoriza un valor de cumplimiento en Peligro/Alerta/Cumplimiento/
    Sobrecumplimiento/Sin dato.

    El régimen (general/plan_anual/negativo_pct) se determina por `id_indicador`
    contra las listas de `constants.py`, salvo que se pase `regimen`
    explícitamente — usado por categorías que aplican Plan Anual
    incondicionalmente por tipo (Retos, Proyectos), no por pertenecer a la
    lista de IDs. Ver docs/tecnico/05-reglas-de-negocio.md."""
    try:
        if pd.isna(cumplimiento):
            return CategoriaCumplimiento.SIN_DATO.value
    except (ValueError, TypeError):
        return CategoriaCumplimiento.SIN_DATO.value

    if regimen is not None:
        es_plan_anual = regimen == "plan_anual"
        es_negativo_pct = regimen == "negativo_pct"
    else:
        es_plan_anual = False
        if id_indicador is not None:
            es_plan_anual = str(id_indicador).strip() in get_ids_plan_anual()

        es_negativo_pct = False
        if not es_plan_anual and id_indicador is not None:
            es_negativo_pct = str(id_indicador).strip() in IDS_NEGATIVO_PCT

    try:
        if isinstance(cumplimiento, str):
            cumpl_clean = cumplimiento.replace("%", "").strip()
            if "," in cumpl_clean:
                cumpl_clean = cumpl_clean.replace(".", "").replace(",", ".")
            c = float(cumpl_clean)
        else:
            c = float(cumplimiento)
    except (TypeError, ValueError):
        return CategoriaCumplimiento.SIN_DATO.value

    if es_plan_anual:
        if c < UMBRAL_PELIGRO:
            return CategoriaCumplimiento.PELIGRO.value
        if c < UMBRAL_ALERTA_PA:
            return CategoriaCumplimiento.ALERTA.value
        if c <= UMBRAL_SOBRECUMPLIMIENTO_PA:
            return CategoriaCumplimiento.CUMPLIMIENTO.value
        return CategoriaCumplimiento.SOBRECUMPLIMIENTO.value

    if es_negativo_pct:
        if c < UMBRAL_ALERTA_NEG_PCT:
            return CategoriaCumplimiento.CUMPLIMIENTO.value
        if c <= UMBRAL_PELIGRO_NEG_PCT:
            return CategoriaCumplimiento.ALERTA.value
        return CategoriaCumplimiento.PELIGRO.value

    if c < UMBRAL_PELIGRO:
        return CategoriaCumplimiento.PELIGRO.value
    if c < UMBRAL_ALERTA:
        return CategoriaCumplimiento.ALERTA.value
    if c < UMBRAL_SOBRECUMPLIMIENTO:
        return CategoriaCumplimiento.CUMPLIMIENTO.value
    return CategoriaCumplimiento.SOBRECUMPLIMIENTO.value
