"""Servicio matriz Gestión OM."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.om_builders import (
    build_filtros,
    build_kpis_matriz,
    filter_indicadores_riesgo,
    load_avance_om,
    matriz_to_records,
    merge_om_registros,
)
from app.services.excel_reader import ExcelReaderService
from app.services.om_service import OMService
from app.services.tracking_cache import get_tracking_dataframe


class OMMatrizService:
    def __init__(self, excel: ExcelReaderService) -> None:
        self._excel = excel
        self._om = OMService()

    def _load_historico(self):
        return get_tracking_dataframe(self._excel, historico=True)

    async def get_matriz(
        self,
        db: AsyncSession,
        *,
        anio: int,
        mes: str,
        proceso: str | None = None,
        subproceso: str | None = None,
        mostrar_alerta: bool = False,
    ) -> dict[str, Any]:
        df_riesgo = self._load_historico()
        if df_riesgo.empty:
            return {"error": "No hay datos históricos para Gestión OM.", "filtros": {}, "kpis": {}, "filas": []}

        if "Categoria" not in df_riesgo.columns and "Nivel de cumplimiento" in df_riesgo.columns:
            df_riesgo = df_riesgo.copy()
            df_riesgo["Categoria"] = df_riesgo["Nivel de cumplimiento"]

        filtros = build_filtros(df_riesgo)
        registros_orm = await self._om.list_registros(db, anio=anio, periodo=mes)
        registros = [
            {
                "id": r.id,
                "id_indicador": r.id_indicador,
                "nombre_indicador": r.nombre_indicador,
                "proceso": r.proceso,
                "tiene_om": r.tiene_om,
                "tipo_accion": r.tipo_accion,
                "numero_om": r.numero_om,
                "comentario": r.comentario,
            }
            for r in registros_orm
        ]
        avances = load_avance_om(self._excel)
        df_filtrado = filter_indicadores_riesgo(
            df_riesgo,
            anio=anio,
            mes=mes,
            proceso=proceso,
            subproceso=subproceso,
            mostrar_alerta=mostrar_alerta,
        )
        df_tabla = merge_om_registros(df_filtrado, registros, avances)
        return {
            "anio": anio,
            "mes": mes,
            "filtros": filtros,
            "filtros_aplicados": {
                "anio": anio,
                "mes": mes,
                "proceso": proceso or "Todos",
                "subproceso": subproceso or "Todos",
                "mostrar_alerta": mostrar_alerta,
            },
            "kpis": build_kpis_matriz(df_tabla),
            "filas": matriz_to_records(df_tabla),
            "tipo_accion_colores": {
                "OM Kawak": "#2563EB",
                "Reto Plan Anual": "#D97706",
                "Proyecto Institucional": "#0EA5A4",
                "Otro": "#6B7280",
                "Sin acción": "#94A3B8",
            },
        }
