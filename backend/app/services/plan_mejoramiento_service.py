"""Servicio Plan de Mejoramiento."""

from __future__ import annotations

import io
from typing import Any

import pandas as pd

from app.domain.plan_mejoramiento_builders import (
    CORTE_SEMESTRAL,
    TENDENCIA_METRICAS_FILTRO_OPTIONS,
    apply_cna_filters,
    apply_metricas_filters,
    apply_plan_indicadores_filters,
    build_acciones_section,
    build_filtros_cna,
    build_filtros_corte,
    build_graficos,
    build_indicador_detalle,
    build_kpis,
    build_metrica_detalle,
    build_metricas_historico,
    build_metricas_kpis,
    build_metricas_por_factor,
    build_metricas_tabla_agrupada,
    build_plan_indicadores_kpis,
    build_plan_indicadores_tabla_historico,
    build_plan_indicadores_tabla_metas,
    build_tabla_cna,
    load_acciones_mejora,
    load_plan_indicadores,
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
        filtros_corte = (
            build_filtros_corte(cierres) if not cierres.empty else {"anios": [], "cortes": []}
        )
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

        df_filtered = apply_cna_filters(
            df, factor=factor, caracteristica=caracteristica, nombre=nombre
        )
        ids_cna = (
            set(df_filtered["Id"].astype(str).tolist())
            if not df_filtered.empty and "Id" in df_filtered.columns
            else set()
        )
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

    # ─────────────────────────────────────────────────────────────────────
    # Pestaña "Indicadores" (Meta/Ejecución/%Cump 2025-2026 + metas 2026-2030)
    # Ver docs/migration/PLAN_MIGRACION_PRIORIZADO.md ítem 0.
    # ─────────────────────────────────────────────────────────────────────

    def get_indicadores_dashboard(
        self,
        *,
        subvista: str = "metas",
        factor: str | None = None,
        tipo: str | None = None,
        nombre: str | None = None,
    ) -> dict[str, Any]:
        df = load_plan_indicadores(self._excel)
        if df.empty:
            return {
                "kpis": {"total": 0, "con_meta_futura": 0, "con_cumplimiento_historico": 0,
                         "aprobados": 0, "pct_aprobados": 0},
                "filtros": {"factores": [], "tipos": []},
                "tabla": [],
                "total": 0,
            }

        kpis = build_plan_indicadores_kpis(df)
        rows = apply_plan_indicadores_filters(df, factor=factor, tipo=tipo, nombre=nombre)
        tabla = (
            build_plan_indicadores_tabla_historico(rows)
            if subvista == "historico"
            else build_plan_indicadores_tabla_metas(rows)
        )
        factores = sorted(df["Factor"].dropna().unique().tolist()) if "Factor" in df.columns else []
        tipos = sorted(df["Tipo"].dropna().unique().tolist()) if "Tipo" in df.columns else []

        return {
            "kpis": kpis,
            "filtros": {"factores": factores, "tipos": tipos},
            "tabla": tabla,
            "total": len(tabla),
        }

    def export_indicadores_excel(
        self,
        *,
        subvista: str = "metas",
        factor: str | None = None,
        tipo: str | None = None,
        nombre: str | None = None,
    ) -> bytes:
        """Exportación a Excel de la pestaña Indicadores — paridad con
        pages/plan_mejoramiento.py::_render_export_button (valores numéricos
        crudos, no el texto formateado de la tabla en pantalla)."""
        df = load_plan_indicadores(self._excel)
        rows = apply_plan_indicadores_filters(df, factor=factor, tipo=tipo, nombre=nombre)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            if subvista == "historico":
                records = build_plan_indicadores_tabla_historico(rows)
                data = pd.DataFrame(
                    [
                        {
                            "Factor": r["factor"],
                            "Indicador": r["indicador"],
                            "Meta 2025": r["meta_2025"]["valor"],
                            "Ejecución 2025": r["ejecucion_2025"]["valor"],
                            "% Cump 2025": r["cump_2025"]["valor"],
                            "Meta 2026": r["meta_2026"]["valor"],
                            "Ejecución 2026": r["ejecucion_2026"]["valor"],
                            "% Cump 2026": r["cump_2026"]["valor"],
                        }
                        for r in records
                    ]
                )
                data.to_excel(writer, index=False, sheet_name="Cumplimiento historico")
            else:
                records = build_plan_indicadores_tabla_metas(rows)
                data = pd.DataFrame(
                    [
                        {
                            "Factor": r["factor"],
                            "Indicador": r["indicador"],
                            "Tipo": r["tipo"],
                            **{
                                f"Meta {y}": r["metas"][y]["valor"]
                                for y in ("2026", "2027", "2028", "2029", "2030")
                            },
                        }
                        for r in records
                    ]
                )
                data.to_excel(writer, index=False, sheet_name="Metas 2026-2030")
        return buffer.getvalue()

    def get_indicador_detalle(self, *, factor: str, indicador: str) -> dict[str, Any] | None:
        df = load_plan_indicadores(self._excel)
        if df.empty or "Factor" not in df.columns or "Indicador" not in df.columns:
            return None
        match = df[(df["Factor"] == factor) & (df["Indicador"] == indicador)]
        if match.empty:
            return None
        return build_indicador_detalle(match.iloc[0])

    # ─────────────────────────────────────────────────────────────────────
    # Pestaña "Métricas" (serie histórica anual CNA, tendencia, sparkline)
    # ─────────────────────────────────────────────────────────────────────

    def get_metricas_dashboard(
        self,
        *,
        factor: str | None = None,
        tendencia: str | None = None,
        nombre: str | None = None,
    ) -> dict[str, Any]:
        df = build_metricas_historico(self._excel)
        if df.empty:
            return {
                "kpis": {"total": 0, "factores_cubiertos": 0, "n_creciente": 0, "n_decreciente": 0,
                         "pct_creciente": 0, "pct_decreciente": 0},
                "filtros": {"factores": [], "tendencias": TENDENCIA_METRICAS_FILTRO_OPTIONS},
                "grafico_por_factor": [],
                "tabla": [],
                "total": 0,
            }

        agrupado_total = build_metricas_tabla_agrupada(df)
        kpis = build_metricas_kpis(agrupado_total)
        grafico_por_factor = build_metricas_por_factor(agrupado_total)
        rows = apply_metricas_filters(df, factor=factor, tendencia=tendencia, nombre=nombre)
        tabla = build_metricas_tabla_agrupada(rows)
        factores = sorted(df["Factor"].dropna().unique().tolist()) if "Factor" in df.columns else []

        return {
            "kpis": kpis,
            "filtros": {"factores": factores, "tendencias": TENDENCIA_METRICAS_FILTRO_OPTIONS},
            "grafico_por_factor": grafico_por_factor,
            "tabla": tabla,
            "total": len(tabla),
        }

    def get_metrica_detalle(
        self, *, factor: str, indicador: str, subindicador: str | None = None
    ) -> dict[str, Any] | None:
        df = build_metricas_historico(self._excel)
        if df.empty or "Factor" not in df.columns or "Indicador" not in df.columns:
            return None
        mask = (df["Factor"] == factor) & (df["Indicador"] == indicador)
        if subindicador is not None and "Subindicador" in df.columns:
            mask &= df["Subindicador"] == subindicador
        match = df[mask]
        if match.empty:
            return None
        return build_metrica_detalle(match.iloc[0])
