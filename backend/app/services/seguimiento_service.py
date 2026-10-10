"""Servicio Seguimiento Operativo."""

from __future__ import annotations

import io
from typing import Any

import pandas as pd

from app.domain.seguimiento_builders import (
    apply_filters,
    build_dashboard,
    build_filtros,
    load_tracking,
)
from app.services.cmi_service import MAX_ANIO_FILTROS
from app.services.excel_reader import ExcelReaderService


class SeguimientoService:
    def __init__(self, excel: ExcelReaderService) -> None:
        self._excel = excel

    def get_filtros(self) -> dict:
        """Devuelve años, meses, procesos y estados disponibles en el tracking."""
        df = load_tracking(self._excel)
        if df.empty:
            return {"anios": [], "meses": [], "procesos": [], "estados": []}
        if "Año" in df.columns:
            df = df[df["Año"].isna() | (df["Año"] <= MAX_ANIO_FILTROS)]
        return build_filtros(df)

    def get_dashboard(
        self,
        *,
        anio: int | None = None,
        mes: int | None = None,
        proceso: str | None = None,
        estado: str | None = None,
        limit: int = 500,
        offset: int = 0,
        orden_por: str | None = None,
        orden_dir: str = "asc",
        busqueda: str | None = None,
    ) -> dict[str, Any]:
        df = load_tracking(self._excel)
        if df.empty:
            return {
                "error": "No se encontró Tracking Mensual en Seguimiento_Reporte.xlsx",
                "kpis": {},
            }
        # anio/mes = None es un valor explícito de "Todos" (el frontend siempre
        # envía un valor concreto una vez carga los filtros por defecto).
        return build_dashboard(
            df,
            anio=anio,
            mes=mes,
            proceso=proceso,
            estado=estado,
            limit=limit,
            offset=offset,
            orden_por=orden_por,
            orden_dir=orden_dir,
            busqueda=busqueda,
        )

    def export_excel(
        self,
        *,
        anio: int | None = None,
        mes: int | None = None,
        proceso: str | None = None,
        estado: str | None = None,
        busqueda: str | None = None,
    ) -> bytes:
        df = load_tracking(self._excel)
        df_view = apply_filters(
            df, anio=anio, mes=mes, proceso=proceso, estado=estado, busqueda=busqueda
        )
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_view.to_excel(writer, index=False, sheet_name="Tracking Filtrado")
        return buffer.getvalue()
