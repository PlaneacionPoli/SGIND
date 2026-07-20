"""Servicio CMI — agregaciones estratégicas alineadas con Streamlit tabulado."""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from app.core.ttl_cache import cache_get

from app.domain.cmi_builders import (
    CORTE_POR_MES,
    CORTE_SEMESTRAL,
    build_alertas,
    build_cumplimiento_por_linea,
    build_distribucion_nivel,
    build_indicadores_listado,
    build_insights,
    build_lineas_detalle,
    build_vista_rapida_lineas,
    calcular_kpis,
    default_anio,
    default_corte,
    df_to_records,
    linea_color,
    previous_corte,
)
from app.domain.linea_order import linea_sort_key
from app.domain.calidad_builders import build_calidad_dashboard, filter_calidad, load_calidad_data
from app.domain.cmi_filters import CMIFilterService
from app.domain.procesos_builders import (
    MESES_OPCIONES,
    TIPO_PROCESO_COLORS,
    apply_ui_filters,
    avg_cumplimiento,
    build_analisis_avanzado,
    build_banner,
    build_catalog_charts,
    build_export_dataframe,
    build_export_excel_bytes,
    build_ejecucion_variacion,
    build_filtros_options,
    build_historico_catalog,
    build_indicadores_procesos_listado,
    build_indicadores_summary,
    build_proceso_bars,
    build_procesos_detalle,
    build_procesos_kpis,
    build_tipo_proceso_cards,
    build_unidades_detalle,
    build_variacion_analisis,
    build_vista_global,
    default_anio_procesos,
    default_mes,
    filter_by_anio_mes,
    get_prev_month_for_year,
    latest_per_indicator,
    mes_nombre,
    mes_to_num,
    prepare_tracking,
)
from app.domain.procesos_loaders import load_process_map
from app.domain.resumen_builders import ensure_nivel_cumplimiento
from app.domain.strategic_processors import StrategicProcessors
from app.services.excel_reader import ExcelReaderService
from app.services.indicator_service import IndicatorService
from app.services.narrativa_ia_service import generar_narrativa_ficha
from app.services.strategic_loaders import StrategicLoaders
from app.services.tracking_cache import get_tracking_dataframe

# Desde la fusión 2026-07-14, la ficha técnica vive en la hoja
# "Ficha Tecnica Detalle" del directorio maestro dedicado (Catalogo de
# Indicadores.xlsx), no en 'Ficha_Tecnica_Indicadores.xlsx' (archivado en
# data/raw/_archivados/).
_FICHA_PATH = "raw/Catalogo de Indicadores.xlsx"
_FICHA_SHEET = "Ficha Tecnica Detalle"

_YEAR_PREPARED_CACHE: dict[tuple[str, int, bool], tuple[float, pd.DataFrame]] = {}


