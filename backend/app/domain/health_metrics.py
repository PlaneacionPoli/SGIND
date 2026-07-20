"""Recálculo de cumplimiento — portado desde core/domain/health_metrics.py."""

import logging

import pandas as pd

from app.domain.categorization import get_ids_plan_anual
from app.domain.constants import IDS_TOPE_100

logger = logging.getLogger(__name__)


def recalcular_cumplimiento_faltante(
    meta,
    ejecucion,
    sentido: str = "Positivo",
    id_indicador=None,
) -> float:
    if meta is None or ejecucion is None:
        return float("nan")

    try:
        m = float(meta)
        e = float(ejecucion)
    except (TypeError, ValueError):
        return float("nan")

    if pd.isna(m) or pd.isna(e):
        return float("nan")

    sentido_str = str(sentido).strip().lower() if sentido else "positivo"

    if m == 0 and e == 0:
        return 1.0

    if sentido_str == "negativo" and e == 0 and m > 0:
        return 1.0

    try:
        if sentido_str == "positivo":
            if m == 0:
                return float("nan")
            raw = e / m
        elif sentido_str == "negativo":
            if e == 0:
                return float("nan")
            raw = m / e
        else:
            if m == 0:
                return float("nan")
            raw = e / m
    except ZeroDivisionError:
        return float("nan")

    if pd.isna(raw):
        return float("nan")

    id_str = str(id_indicador).strip() if id_indicador is not None else ""
    es_plan_anual = id_str in get_ids_plan_anual()
    es_tope_100 = id_str in IDS_TOPE_100
    tope = 1.0 if (es_plan_anual or es_tope_100) else 1.3

    return min(max(raw, 0.0), tope)
