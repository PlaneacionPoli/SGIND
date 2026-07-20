"""Servicio Plan de Mejoramiento."""

from __future__ import annotations

from typing import Any

from app.domain.plan_mejoramiento_builders import (
    CORTE_SEMESTRAL,
    apply_cna_filters,
    build_acciones_section,
    build_filtros_cna,
    build_filtros_corte,
    build_graficos,
    build_kpis,
    build_tabla_cna,
    load_acciones_mejora,
)
from app.domain.strategic_processors import StrategicProcessors
from app.services.excel_reader import ExcelReaderService
from app.services.strategic_loaders import StrategicLoaders


class PlanMejoramientoService:
    def __init__(self, excel: ExcelReaderService) -> None:
        self._excel = excel
        self._strategic = StrategicProcessors(excel)
        self._loaders = StrategicLoaders(excel)

    def get_filtros(self) -> dict:
        """Devuelve los filtros disponibles para Plan de Mejoramiento."""
        cierres = self._loaders.load_cierres()
        filtros_corte = build_filtros_corte(cierres) if not cierres.empty else {"anios": [], "cortes": []}
        catalog = self._loaders.load_cna_catalog()
        factores: list[str] = []
        if not catalog.empty and "Factor" in catalog.columns:
            factores = sorted(catalog["Factor"].dropna().unique().tolist())
        caracteristicas: list[str] = []
        if not catalog.empty and "Característica" in catalog.columns:
            caracteristicas = sorted(catalog["Característica"].dropna().unique().tolist())
        return {**filtros_corte, "factores": factores, "caracteristicas": caracteristicas}

    def get_dashboard(
        self,
        *,
        anio: int | None = None,
        corte: str | None = None,
        factor: str | None = None,
        caracteristica: str | None = None,
        nombre: str | None = None,
    ) -> dict[str, Any]:
        cierres = self._loaders.load_cierres()
        if cierres.empty:
            return {"error": "No se encontró información de cierres."}

        filtros_corte = build_filtros_corte(cierres)
        anio_eff = anio or filtros_corte["anio_default"]
        corte_eff = corte or filtros_corte["corte_default"]
        mes = CORTE_SEMESTRAL.get(corte_eff, 12)

        df = self._strategic.preparar_cna_con_cierre(int(anio_eff), int(mes))
        catalog = self._loaders.load_cna_catalog()
        filtros_cna = build_filtros_cna(df, catalog, factor_sel=factor)

        df_filtered = apply_cna_filters(df, factor=factor, caracteristica=caracteristica, nombre=nombre)
        ids_cna = set(df_filtered["Id"].astype(str).tolist()) if not df_filtered.empty and "Id" in df_filtered.columns else set()
        acciones = load_acciones_mejora(self._excel)

        return {
            "anio": int(anio_eff),
            "mes": mes,
            "corte": corte_eff,
            "filtros_corte": filtros_corte,
            "filtros_cna": filtros_cna,
            "filtros_aplicados": {
                "anio": int(anio_eff),
                "corte": corte_eff,
                "factor": factor or "Todos",
                "caracteristica": caracteristica or "Todas",
                "nombre": nombre or "",
            },
            "kpis": build_kpis(df_filtered, catalog),
            "graficos": build_graficos(df_filtered),
            "tabla_cna": build_tabla_cna(df_filtered),
            "acciones": build_acciones_section(acciones, ids_cna if ids_cna else None),
            "total_indicadores": len(df_filtered),
        }