class CMIService:
    def __init__(self, excel: ExcelReaderService) -> None:
        self._excel = excel
        self._strategic = StrategicProcessors(excel)
        self._loaders = StrategicLoaders(excel)
        self._cmi = CMIFilterService(excel)
        self._indicators = IndicatorService(excel)

    def _available_anios(self) -> list[int]:
        cierres = self._loaders.load_cierres()
        if cierres.empty or "Anio" not in cierres.columns:
            return [date.today().year]
        anios = sorted(
            pd.to_numeric(cierres["Anio"], errors="coerce").dropna().astype(int).unique().tolist()
        )
        return anios or [date.today().year]

    def _resolve_mes(self, mes: int | None, corte: str | None) -> int:
        if corte and corte in CORTE_SEMESTRAL:
            return CORTE_SEMESTRAL[corte]
        if mes in (6, 12):
            return int(mes)
        return 12

    def _enrich_ficha(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "Id" not in df.columns:
            return df
        ft: pd.DataFrame | None = None
        if (self._excel.data_root / _FICHA_PATH).exists():
            try:
                ft = self._excel.read_excel(_FICHA_PATH, sheet_name=_FICHA_SHEET)
            except Exception:
                ft = None
        if ft is None or ft.empty:
            return df

        ft.columns = [str(c).strip() for c in ft.columns]
        desc_col = next((c for c in ft.columns if "descripci" in c.lower()), None)
        wanted = [
            c
            for c in [
                desc_col,
                "Responsable del calculo",
                "Fuente V1",
                "Formula",
                "Frecuencia",
            ]
            if c and c in ft.columns
        ]
        if not wanted or "Id" not in ft.columns:
            return df

        ft_sub = ft[["Id"] + wanted].drop_duplicates(subset=["Id"], keep="first").copy()
        if desc_col and desc_col in ft_sub.columns:
            ft_sub = ft_sub.rename(columns={desc_col: "Descripcion"})
        out = df.copy()
        out["Id"] = out["Id"].astype(str)
        ft_sub["Id"] = ft_sub["Id"].astype(str)
        return out.merge(ft_sub, on="Id", how="left")

    def _prepare_df(self, *, anio: int, mes: int) -> pd.DataFrame:
        df = self._strategic.preparar_pdi_con_cierre(int(anio), int(mes))
        if df.empty:
            return df
        df = ensure_nivel_cumplimiento(df)
        return self._enrich_ficha(df)

    def get_filtros(self) -> dict[str, Any]:
        anios = self._available_anios()
        anio_def = default_anio(anios)
        return {
            "anios": anios,
            "anio_default": anio_def,
            "corte_default": default_corte(anio_def),
            "cortes": list(CORTE_SEMESTRAL.keys()),
        }

    def get_dashboard(self, *, anio: int | None = None, mes: int | None = None, corte: str | None = None) -> dict[str, Any]:
        anios = self._available_anios()
        anio_eff = int(anio) if anio is not None else default_anio(anios)
        mes_eff = self._resolve_mes(mes, corte)
        corte_label = CORTE_POR_MES.get(mes_eff, "Diciembre")

        df = self._prepare_df(anio=anio_eff, mes=mes_eff)
        pdi_catalog = self._loaders.load_pdi_catalog()
        cierres = self._loaders.load_cierres()

        if df.empty:
            return {
                "anio": anio_eff,
                "mes": mes_eff,
                "corte": corte_label,
                "anios_disponibles": anios,
                "cortes": list(CORTE_SEMESTRAL.keys()),
                "total_indicadores": 0,
                "kpis": calcular_kpis(df),
                "cumplimiento_por_linea": [],
                "distribucion_nivel": [],
                "vista_rapida_lineas": [],
                "insights": build_insights(calcular_kpis(df)),
                "lineas_detalle": [],
                "indicadores": [],
                "alertas": {"peligro": 0, "alerta": 0, "items": []},
            }

        kpis = calcular_kpis(df)
        prev_anio, prev_mes = previous_corte(anio_eff, mes_eff)
        df_previous = self._prepare_df(anio=prev_anio, mes=prev_mes)

        return {
            "anio": anio_eff,
            "mes": mes_eff,
            "corte": corte_label,
            "anios_disponibles": anios,
            "cortes": list(CORTE_SEMESTRAL.keys()),
            "total_indicadores": len(df),
            "kpis": kpis,
            "cumplimiento_por_linea": build_cumplimiento_por_linea(df),
            "distribucion_nivel": build_distribucion_nivel(df),
            "vista_rapida_lineas": build_vista_rapida_lineas(df),
            "insights": build_insights(kpis),
            "lineas_detalle": build_lineas_detalle(
                df,
                cierres,
                pdi_catalog,
                df_previous=df_previous,
                anio=anio_eff,
                mes=mes_eff,
            ),
            "indicadores": build_indicadores_listado(df),
            "alertas": build_alertas(df),
        }

    def get_indicador_ficha(self, indicador_id: str, *, anio: int, mes: int | None = None, corte: str | None = None) -> dict[str, Any] | None:
        mes_eff = self._resolve_mes(mes, corte)
        df = self._prepare_df(anio=int(anio), mes=mes_eff)
        if df.empty or "Id" not in df.columns:
            return None
        match = df[df["Id"].astype(str) == str(indicador_id)]
        if match.empty:
            return None
        row = match.iloc[0]
        cierres = self._loaders.load_cierres()
        historico: list[dict[str, Any]] = []
        if not cierres.empty and "Id" in cierres.columns:
            hist = cierres[cierres["Id"].astype(str) == str(indicador_id)].copy()
            hist = ensure_nivel_cumplimiento(hist)
            if not hist.empty and "Anio" in hist.columns:
                hist["Periodo"] = (
                    hist["Anio"].astype(str)
                    + "-"
                    + hist.get("Mes", pd.Series([12] * len(hist))).astype(int).astype(str).str.zfill(2)
                )
                for _, r in hist.sort_values("Periodo").iterrows():
                    historico.append(
                        {
                            "periodo": str(r["Periodo"]),
                            "meta": r.get("Meta"),
                            "ejecucion": r.get("Ejecucion"),
                            "cumplimiento": r.get("cumplimiento_pct"),
                        }
                    )
        record = df_to_records(match)[0]
        record["historico"] = historico
        record["linea_color"] = linea_color(str(row.get("Linea", "")))
        cump = row.get("cumplimiento_pct")
        try:
            cump_f = float(cump) if cump is not None else None
        except (TypeError, ValueError):
            cump_f = None
        record["narrativa_ia"] = generar_narrativa_ficha(
            nombre=str(row.get("Indicador", "")),
            meta=row.get("Meta"),
            ejecucion=row.get("Ejecucion"),
            nivel=str(row.get("Nivel de cumplimiento", "")),
            cumplimiento=cump_f,
            proceso=str(row.get("Linea", "")) or None,
        )
        return record

    def _load_tracking(self) -> pd.DataFrame:
        return get_tracking_dataframe(self._excel, historico=False)

    def _get_year_prepared(
        self,
        tracking: pd.DataFrame,
        map_df: pd.DataFrame,
        *,
        anio: int,
        omit_kawak_cross: bool = False,
    ) -> pd.DataFrame:
        root = str(self._excel.data_root.resolve())
        key = (root, int(anio), omit_kawak_cross)

        def _load() -> pd.DataFrame:
            if tracking.empty or "Anio" not in tracking.columns:
                return pd.DataFrame()
            year_df = tracking[pd.to_numeric(tracking["Anio"], errors="coerce") == int(anio)].copy()
            if year_df.empty:
                return pd.DataFrame()
            prepared = prepare_tracking(year_df, map_df)
            prepared = self._cmi.filter_procesos(
                prepared,
                anio=anio,
                map_df=map_df,
                omit_if_no_cross=not omit_kawak_cross,
            )
            return ensure_nivel_cumplimiento(prepared)

        return cache_get(_YEAR_PREPARED_CACHE, key, _load)

    @staticmethod
    def _slice_by_mes(year_prepared: pd.DataFrame, *, anio: int, mes: int) -> pd.DataFrame:
        if year_prepared.empty:
            return year_prepared
        return filter_by_anio_mes(year_prepared, anio=anio, mes=mes)

    def _prepare_procesos_slice(
        self,
        tracking: pd.DataFrame,
        map_df: pd.DataFrame,
        *,
        anio: int,
        mes: int,
        omit_kawak_cross: bool = False,
    ) -> pd.DataFrame:
        year_prepared = self._get_year_prepared(
            tracking, map_df, anio=anio, omit_kawak_cross=omit_kawak_cross
        )
        return self._slice_by_mes(year_prepared, anio=anio, mes=mes)

    def get_procesos_filtros(self, *, anio: int | None = None) -> dict[str, Any]:
        tracking = self._load_tracking()
        map_df = load_process_map(self._excel)
        anios = self._available_anios()
        anio_eff = int(anio) if anio is not None else default_anio_procesos(anios)
        opts = build_filtros_options(tracking, map_df, self._cmi.load_cmi_worksheet(), anio=anio_eff)
        return {
            "anios": opts["anios"] or anios,
            "anio_default": anio_eff,
            "meses": opts["meses"],
            "mes_default": opts["mes_default"],
            "meses_nombres": MESES_OPCIONES,
            "unidades": opts["unidades"],
            "procesos": opts["procesos"],
            "subprocesos": opts["subprocesos"],
            "clasificaciones": opts["clasificaciones"],
            "frecuencias": opts["frecuencias"],
        }

    def get_procesos_indicators_light(
        self,
        *,
        anio: int,
        mes: int,
        unidad: str | None = None,
        proceso: str | None = None,
        subproceso: str | None = None,
        clasificacion: str | None = None,
        frecuencia: str | None = None,
    ) -> list[dict[str, Any]]:
        """Solo listado de indicadores (sin KPIs/gráficos) — para comparación año anterior en Informe."""
        tracking = self._load_tracking()
        map_df = load_process_map(self._excel)
        if tracking.empty:
            return []
        year_prep = self._get_year_prepared(tracking, map_df, anio=anio)
        df = self._slice_by_mes(year_prep, anio=anio, mes=mes)
        df = apply_ui_filters(
            df,
            unidad=unidad,
            proceso=proceso,
            subproceso=subproceso,
            clasificacion=clasificacion,
            frecuencia=frecuencia,
        )
        latest = latest_per_indicator(df)
        return build_indicadores_procesos_listado(latest)

    def get_procesos_dashboard(
        self,
        *,
        anio: int | None = None,
        mes: int | None = None,
        unidad: str | None = None,
        proceso: str | None = None,
        subproceso: str | None = None,
        clasificacion: str | None = None,
        frecuencia: str | None = None,
    ) -> dict[str, Any]:
        tracking = self._load_tracking()
        map_df = load_process_map(self._excel)
        cmi_catalog = self._cmi.load_cmi_worksheet()
        anios = self._available_anios()
        anio_eff = int(anio) if anio is not None else default_anio_procesos(anios)
        mes_eff = int(mes) if mes is not None else default_mes(tracking, anio_eff)

        empty_payload = {
            "anio": anio_eff,
            "mes": mes_eff,
            "mes_nombre": mes_nombre(mes_eff),
            "anios_disponibles": anios,
            "meses_disponibles": list(range(1, 13)),
            "filtros_aplicados": {
                "unidad": unidad or "Todos",
                "proceso": proceso or "Todos",
                "subproceso": subproceso or "Todos",
                "clasificacion": clasificacion or "Todos",
                "frecuencia": frecuencia or "Todos",
            },
            "total_indicadores": 0,
            "kpis": build_procesos_kpis(pd.DataFrame()),
            "banner": build_banner(pd.DataFrame(), anio=anio_eff, mes=mes_eff, base_year=anio_eff - 1, base_month=None, cumpl_global=None, cumpl_base=None),
            "distribucion_nivel": [],
            "tipo_proceso_cards": [],
            "proceso_bars": [],
            "catalog_charts": {"periodicidad": [], "tipo_indicador": []},
            "procesos_detalle": [],
            "unidades_detalle": [],
            "indicadores_summary": build_indicadores_summary(pd.DataFrame()),
            "indicadores": [],
            "alertas": {"peligro": 0, "alerta": 0, "items": []},
            "variacion": {"mejoraron": [], "empeoraron": [], "top_riesgo_procesos": []},
            "analisis_avanzado": {},
            "calidad": build_calidad_dashboard(pd.DataFrame(), mensaje="Sin datos de tracking."),
            "vista_global": {},
            "ejecucion_variacion": {"positiva": [], "negativa": []},
            "meta": {"base_anio": anio_eff - 1, "base_mes": None, "latest_month_global": mes_eff},
        }

        if tracking.empty:
            return empty_payload

        base_year = anio_eff - 1
        base_mes = get_prev_month_for_year(tracking, base_year) if base_year in anios else None

        year_prep = self._get_year_prepared(tracking, map_df, anio=anio_eff)
        year_prep_base = (
            self._get_year_prepared(tracking, map_df, anio=base_year, omit_kawak_cross=True)
            if base_mes is not None
            else pd.DataFrame()
        )

        df_current = self._slice_by_mes(year_prep, anio=anio_eff, mes=mes_eff)
        df_prev_month = (
            self._slice_by_mes(year_prep, anio=anio_eff, mes=max(1, mes_eff - 1)) if mes_eff > 1 else pd.DataFrame()
        )

        df_base_year = (
            self._slice_by_mes(year_prep_base, anio=base_year, mes=base_mes) if base_mes is not None else pd.DataFrame()
        )

        mes_global = get_prev_month_for_year(tracking, anio_eff) or mes_eff
        df_global = self._slice_by_mes(year_prep, anio=anio_eff, mes=mes_global)

        df_global_base = (
            self._slice_by_mes(year_prep_base, anio=base_year, mes=base_mes) if base_mes is not None else pd.DataFrame()
        )

        vista_global = build_vista_global(
            df_global,
            df_global_base,
            cmi_catalog,
            anio=anio_eff,
            mes_corte=mes_global,
            base_year=base_year,
            base_mes=base_mes,
        )

        meses_hist = sorted(
            tracking[pd.to_numeric(tracking["Anio"], errors="coerce") == anio_eff]["Mes"]
            .apply(lambda m: int(mes_to_num(m) or 0))
            .dropna()
            .astype(int)
            .unique()
            .tolist()
        ) if "Anio" in tracking.columns else list(range(1, 13))

        hist_slices_global: list[pd.DataFrame] = []
        for m in meses_hist:
            sl = self._slice_by_mes(year_prep, anio=anio_eff, mes=int(m))
            if not sl.empty:
                hist_slices_global.append(sl)
        tracking_hist_global = (
            pd.concat(hist_slices_global, ignore_index=True) if hist_slices_global else pd.DataFrame()
        )

        filtered = apply_ui_filters(
            df_current,
            unidad=unidad,
            proceso=proceso,
            subproceso=subproceso,
            clasificacion=clasificacion,
            frecuencia=frecuencia,
        )
        latest = latest_per_indicator(filtered)

        active_ids = set(latest["Id"].astype(str).str.strip().tolist()) if "Id" in latest.columns else set()
        catalog_charts = build_catalog_charts(cmi_catalog, active_ids)

        hist_slices: list[pd.DataFrame] = []
        for m in meses_hist:
            sl = self._slice_by_mes(year_prep, anio=anio_eff, mes=int(m))
            sl = apply_ui_filters(
                sl,
                unidad=unidad,
                proceso=proceso,
                subproceso=subproceso,
                clasificacion=clasificacion,
                frecuencia=frecuencia,
            )
            if not sl.empty:
                hist_slices.append(sl)
        tracking_hist = pd.concat(hist_slices, ignore_index=True) if hist_slices else pd.DataFrame()

        calidad_raw, calidad_msg = load_calidad_data(self._excel)
        calidad_filt = filter_calidad(
            calidad_raw,
            proceso=proceso,
            subproceso=subproceso,
            unidad=unidad,
            map_df=map_df,
        )
        calidad = build_calidad_dashboard(calidad_filt, mensaje=calidad_msg)

        analisis_avanzado = build_analisis_avanzado(
            latest,
            df_prev_month,
            df_base_year,
            tracking_hist_global if not tracking_hist_global.empty else tracking_hist,
            proceso=proceso or "Todos",
            base_anio=base_year,
        )
        latest_global = latest_per_indicator(df_global)
        analisis_avanzado["historico_indicadores"] = build_historico_catalog(
            latest_global,
            tracking_hist_global,
        )

        ejecucion_variacion = build_ejecucion_variacion(
            latest,
            df_prev_month if not df_prev_month.empty else df_base_year,
        )

        return {
            "anio": anio_eff,
            "mes": mes_eff,
            "mes_nombre": mes_nombre(mes_eff),
            "anios_disponibles": anios,
            "meses_disponibles": sorted(
                tracking[tracking["Anio"] == anio_eff]["Mes"].apply(lambda m: int(mes_to_num(m) or 0)).dropna().unique().tolist()
            )
            if "Anio" in tracking.columns and "Mes" in tracking.columns
            else list(range(1, 13)),
            "filtros_aplicados": {
                "unidad": unidad or "Todos",
                "proceso": proceso or "Todos",
                "subproceso": subproceso or "Todos",
                "clasificacion": clasificacion or "Todos",
                "frecuencia": frecuencia or "Todos",
            },
            "total_indicadores": len(latest),
            "kpis": build_procesos_kpis(latest),
            "banner": build_banner(
                latest,
                anio=anio_eff,
                mes=mes_eff,
                base_year=base_year,
                base_month=base_mes,
                cumpl_global=avg_cumplimiento(df_global),
                cumpl_base=avg_cumplimiento(df_base_year),
            ),
            "distribucion_nivel": build_distribucion_nivel(latest),
            "tipo_proceso_cards": build_tipo_proceso_cards(latest, df_base_year),
            "proceso_bars": build_proceso_bars(latest, df_base_year),
            "catalog_charts": catalog_charts,
            "procesos_detalle": build_procesos_detalle(latest),
            "unidades_detalle": build_unidades_detalle(latest),
            "indicadores_summary": build_indicadores_summary(latest),
            "indicadores": build_indicadores_procesos_listado(latest),
            "alertas": build_alertas(latest),
            "variacion": build_variacion_analisis(latest, df_prev_month if not df_prev_month.empty else df_base_year),
            "analisis_avanzado": analisis_avanzado,
            "calidad": calidad,
            "vista_global": vista_global,
            "ejecucion_variacion": ejecucion_variacion,
            "meta": {
                "base_anio": base_year,
                "base_mes": base_mes,
                "latest_month_global": get_prev_month_for_year(tracking, anio_eff) or mes_eff,
            },
        }

    def _ultimo_filtrado_procesos(self, *, anio: int | None = None) -> pd.DataFrame:
        tracking = self._load_tracking()
        map_df = load_process_map(self._excel)
        if tracking.empty:
            return pd.DataFrame()
        anio_eff = int(anio) if anio is not None else default_anio_procesos(self._available_anios())
        mes_eff = default_mes(tracking, anio_eff)
        return self._prepare_procesos_slice(tracking, map_df, anio=anio_eff, mes=mes_eff)

    def get_procesos_indicador_ficha(
        self,
        indicador_id: str,
        *,
        anio: int,
        mes: int | None = None,
        unidad: str | None = None,
        proceso: str | None = None,
        subproceso: str | None = None,
    ) -> dict[str, Any] | None:
        tracking = self._load_tracking()
        map_df = load_process_map(self._excel)
        mes_eff = int(mes) if mes is not None else default_mes(tracking, int(anio))
        df = self._prepare_procesos_slice(tracking, map_df, anio=int(anio), mes=mes_eff)
        df = apply_ui_filters(df, unidad=unidad, proceso=proceso, subproceso=subproceso)
        if df.empty or "Id" not in df.columns:
            return None
        match = df[df["Id"].astype(str) == str(indicador_id)]
        if match.empty:
            return None
        row = match.iloc[0]

        historico: list[dict[str, Any]] = []
        for m in range(1, 13):
            sl = self._prepare_procesos_slice(tracking, map_df, anio=int(anio), mes=m)
            if sl.empty or "Id" not in sl.columns:
                continue
            ind_sl = sl[sl["Id"].astype(str) == str(indicador_id)]
            if not ind_sl.empty:
                r = ind_sl.iloc[0]
                historico.append(
                    {
                        "periodo": f"{anio}-{str(m).zfill(2)}",
                        "meta": r.get("Meta"),
                        "ejecucion": r.get("Ejecucion"),
                        "cumplimiento": r.get("cumplimiento_pct"),
                    }
                )

        record = df_to_records(match)[0]
        record["historico"] = historico
        proc_name = str(row.get("Proceso_padre", row.get("Proceso", "")))
        tipo = str(row.get("Tipo de proceso", ""))
        record["proceso_padre"] = proc_name
        record["subproceso_final"] = str(row.get("Subproceso_final", row.get("Subproceso", "")))
        record["unidad"] = str(row.get("Unidad", ""))
        record["tipo_proceso"] = tipo
        record["tipo_proceso_color"] = TIPO_PROCESO_COLORS.get(tipo.upper() if tipo else "", "#1A3A5C")
        cump = row.get("cumplimiento_pct")
        try:
            cump_f = float(cump) if cump is not None else None
        except (TypeError, ValueError):
            cump_f = None
        record["narrativa_ia"] = generar_narrativa_ficha(
            nombre=str(row.get("Indicador", "")),
            meta=row.get("Meta"),
            ejecucion=row.get("Ejecucion"),
            nivel=str(row.get("Nivel de cumplimiento", "")),
            cumplimiento=cump_f,
            proceso=proc_name,
        )
        tendencia = "Estable"
        if len(historico) >= 2:
            vals = [h["cumplimiento"] for h in historico if h.get("cumplimiento") is not None]
            if len(vals) >= 2:
                delta = float(vals[-1]) - float(vals[-2])
                if delta > 2:
                    tendencia = "Al alza"
                elif delta < -2:
                    tendencia = "A la baja"
        record["tendencia"] = tendencia
        return record

    def export_procesos_indicadores(
        self,
        *,
        anio: int,
        mes: int | None = None,
        formato: str = "xlsx",
        unidad: str | None = None,
        proceso: str | None = None,
        subproceso: str | None = None,
        clasificacion: str | None = None,
        frecuencia: str | None = None,
    ) -> tuple[bytes, str, str]:
        tracking = self._load_tracking()
        map_df = load_process_map(self._excel)
        mes_eff = int(mes) if mes is not None else default_mes(tracking, int(anio))
        df = self._prepare_procesos_slice(tracking, map_df, anio=int(anio), mes=mes_eff)
        df = apply_ui_filters(
            df,
            unidad=unidad,
            proceso=proceso,
            subproceso=subproceso,
            clasificacion=clasificacion,
            frecuencia=frecuencia,
        )
        latest = latest_per_indicator(df)
        if formato.lower() == "csv":
            export_df = build_export_dataframe(latest)
            content = export_df.to_csv(index=False).encode("utf-8-sig")
            filename = f"cmi_procesos_{anio}_{mes_eff}.csv"
            media = "text/csv; charset=utf-8"
            return content, filename, media
        content = build_export_excel_bytes(latest)
        filename = f"cmi_procesos_{anio}_{mes_eff}.xlsx"
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return content, filename, media

    def get_estrategico(self, *, anio: int | None = None, mes: int | None = None, corte: str | None = None) -> dict[str, Any]:
        anios = self._available_anios()
        anio_eff = int(anio) if anio is not None else default_anio(anios)
        mes_eff = self._resolve_mes(mes, corte)
        df = self._prepare_df(anio=anio_eff, mes=mes_eff)
        if df.empty or "Linea" not in df.columns:
            return {"anio": anio_eff, "mes": mes_eff, "lineas": [], "total_indicadores": 0}

        lineas = []
        for linea, group in df.groupby("Linea", dropna=True):
            if not linea or str(linea).strip() in ("", "nan"):
                continue
            cumpl = group["cumplimiento_pct"].dropna() if "cumplimiento_pct" in group else pd.Series(dtype=float)
            promedio = round(float(cumpl.mean()), 1) if len(cumpl) else None
            riesgo = 0
            if "Nivel de cumplimiento" in group.columns:
                riesgo = int(group["Nivel de cumplimiento"].isin(["Peligro", "Alerta"]).sum())
            lineas.append(
                {
                    "linea": str(linea),
                    "total_indicadores": len(group),
                    "cumplimiento_promedio": promedio,
                    "en_riesgo": riesgo,
                }
            )
        lineas.sort(key=lambda x: linea_sort_key(x.get("linea", "")))
        return {
            "anio": anio_eff,
            "mes": mes_eff,
            "total_indicadores": len(df),
            "lineas": lineas,
        }

    def get_procesos(self, *, anio: int | None = None) -> dict[str, Any]:
        df = self._ultimo_filtrado_procesos(anio=anio)
        col = "Proceso_padre" if "Proceso_padre" in df.columns else "Proceso"
        if df.empty or col not in df.columns:
            return {"anio": anio, "procesos": [], "total_indicadores": 0}

        procesos = []
        for proceso, group in df.groupby(col, dropna=True):
            if not proceso or str(proceso).strip() in ("", "nan"):
                continue
            cumpl = group["cumplimiento_pct"].dropna() if "cumplimiento_pct" in group.columns else pd.Series(dtype=float)
            promedio = round(float(cumpl.mean()), 1) if len(cumpl) else None
            conteo_cat: dict[str, int] = {}
            if "Nivel de cumplimiento" in group.columns:
                for cat in ("Peligro", "Alerta", "Cumplimiento", "Sobrecumplimiento"):
                    conteo_cat[cat] = int((group["Nivel de cumplimiento"] == cat).sum())
            procesos.append(
                {
                    "proceso": str(proceso),
                    "total_indicadores": len(group),
                    "cumplimiento_promedio": promedio,
                    "categorias": conteo_cat,
                }
            )
        procesos.sort(key=lambda x: x["cumplimiento_promedio"] or 0)
        return {"anio": anio, "total_indicadores": len(df), "procesos": procesos}

    def get_alertas(
        self,
        *,
        anio: int | None = None,
        mes: int | None = None,
        corte: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        anios = self._available_anios()
        anio_eff = int(anio) if anio is not None else default_anio(anios)
        mes_eff = self._resolve_mes(mes, corte)
        df = self._prepare_df(anio=anio_eff, mes=mes_eff)
        alertas = build_alertas(df)
        items = alertas["items"][:limit]
        return {
            "anio": anio_eff,
            "mes": mes_eff,
            "total": len(alertas["items"]),
            "peligro": alertas["peligro"],
            "alerta": alertas["alerta"],
            "alertas": items,
        }
