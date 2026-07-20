"""Servicio Seguimiento Operativo."""

from __future__ import annotations

import io
from typing import Any

import pandas as pd

from app.domain.seguimiento_builders import apply_filters, build_dashboard, load_tracking
from app.services.excel_reader import ExcelReaderService


class SeguimientoService:
    def __init__(self, excel: ExcelReaderService) -> None:
        self._excel = excel

    def get_filtros(self) -> dict:
        """Devuelve años, meses, procesos y estados disponibles en el tracking."""
        df = load_tracking(self._excel)
        if df.empty:
            return {"anios": [], "meses": [], "procesos": [], "estados": []}
        anios: list[int] = sorted(
            [int(a) for a in df["Año"].dropna().unique().tolist() if str(a).isdigit()], reverse=True
        ) if "Año" in df.columns else []
        meses: list[int] = sorted(
            [int(m) for m in df["Mes"].dropna().unique().tolist() if str(m).isdigit()]
        ) if "Mes" in df.columns else []
        procesos: list[str] = sorted(df["Proceso"].dropna().unique().tolist()) if "Proceso" in df.columns else []
        estados: list[str] = sorted(df["Estado"].dropna().unique().tolist()) if "Estado" in df.columns else []
        anio_default = anios[0] if anios else None
        mes_default = max(meses) if meses else None
        return {
            "anios": anios,
            "anio_default": anio_default,
            "meses": meses,
            "mes_default": mes_default,
            "procesos": procesos,
            "estados": estados,
        }

    def get_dashboard(
        self,
        *,
        anio: int | None = None,
        mes: int | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> dict[str, Any]:
        df = load_tracking(self._excel)
        if df.empty:
            return {"error": "No se encontró Tracking Mensual en Seguimiento_Reporte.xlsx", "kpis": {}}
        filtros = build_dashboard(df, anio=anio, mes=mes, proceso=proceso, estado=estado)
        if anio is None:
            anio = filtros["filtros"].get("anio_default")
        if mes is None:
            mes = filtros["filtros"].get("mes_default")
        return build_dashboard(df, anio=anio, mes=mes, proceso=proceso, estado=estado)

    def export_excel(
        self,
        *,
        anio: int | None = None,
        mes: int | None = None,
        proceso: str | None = None,
        estado: str | None = None,
    ) -> bytes:
        df = load_tracking(self._excel)
        df_view = apply_filters(df, anio=anio, mes=mes, proceso=proceso, estado=estado)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_view.to_excel(writer, index=False, sheet_name="Tracking Filtrado")
        return buffer.getvalue()
