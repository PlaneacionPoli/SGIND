"""Servicio de indicadores con pipeline ETL."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from app.domain.calculos import obtener_ultimo_registro
from app.domain.cmi_filters import CMIFilterService
from app.services.etl_pipeline import ETLPipelineService
from app.services.excel_reader import ExcelReaderService
from app.services.tracking_cache import get_tracking_dataframe


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        if math.isnan(value):
            return None
        return round(float(value), 4)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _row_to_dict(row: pd.Series, fields: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for field in fields:
        if field in row.index:
            out[field] = _json_safe(row[field])
    return out


_INDICATOR_FIELDS = [
    "Id",
    "Indicador",
    "Proceso",
    "Subproceso",
    "Linea",
    "Objetivo",
    "Anio",
    "Mes",
    "Periodo",
    "Meta",
    "Ejecucion",
    "Cumplimiento",
    "Cumplimiento_norm",
    "Categoria",
    "Clasificacion",
    "Fecha",
]


class IndicatorService:
    def __init__(self, excel: ExcelReaderService) -> None:
        self._excel = excel
        self._etl = ETLPipelineService(excel)
        self._cmi = CMIFilterService(excel)

    def _load(self, *, historico: bool = False, cierres: bool = True) -> pd.DataFrame:
        if cierres and not historico:
            return self._etl.leer_cierres()
        return get_tracking_dataframe(self._excel, historico=historico)

    def _apply_filters(
        self,
        df: pd.DataFrame,
        *,
        anio: int | None = None,
        periodo: str | None = None,
        proceso: str | None = None,
        categoria: str | None = None,
        linea: str | None = None,
        vista: str | None = None,
    ) -> pd.DataFrame:
        out = df
        if anio is not None:
            for col in ("Anio", "Año"):
                if col in out.columns:
                    out = out[out[col] == anio]
                    break
        if periodo is not None:
            for col in ("Periodo", "Mes", "periodo"):
                if col in out.columns:
                    out = out[out[col].astype(str) == str(periodo)]
                    break
        if proceso is not None and "Proceso" in out.columns:
            out = out[out["Proceso"].astype(str).str.lower() == proceso.lower()]
        if categoria is not None and "Categoria" in out.columns:
            out = out[out["Categoria"].astype(str) == categoria]
        if linea is not None and "Linea" in out.columns:
            out = out[out["Linea"].astype(str).str.lower() == linea.lower()]
        if vista:
            vista_norm = vista.strip().lower()
            if vista_norm == "indicadores":
                out = self._cmi.filter_estrategico(out)
            elif vista_norm == "proyectos":
                out = self._cmi.filter_proyectos(out)
        return out

    def list_indicators(
        self,
        *,
        anio: int | None = None,
        periodo: str | None = None,
        proceso: str | None = None,
        categoria: str | None = None,
        linea: str | None = None,
        vista: str | None = None,
        ultimo: bool = True,
        limit: int = 500,
        offset: int = 0,
    ) -> dict[str, Any]:
        try:
            df = self._load()
        except FileNotFoundError as exc:
            return {"total": 0, "items": [], "error": str(exc)}

        df = self._apply_filters(
            df,
            anio=anio,
            periodo=periodo,
            proceso=proceso,
            categoria=categoria,
            linea=linea,
            vista=vista,
        )
        if ultimo:
            df = obtener_ultimo_registro(df)

        total = len(df)
        page = df.iloc[offset : offset + limit]
        items = [_row_to_dict(row, _INDICATOR_FIELDS) for _, row in page.iterrows()]
        return {"total": total, "items": items, "limit": limit, "offset": offset}

    def get_indicator(self, indicator_id: str, *, anio: int | None = None) -> dict[str, Any] | None:
        try:
            df = self._load()
        except FileNotFoundError:
            return None

        if "Id" not in df.columns:
            return None

        df = df[df["Id"].astype(str) == str(indicator_id)]
        if anio is not None and "Anio" in df.columns:
            df = df[df["Anio"] == anio]
        if df.empty:
            return None

        row = df.sort_values("Fecha" if "Fecha" in df.columns else "Id").iloc[-1]
        detail = _row_to_dict(row, _INDICATOR_FIELDS)
        detail["historico"] = [
            _row_to_dict(r, _INDICATOR_FIELDS)
            for _, r in df.sort_values("Fecha" if "Fecha" in df.columns else "Id").iterrows()
        ]
        return detail
