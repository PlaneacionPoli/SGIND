"""Lógica de Resumen General alineada con streamlit_app/pages/resumen_general.py."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.domain.calculos import aplicar_calculos_cumplimiento, calcular_kpis, obtener_ultimo_registro
from app.domain.cmi_filters import CMIFilterService
from app.domain.linea_order import linea_sort_key
from app.domain.resumen_builders import (
    build_linea_summary,
    build_linea_summary_retos,
    build_proyectos_gantt,
    build_proyectos_tabla,
    build_retos_tabla,
    build_strategy_cards,
    build_sunburst_plotly,
    compute_trends,
    ensure_nivel_cumplimiento,
    generate_narrative_consolidado,
    generate_narrative_indicadores,
    generate_narrative_proyectos,
    generate_narrative_retos,
    get_chip_config_consolidado,
    get_chip_config_indicadores,
    get_chip_config_proyectos,
    get_chip_config_retos,
    merge_consolidado_summaries,
)
from app.domain.strategic_processors import StrategicProcessors
from app.services.etl_pipeline import ETLPipelineService
from app.services.excel_reader import ExcelReaderService
from app.services.retos_loaders import RetosLoaders

VISTAS = ("consolidado", "retos", "proyectos", "indicadores")

_LINE_COLORS = {
    "Talento Humano": "#E63946",
    "Investigación": "#1D3557",
    "Extensión": "#2A9D8F",
    "Internacionalización": "#E9C46A",
    "Bienestar": "#F4A261",
    "Gestión": "#6B728E",
}


class ResumenService:
    def __init__(self, excel: ExcelReaderService) -> None:
        self._excel = excel
        self._etl = ETLPipelineService(excel)
        self._cmi = CMIFilterService(excel)
        self._strategic = StrategicProcessors(excel)
        self._retos = RetosLoaders(excel)

    def _load_cierres(self) -> pd.DataFrame:
        return self._etl.leer_cierres()

    def _anio_column(self, df: pd.DataFrame) -> str | None:
        for col in ("Anio", "Año", "anio"):
            if col in df.columns:
                return col
        return None

    def _filter_period(self, df: pd.DataFrame, anio: int | None, periodo: str | None) -> pd.DataFrame:
        out = df
        anio_col = self._anio_column(out)
        if anio is not None and anio_col:
            out = out[out[anio_col] == anio]
        if periodo is not None:
            for col in ("Periodo", "periodo", "Mes"):
                if col in out.columns:
                    out = out[out[col].astype(str) == str(periodo)]
                    break
        return out

    def _apply_vista(self, df: pd.DataFrame, vista: str) -> pd.DataFrame:
        vista_norm = (vista or "indicadores").strip().lower()
        if vista_norm == "indicadores":
            return self._cmi.filter_estrategico(df)
        if vista_norm == "proyectos":
            return self._cmi.filter_proyectos(df)
        if vista_norm == "consolidado":
            return df
        return df

    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        return obtener_ultimo_registro(aplicar_calculos_cumplimiento(df))

    def _ensure_cumplimiento_pct(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        if "cumplimiento_pct" not in out.columns:
            if "Cumplimiento_norm" in out.columns:
                out["cumplimiento_pct"] = out["Cumplimiento_norm"] * 100
            elif "Cumplimiento" in out.columns:
                out["cumplimiento_pct"] = pd.to_numeric(out["Cumplimiento"], errors="coerce")
            elif "Meta" in out.columns and "Ejecucion" in out.columns:
                out["cumplimiento_pct"] = out.apply(
                    lambda r: (r["Ejecucion"] / r["Meta"] * 100)
                    if pd.notna(r.get("Meta")) and r["Meta"] != 0
                    else None,
                    axis=1,
                )
        return out

    def load_retos(self, anio: int) -> pd.DataFrame:
        path = self._excel.data_root / "raw" / "Retos" / "Plan de retos.xlsx"
        if not path.exists():
            return pd.DataFrame()
        try:
            obj_df = self._excel.read_excel("raw/Retos/Plan de retos.xlsx", sheet_name="Objetivo")
            obj_df.columns = [str(c).strip() for c in obj_df.columns]
            if "Año" in obj_df.columns:
                obj_df = obj_df[obj_df["Año"] == anio]
            if "Línea Estratégica" in obj_df.columns:
                obj_df = obj_df.rename(columns={"Línea Estratégica": "Linea"})
            if "Cumplimiento" in obj_df.columns:
                obj_df = obj_df.rename(columns={"Cumplimiento": "cumplimiento_pct"})
                obj_df["cumplimiento_pct"] = pd.to_numeric(obj_df["cumplimiento_pct"], errors="coerce") * 100
            return obj_df
        except Exception:
            return pd.DataFrame()

    def get_dataset(
        self,
        *,
        anio: int | None = None,
        periodo: str | None = None,
        vista: str = "indicadores",
    ) -> pd.DataFrame:
        try:
            df = self._load_cierres()
        except FileNotFoundError:
            return pd.DataFrame()

        df = self._filter_period(df, anio, periodo)
        vista_norm = (vista or "indicadores").strip().lower()

        if vista_norm == "retos" and anio is not None:
            retos = self.load_retos(anio)
            if not retos.empty:
                return self._ensure_cumplimiento_pct(retos)
            return pd.DataFrame()

        df = self._apply_vista(df, vista_norm)
        return self._prepare(df)

    def get_filtros(self) -> dict:
        try:
            df = self._load_cierres()
        except FileNotFoundError:
            return {"anios": [], "periodos": [], "anio_default": None, "vistas": list(VISTAS)}

        anio_col = self._anio_column(df)
        anios = (
            sorted(int(x) for x in pd.to_numeric(df[anio_col], errors="coerce").dropna().unique())
            if anio_col
            else []
        )
        allowed = [y for y in anios if y in {2022, 2023, 2024, 2025, 2026}]
        anios_out = allowed or anios
        periodos: list[str] = []
        for col in ("Mes", "Periodo"):
            if col in df.columns:
                periodos = sorted(df[col].dropna().astype(str).unique().tolist())
                break
        return {
            "anios": anios_out,
            "periodos": periodos,
            "anio_default": anios_out[-1] if anios_out else None,
            "vistas": list(VISTAS),
        }

    def get_kpis(self, *, anio: int | None = None, periodo: str | None = None, vista: str = "indicadores") -> list[dict]:
        df_ultimo = self.get_dataset(anio=anio, periodo=periodo, vista=vista)
        total, conteos = calcular_kpis(df_ultimo)

        if total == 0:
            return [
                {"label": "Indicadores evaluados", "value": 0, "unit": "ind"},
                {"label": "Cumplimiento global", "value": "Sin datos", "unit": ""},
                {"label": "En Peligro", "value": "—", "unit": "ind"},
                {"label": "En Alerta", "value": "—", "unit": "ind"},
                {"label": "Sobrecumplimiento", "value": "—", "unit": "ind"},
                {"label": "En Cumplimiento", "value": "—", "unit": "ind"},
            ]

        peligro = conteos.get("Peligro", {"n": 0, "pct": 0})
        alerta = conteos.get("Alerta", {"n": 0, "pct": 0})
        cumple = conteos.get("Cumplimiento", {"n": 0, "pct": 0})
        sobre = conteos.get("Sobrecumplimiento", {"n": 0, "pct": 0})
        cumplimiento_global = round(float(df_ultimo["Cumplimiento_norm"].mean()) * 100, 1)

        return [
            {"label": "Indicadores evaluados", "value": total, "unit": "ind"},
            {"label": "Cumplimiento global", "value": cumplimiento_global, "unit": "%"},
            {"label": "En Peligro", "value": peligro["n"], "unit": "ind", "trend": f"{peligro['pct']}%"},
            {"label": "En Alerta", "value": alerta["n"], "unit": "ind", "trend": f"{alerta['pct']}%"},
            {"label": "Sobrecumplimiento", "value": sobre["n"], "unit": "ind", "trend": f"{sobre['pct']}%"},
            {"label": "En Cumplimiento", "value": cumple["n"], "unit": "ind", "trend": f"{cumple['pct']}%"},
        ]

    def get_lineas(self, *, anio: int | None = None, periodo: str | None = None, vista: str = "indicadores") -> list[dict]:
        df_ultimo = self._ensure_cumplimiento_pct(self.get_dataset(anio=anio, periodo=periodo, vista=vista))
        if "Linea" not in df_ultimo.columns:
            return []

        lineas = []
        for linea, group in df_ultimo.groupby("Linea", dropna=True):
            nombre = str(linea).strip()
            if not nombre or nombre.lower() == "nan":
                continue
            con_datos = group[group["Cumplimiento_norm"].notna()] if "Cumplimiento_norm" in group else group
            promedio = (
                round(float(con_datos["Cumplimiento_norm"].mean()) * 100, 1)
                if len(con_datos) and "Cumplimiento_norm" in con_datos
                else (
                    round(float(group["cumplimiento_pct"].mean()), 1)
                    if "cumplimiento_pct" in group and group["cumplimiento_pct"].notna().any()
                    else None
                )
            )
            riesgo = int((group["Categoria"].isin(["Peligro", "Alerta"])).sum()) if "Categoria" in group else 0
            lineas.append(
                {
                    "linea": nombre,
                    "total_indicadores": len(group),
                    "cumplimiento_promedio": promedio,
                    "en_riesgo": riesgo,
                }
            )
        lineas.sort(key=lambda x: linea_sort_key(x.get("linea", "")))
        return lineas

    def get_semaphore(self, *, anio: int | None = None, periodo: str | None = None, vista: str = "indicadores") -> list[dict]:
        df_ultimo = self.get_dataset(anio=anio, periodo=periodo, vista=vista)
        total, conteos = calcular_kpis(df_ultimo)
        if total == 0:
            return []
        return [{"categoria": cat, "count": data["n"], "percent": data["pct"]} for cat, data in conteos.items()]

    def get_trend(self, *, anio: int | None = None, vista: str = "indicadores") -> list[dict]:
        try:
            df = self._load_cierres()
        except FileNotFoundError:
            return []
        if anio is not None:
            df = self._filter_period(df, anio, None)
        vista_norm = (vista or "indicadores").strip().lower()
        if vista_norm == "retos" and anio is not None:
            retos = self.load_retos(anio)
            if retos.empty:
                return []
            avg = retos["cumplimiento_pct"].mean() if "cumplimiento_pct" in retos else None
            return [{"periodo": str(anio), "cumplimiento": round(float(avg), 1) if pd.notna(avg) else None}]
        df = self._apply_vista(df, vista_norm)
        if df.empty:
            return []
        df = aplicar_calculos_cumplimiento(df)
        period_col = next((c for c in ("Mes", "Periodo") if c in df.columns), None)
        if not period_col or "Cumplimiento_norm" not in df.columns:
            return []
        trend = df.groupby(period_col)["Cumplimiento_norm"].mean().reset_index()
        return [
            {
                "periodo": str(row[period_col]),
                "cumplimiento": round(float(row["Cumplimiento_norm"]) * 100, 1)
                if pd.notna(row["Cumplimiento_norm"])
                else None,
            }
            for _, row in trend.iterrows()
        ]

    def get_sunburst(self, *, anio: int | None = None, vista: str = "indicadores") -> list[dict]:
        df = self._ensure_cumplimiento_pct(self.get_dataset(anio=anio, vista=vista))
        if df.empty or "Linea" not in df.columns:
            return [{"id": "sin_datos", "label": "Sin datos", "parent": "", "value": 1, "color": "#6B728E"}]

        if "Objetivo" not in df.columns:
            grouped = (
                df.groupby("Linea")["cumplimiento_pct"]
                .mean()
                .reset_index()
                .rename(columns={"cumplimiento_pct": "promedio"})
            )
            nodes = [{"id": "root", "label": "PDI", "parent": "", "value": 0, "color": "#1D3557"}]
            for _, row in grouped.iterrows():
                linea = str(row["Linea"]).strip()
                if not linea:
                    continue
                nodes.append(
                    {
                        "id": linea,
                        "label": linea,
                        "parent": "root",
                        "value": round(float(row["promedio"]), 1) if pd.notna(row["promedio"]) else 0,
                        "color": _LINE_COLORS.get(linea, "#457B9D"),
                    }
                )
            return nodes

        obj = (
            df[df["Linea"].notna() & df["Objetivo"].notna()]
            .groupby(["Linea", "Objetivo"])["cumplimiento_pct"]
            .mean()
            .reset_index()
        )
        nodes: list[dict[str, Any]] = [{"id": "root", "label": "PDI", "parent": "", "value": 0, "color": "#1D3557"}]
        for linea in obj["Linea"].unique():
            linea_str = str(linea).strip()
            if not linea_str:
                continue
            sub = obj[obj["Linea"] == linea]
            linea_avg = sub["cumplimiento_pct"].mean()
            nodes.append(
                {
                    "id": linea_str,
                    "label": linea_str,
                    "parent": "root",
                    "value": round(float(linea_avg), 1) if pd.notna(linea_avg) else 0,
                    "color": _LINE_COLORS.get(linea_str, "#457B9D"),
                }
            )
            for _, row in sub.iterrows():
                obj_name = str(row["Objetivo"]).strip()
                if not obj_name:
                    continue
                node_id = f"{linea_str}::{obj_name}"
                nodes.append(
                    {
                        "id": node_id,
                        "label": obj_name,
                        "parent": linea_str,
                        "value": round(float(row["cumplimiento_pct"]), 1) if pd.notna(row["cumplimiento_pct"]) else 0,
                        "color": _LINE_COLORS.get(linea_str, "#457B9D"),
                    }
                )
        return nodes

    def get_yoy(self, *, anio: int, vista: str = "indicadores") -> list[dict]:
        actual = self.get_lineas(anio=anio, vista=vista)
        prev = self.get_lineas(anio=anio - 1, vista=vista)
        prev_map = {item["linea"]: item["cumplimiento_promedio"] for item in prev}
        rows = []
        for item in actual:
            prev_val = prev_map.get(item["linea"])
            curr = item["cumplimiento_promedio"]
            variacion = round(curr - prev_val, 1) if curr is not None and prev_val is not None else None
            rows.append(
                {
                    "linea": item["linea"],
                    "anio_actual": anio,
                    "cumplimiento_actual": curr,
                    "cumplimiento_anterior": prev_val,
                    "variacion_pp": variacion,
                    "en_riesgo": item["en_riesgo"],
                }
            )
        return rows

    def get_narrativa(self, *, anio: int | None = None, vista: str = "indicadores") -> dict:
        df = self.get_dataset(anio=anio, vista=vista)
        total, conteos = calcular_kpis(df)
        if total == 0:
            return {"titulo": "Sin datos", "parrafos": ["No hay indicadores evaluables para el periodo seleccionado."]}

        cumpl_global = round(float(df["Cumplimiento_norm"].mean()) * 100, 1)
        peligro = conteos.get("Peligro", {}).get("n", 0)
        alerta = conteos.get("Alerta", {}).get("n", 0)
        lineas = self.get_lineas(anio=anio, vista=vista)
        mejor = max(lineas, key=lambda x: x["cumplimiento_promedio"] or 0) if lineas else None
        peor = min(lineas, key=lambda x: x["cumplimiento_promedio"] or 100) if lineas else None

        parrafos = [
            f"En {anio or 'el periodo seleccionado'}, se evaluaron {total} indicadores con un cumplimiento global de {cumpl_global}%.",
            f"El semáforo registra {peligro} indicadores en Peligro y {alerta} en Alerta.",
        ]
        if mejor and mejor.get("cumplimiento_promedio") is not None:
            parrafos.append(
                f"La línea con mejor desempeño es {mejor['linea']} ({mejor['cumplimiento_promedio']}%)."
            )
        if peor and peor.get("cumplimiento_promedio") is not None:
            parrafos.append(
                f"La línea que requiere mayor atención es {peor['linea']} ({peor['cumplimiento_promedio']}%)."
            )
        return {
            "titulo": f"Narrativa ejecutiva — {vista.capitalize()} {anio or ''}".strip(),
            "parrafos": parrafos,
        }

    def get_resumen_completo(self, *, anio: int, vista: str = "indicadores", rango: bool = False) -> dict[str, Any]:
        """Payload unificado alineado con streamlit resumen_general.py."""
        vista_norm = (vista or "indicadores").strip().lower()
        meses = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}

        if vista_norm == "indicadores":
            pdi_df = ensure_nivel_cumplimiento(self._strategic.preparar_pdi_con_cierre(anio, 12))
            chips = get_chip_config_indicadores(pdi_df)
            linea_summary = build_linea_summary(pdi_df, unique_count_col="Id")
            historico_df = self._strategic.load_historico_por_linea()
            cards = build_strategy_cards(linea_summary, historico_df, vista=vista_norm)
            objetivo_cols = [c for c in ["Linea", "Objetivo", "cumplimiento_pct"] if c in pdi_df.columns]
            objetivo_df = pdi_df[objetivo_cols].copy() if objetivo_cols else pd.DataFrame()
            sunburst = build_sunburst_plotly(objetivo_df)
            narrativa = generate_narrative_indicadores(pdi_df, linea_summary, chips)

            prev_month = self._strategic.latest_month_for_year(anio - 1)
            best, worst = [], []
            periodo_txt = f"Solo datos de {anio} — sin período anterior disponible"
            if prev_month:
                prev_df = ensure_nivel_cumplimiento(
                    self._strategic.preparar_pdi_con_cierre(anio - 1, prev_month)
                )
                best, worst = compute_trends(pdi_df, prev_df)
                periodo_txt = (
                    f"Comparando {anio} (cierre anual) vs {anio - 1} ({meses.get(prev_month, prev_month)})"
                )

            return {
                "anio": anio,
                "vista": vista_norm,
                "chips": chips,
                "fichas": cards,
                "sunburst": sunburst,
                "narrativa": narrativa,
                "mejoraron": best,
                "en_riesgo": worst,
                "periodo_comparacion": periodo_txt,
                "total_indicadores": chips[0]["value"] if chips else 0,
            }

        if vista_norm == "proyectos":
            proy_all = self._strategic.load_proyectos()
            proy_df = ensure_nivel_cumplimiento(self._strategic.preparar_proyectos_con_cierre(anio, 12))
            chips = get_chip_config_proyectos(proy_df)
            linea_summary = build_linea_summary(proy_df, unique_count_col="Id", count_col_name="N_Proyectos")
            historico_df = proy_df
            cards = build_strategy_cards(linea_summary, historico_df, vista=vista_norm)
            objetivo_cols = [c for c in ["Linea", "Objetivo", "cumplimiento_pct"] if c in proy_df.columns]
            objetivo_df = proy_df[objetivo_cols].copy() if objetivo_cols else pd.DataFrame()
            sunburst = build_sunburst_plotly(objetivo_df)
            narrativa = generate_narrative_proyectos(proy_df, linea_summary)
            gantt = build_proyectos_gantt(proy_all)

            return {
                "anio": anio,
                "vista": vista_norm,
                "chips": chips,
                "fichas": cards,
                "sunburst": sunburst,
                "narrativa": narrativa,
                "mejoraron": [],
                "en_riesgo": [],
                "periodo_comparacion": "",
                "gantt_proyectos": gantt,
                "total_indicadores": chips[0]["value"] if chips else 0,
                "tabla_detalle": build_proyectos_tabla(proy_df),
            }

        if vista_norm == "retos":
            linea_df, obj_df = self._retos.load_retos_data(anio)
            planes_df = self._retos.load_planes(anio)
            area_count = self._retos.load_area_count(anio)
            linea_summary = build_linea_summary_retos(linea_df, obj_df, planes_df)
            chips = get_chip_config_retos(linea_summary, area_count)
            cards = build_strategy_cards(linea_summary, linea_df, vista=vista_norm)
            sunburst = build_sunburst_plotly(obj_df if not obj_df.empty else linea_df)
            narrativa = generate_narrative_retos(linea_summary)

            return {
                "anio": anio,
                "vista": vista_norm,
                "chips": chips,
                "fichas": cards,
                "sunburst": sunburst,
                "narrativa": narrativa,
                "mejoraron": [],
                "en_riesgo": [],
                "periodo_comparacion": "",
                "total_indicadores": chips[0]["value"] if chips else 0,
                "tabla_detalle": build_retos_tabla(linea_df),
            }

        if vista_norm == "consolidado":
            if rango:
                anios_rango = [2022, 2023, 2024, 2025]
                pdi_parts = [
                    ensure_nivel_cumplimiento(self._strategic.preparar_pdi_con_cierre(y, 12)) for y in anios_rango
                ]
                pdi_parts = [p for p in pdi_parts if p is not None and not p.empty]
                pdi_df = pd.concat(pdi_parts, ignore_index=True) if pdi_parts else pd.DataFrame()
                if not pdi_df.empty and "Id" in pdi_df.columns:
                    pdi_df = pdi_df.drop_duplicates(subset=["Id"], keep="last")

                proy_parts = [
                    ensure_nivel_cumplimiento(self._strategic.preparar_proyectos_con_cierre(y, 12)) for y in anios_rango
                ]
                proy_parts = [p for p in proy_parts if p is not None and not p.empty]
                proy_df = pd.concat(proy_parts, ignore_index=True) if proy_parts else pd.DataFrame()
                if not proy_df.empty and "Id" in proy_df.columns:
                    proy_df = proy_df.drop_duplicates(subset=["Id"], keep="last")

                ret_linea_parts, ret_obj_parts, ret_planes_parts = [], [], []
                for y in anios_rango:
                    ld, od = self._retos.load_retos_data(y)
                    if ld is not None and not ld.empty:
                        ret_linea_parts.append(ld)
                    if od is not None and not od.empty:
                        ret_obj_parts.append(od)
                    pl = self._retos.load_planes(y)
                    if pl is not None and not pl.empty:
                        ret_planes_parts.append(pl)
                ret_linea_df = pd.concat(ret_linea_parts, ignore_index=True) if ret_linea_parts else pd.DataFrame()
                ret_obj_df = pd.concat(ret_obj_parts, ignore_index=True) if ret_obj_parts else pd.DataFrame()
                ret_planes_df = pd.concat(ret_planes_parts, ignore_index=True) if ret_planes_parts else pd.DataFrame()
            else:
                pdi_df = ensure_nivel_cumplimiento(self._strategic.preparar_pdi_con_cierre(anio, 12))
                proy_df = ensure_nivel_cumplimiento(self._strategic.preparar_proyectos_con_cierre(anio, 12))
                ret_linea_df, ret_obj_df = self._retos.load_retos_data(anio)
                ret_planes_df = self._retos.load_planes(anio)

            s1 = build_linea_summary(pdi_df, unique_count_col="Id", count_col_name="N_Indicadores")
            s2 = build_linea_summary(proy_df, unique_count_col="Id", count_col_name="N_Proyectos")
            s3 = build_linea_summary_retos(ret_linea_df, ret_obj_df, ret_planes_df)

            o1_cols = [c for c in ["Linea", "Objetivo", "cumplimiento_pct"] if c in pdi_df.columns]
            o2_cols = [c for c in ["Linea", "Objetivo", "cumplimiento_pct"] if c in proy_df.columns]
            o1 = pdi_df[o1_cols].copy() if o1_cols else pd.DataFrame()
            o2 = proy_df[o2_cols].copy() if o2_cols else pd.DataFrame()
            o3 = ret_obj_df if not ret_obj_df.empty else ret_linea_df

            linea_summary, objetivo_df = merge_consolidado_summaries(s1, s2, s3, o1, o2, o3)

            ind_count = int(pdi_df["Id"].nunique()) if not pdi_df.empty and "Id" in pdi_df.columns else 0
            proy_count = int(proy_df["Id"].nunique()) if not proy_df.empty and "Id" in proy_df.columns else 0
            retos_count = int(linea_summary["N_Retos"].sum()) if not linea_summary.empty and "N_Retos" in linea_summary.columns else 0

            chips = get_chip_config_consolidado(linea_summary, ind_count, proy_count, retos_count)
            cards = build_strategy_cards(linea_summary, None, vista=vista_norm)
            sunburst = build_sunburst_plotly(objetivo_df)
            narrativa = generate_narrative_consolidado(
                linea_summary,
                ind_count=ind_count,
                proy_count=proy_count,
                retos_count=retos_count,
                anio=anio,
            )

            return {
                "anio": anio,
                "vista": vista_norm,
                "chips": chips,
                "fichas": cards,
                "sunburst": sunburst,
                "narrativa": narrativa,
                "mejoraron": [],
                "en_riesgo": [],
                "periodo_comparacion": "",
                "total_indicadores": ind_count + proy_count + retos_count,
            }

        return {
            "anio": anio,
            "vista": vista_norm,
            "chips": get_chip_config_indicadores(pd.DataFrame()),
            "fichas": build_strategy_cards(pd.DataFrame(), None, vista=vista_norm),
            "sunburst": build_sunburst_plotly(pd.DataFrame()),
            "narrativa": {"texto": "Vista en construcción.", "estado_color": "#6B728E", "estado_icon": "info", "health_rate": 0},
            "mejoraron": [],
            "en_riesgo": [],
            "periodo_comparacion": "",
            "total_indicadores": 0,
        }
