"""Lógica de Resumen General alineada con streamlit_app/pages/resumen_general.py."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from app.core.ttl_cache import cache_get
from app.domain.calculos import (
    aplicar_calculos_cumplimiento,
    calcular_kpis,
    obtener_ultimo_registro,
)
from app.domain.cmi_filters import CMIFilterService
from app.domain.linea_order import linea_sort_key
from app.domain.resumen_builders import (
    STRATEGIC_LINE_DEFS,
    build_informe_ejecutivo_lineas,
    build_linea_summary,
    build_linea_summary_retos,
    build_pdi_mindmap,
    build_proyectos_gantt,
    build_proyectos_pmo_gantt,
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
    norm_key,
)
from app.domain.strategic_processors import StrategicProcessors
from app.services.etl_pipeline import ETLPipelineService
from app.services.excel_reader import ExcelReaderService
from app.services.narrativa_estrategica_service import (
    TARJETAS_CONSOLIDADO,
    leer_narrativa_estrategica,
)
from app.services.proyectos_pmo_loader import ProyectosPmoLoader
from app.services.retos_loaders import RetosLoaders

_RESUMEN_COMPLETO_CACHE: dict[tuple, tuple[float, dict]] = {}

VISTAS = ("consolidado", "retos", "proyectos", "indicadores")

# Rango fijo usado por el Streamlit original para "Cierre PDI 2022-2025"
# (usar_consolidado_rango) — aplica por igual a todas las vistas, no solo Consolidado.
ANIOS_RANGO = [2022, 2023, 2024, 2025]

# El catálogo de indicadores se amplió (2026-07) con PRY-45..PRY-54 para el
# siguiente ciclo; esos proyectos aún no tienen cierres registrados. El total
# vigente del ciclo PDI 2022-2025 es 44 (PRY-1..PRY-44) — ver
# legacy-reference/ (Indicadores por CMI.bak_pre_pry45_54.xlsx).
PROYECTOS_CICLO_2022_2025_MAX = 44
_PROYECTO_NUM_RE = re.compile(r"PRY-(\d+)", re.IGNORECASE)

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
        self._proyectos_pmo = ProyectosPmoLoader(excel)

    def _load_cierres(self) -> pd.DataFrame:
        return self._etl.leer_cierres()

    def _proyectos_multi_anio(self, anios: list[int]) -> pd.DataFrame:
        parts = [
            ensure_nivel_cumplimiento(
                self._strategic.preparar_proyectos_con_cierre(y, 12), regimen="plan_anual"
            )
            for y in anios
        ]
        parts = [p for p in parts if p is not None and not p.empty]
        df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
        if not df.empty and "Id" in df.columns:
            df = df.drop_duplicates(subset=["Id"], keep="last")
        return df

    def _retos_multi_anio(
        self, anios: list[int]
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        linea_parts, obj_parts, planes_parts = [], [], []
        for y in anios:
            ld, od = self._retos.load_retos_data(y)
            if ld is not None and not ld.empty:
                linea_parts.append(ld)
            if od is not None and not od.empty:
                obj_parts.append(od)
            pl = self._retos.load_planes(y)
            if pl is not None and not pl.empty:
                planes_parts.append(pl)
        linea_df = pd.concat(linea_parts, ignore_index=True) if linea_parts else pd.DataFrame()
        obj_df = pd.concat(obj_parts, ignore_index=True) if obj_parts else pd.DataFrame()
        planes_df = pd.concat(planes_parts, ignore_index=True) if planes_parts else pd.DataFrame()
        return linea_df, obj_df, planes_df

    def _count_proyectos_ciclo_vigente(self) -> int:
        """Total de proyectos declarados en el ciclo PDI 2022-2025 (44), sin
        depender de si ya tienen cierres cargados (ver PROYECTOS_CICLO_2022_2025_MAX)."""
        ids = self._cmi.get_proyectos_ids()
        total = 0
        for pid in ids:
            match = _PROYECTO_NUM_RE.search(str(pid))
            if match and int(match.group(1)) <= PROYECTOS_CICLO_2022_2025_MAX:
                total += 1
        return total

    def _anio_column(self, df: pd.DataFrame) -> str | None:
        for col in ("Anio", "Año", "anio"):
            if col in df.columns:
                return col
        return None

    def _filter_period(
        self, df: pd.DataFrame, anio: int | None, periodo: str | None
    ) -> pd.DataFrame:
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
                    lambda r: (
                        (r["Ejecucion"] / r["Meta"] * 100)
                        if pd.notna(r.get("Meta")) and r["Meta"] != 0
                        else None
                    ),
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
                obj_df["cumplimiento_pct"] = (
                    pd.to_numeric(obj_df["cumplimiento_pct"], errors="coerce") * 100
                )
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
        allowed = [y for y in anios if y in {2022, 2023, 2024, 2025}]
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

    def get_kpis(
        self, *, anio: int | None = None, periodo: str | None = None, vista: str = "indicadores"
    ) -> list[dict]:
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
            {
                "label": "En Peligro",
                "value": peligro["n"],
                "unit": "ind",
                "trend": f"{peligro['pct']}%",
            },
            {
                "label": "En Alerta",
                "value": alerta["n"],
                "unit": "ind",
                "trend": f"{alerta['pct']}%",
            },
            {
                "label": "Sobrecumplimiento",
                "value": sobre["n"],
                "unit": "ind",
                "trend": f"{sobre['pct']}%",
            },
            {
                "label": "En Cumplimiento",
                "value": cumple["n"],
                "unit": "ind",
                "trend": f"{cumple['pct']}%",
            },
        ]

    def get_lineas(
        self, *, anio: int | None = None, periodo: str | None = None, vista: str = "indicadores"
    ) -> list[dict]:
        df_ultimo = self._ensure_cumplimiento_pct(
            self.get_dataset(anio=anio, periodo=periodo, vista=vista)
        )
        if "Linea" not in df_ultimo.columns:
            return []

        lineas = []
        for linea, group in df_ultimo.groupby("Linea", dropna=True):
            nombre = str(linea).strip()
            if not nombre or nombre.lower() == "nan":
                continue
            con_datos = (
                group[group["Cumplimiento_norm"].notna()] if "Cumplimiento_norm" in group else group
            )
            promedio = (
                round(float(con_datos["Cumplimiento_norm"].mean()) * 100, 1)
                if len(con_datos) and "Cumplimiento_norm" in con_datos
                else (
                    round(float(group["cumplimiento_pct"].mean()), 1)
                    if "cumplimiento_pct" in group and group["cumplimiento_pct"].notna().any()
                    else None
                )
            )
            riesgo = (
                int((group["Categoria"].isin(["Peligro", "Alerta"])).sum())
                if "Categoria" in group
                else 0
            )
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

    def get_semaphore(
        self, *, anio: int | None = None, periodo: str | None = None, vista: str = "indicadores"
    ) -> list[dict]:
        df_ultimo = self.get_dataset(anio=anio, periodo=periodo, vista=vista)
        total, conteos = calcular_kpis(df_ultimo)
        if total == 0:
            return []
        return [
            {"categoria": cat, "count": data["n"], "percent": data["pct"]}
            for cat, data in conteos.items()
        ]

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
            return [
                {
                    "periodo": str(anio),
                    "cumplimiento": round(float(avg), 1) if pd.notna(avg) else None,
                }
            ]
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
            return [
                {
                    "id": "sin_datos",
                    "label": "Sin datos",
                    "parent": "",
                    "value": 1,
                    "color": "#6B728E",
                }
            ]

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
                        "value": round(float(row["promedio"]), 1)
                        if pd.notna(row["promedio"])
                        else 0,
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
        nodes: list[dict[str, Any]] = [
            {"id": "root", "label": "PDI", "parent": "", "value": 0, "color": "#1D3557"}
        ]
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
                        "value": round(float(row["cumplimiento_pct"]), 1)
                        if pd.notna(row["cumplimiento_pct"])
                        else 0,
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
            variacion = (
                round(curr - prev_val, 1) if curr is not None and prev_val is not None else None
            )
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
            return {
                "titulo": "Sin datos",
                "parrafos": ["No hay indicadores evaluables para el periodo seleccionado."],
            }

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

    def get_resumen_completo(
        self, *, anio: int, vista: str = "indicadores", rango: bool = False
    ) -> dict[str, Any]:
        """Payload unificado alineado con streamlit resumen_general.py.
        Se cachea por combinación de filtros — este dashboard recorre
        varios builders con groupby/loops pesados (resumen_builders.py) en
        cada request; _warm_caches (main.py) precalienta exactamente
        anio=2025/vista='indicadores'/rango=True al arrancar."""
        key = (id(self._excel), anio, vista, rango)
        return cache_get(
            _RESUMEN_COMPLETO_CACHE,
            key,
            lambda: self._get_resumen_completo_uncached(anio=anio, vista=vista, rango=rango),
            ttl=self._excel.ttl,
        )

    def _get_resumen_completo_uncached(
        self, *, anio: int, vista: str = "indicadores", rango: bool = False
    ) -> dict[str, Any]:
        vista_norm = (vista or "indicadores").strip().lower()
        meses = {
            1: "Enero",
            2: "Febrero",
            3: "Marzo",
            4: "Abril",
            5: "Mayo",
            6: "Junio",
            7: "Julio",
            8: "Agosto",
            9: "Septiembre",
            10: "Octubre",
            11: "Noviembre",
            12: "Diciembre",
        }

        if vista_norm == "indicadores":
            pdi_df = (
                ensure_nivel_cumplimiento(self._strategic.preparar_pdi_cierre_final())
                if rango
                else ensure_nivel_cumplimiento(self._strategic.preparar_pdi_con_cierre(anio, 12))
            )
            chips = get_chip_config_indicadores(pdi_df)
            linea_summary = build_linea_summary(pdi_df, unique_count_col="Id")
            historico_df = self._strategic.load_historico_por_linea()
            cards = build_strategy_cards(linea_summary, historico_df, vista=vista_norm)
            objetivo_cols = [
                c for c in ["Linea", "Objetivo", "cumplimiento_pct"] if c in pdi_df.columns
            ]
            objetivo_df = pdi_df[objetivo_cols].copy() if objetivo_cols else pd.DataFrame()
            mindmap = build_pdi_mindmap(objetivo_df, cards)
            narrativa = generate_narrative_indicadores(pdi_df, linea_summary, chips)

            prev_month = self._strategic.latest_month_for_year(anio - 1)
            best, worst = [], []
            periodo_txt = f"Solo datos de {anio} — sin período anterior disponible"
            if prev_month:
                prev_df = ensure_nivel_cumplimiento(
                    self._strategic.preparar_pdi_con_cierre(anio - 1, prev_month)
                )
                best, worst = compute_trends(pdi_df, prev_df)
                periodo_txt = f"Comparando {anio} (cierre anual) vs {anio - 1} ({meses.get(prev_month, prev_month)})"

            return {
                "anio": anio,
                "vista": vista_norm,
                "chips": chips,
                "fichas": cards,
                "mindmap": mindmap,
                "narrativa": narrativa,
                "mejoraron": best,
                "en_riesgo": worst,
                "periodo_comparacion": periodo_txt,
                "total_indicadores": chips[0]["value"] if chips else 0,
            }

        if vista_norm == "proyectos":
            proy_all = self._strategic.load_proyectos()
            proy_df = (
                self._proyectos_multi_anio(ANIOS_RANGO)
                if rango
                else ensure_nivel_cumplimiento(
                    self._strategic.preparar_proyectos_con_cierre(anio, 12), regimen="plan_anual"
                )
            )
            chips = get_chip_config_proyectos(proy_df)
            if rango:
                vigente_total = self._count_proyectos_ciclo_vigente()
                con_cierre = (
                    int(proy_df["Id"].nunique())
                    if not proy_df.empty and "Id" in proy_df.columns
                    else 0
                )
                chips[0]["value"] = vigente_total
                # Proyectos del ciclo sin cierres cargados aun: se cuentan como Planeacion.
                chips[3]["value"] = chips[3]["value"] + max(vigente_total - con_cierre, 0)
            linea_summary = build_linea_summary(
                proy_df, unique_count_col="Id", count_col_name="N_Proyectos"
            )
            historico_df = proy_df
            cards = build_strategy_cards(linea_summary, historico_df, vista=vista_norm)
            objetivo_cols = [
                c for c in ["Linea", "Objetivo", "cumplimiento_pct"] if c in proy_df.columns
            ]
            objetivo_df = proy_df[objetivo_cols].copy() if objetivo_cols else pd.DataFrame()
            mindmap = build_pdi_mindmap(objetivo_df, cards, regimen="plan_anual")
            narrativa = generate_narrative_proyectos(proy_df, linea_summary)
            gantt = build_proyectos_gantt(proy_all)

            prev_month_p = self._strategic.latest_month_for_year(anio - 1)
            best_p, worst_p = [], []
            periodo_txt_p = f"Solo datos de {anio} — sin período anterior disponible"
            if prev_month_p:
                prev_proy_df = ensure_nivel_cumplimiento(
                    self._strategic.preparar_proyectos_con_cierre(anio - 1, prev_month_p),
                    regimen="plan_anual",
                )
                best_p, worst_p = compute_trends(proy_df, prev_proy_df)
                periodo_txt_p = f"Comparando {anio} (cierre anual) vs {anio - 1} ({meses.get(prev_month_p, prev_month_p)})"

            return {
                "anio": anio,
                "vista": vista_norm,
                "chips": chips,
                "fichas": cards,
                "mindmap": mindmap,
                "narrativa": narrativa,
                "mejoraron": best_p,
                "en_riesgo": worst_p,
                "periodo_comparacion": periodo_txt_p,
                "gantt_proyectos": gantt,
                "total_indicadores": chips[0]["value"] if chips else 0,
                "tabla_detalle": build_proyectos_tabla(proy_df),
            }

        if vista_norm == "retos":
            if rango:
                linea_df, obj_df, planes_df = self._retos_multi_anio(ANIOS_RANGO)
            else:
                linea_df, obj_df = self._retos.load_retos_data(anio)
                planes_df = self._retos.load_planes(anio)
            area_count = self._retos.load_area_count(max(ANIOS_RANGO) if rango else anio)
            linea_summary = build_linea_summary_retos(linea_df, obj_df, planes_df)
            avance_global = self._retos.load_avance_global(ANIOS_RANGO if rango else [anio])
            chips = get_chip_config_retos(linea_summary, area_count, avance_global)
            cards = build_strategy_cards(linea_summary, linea_df, vista=vista_norm)
            mindmap = build_pdi_mindmap(
                obj_df if not obj_df.empty else linea_df,
                cards,
                regimen="plan_anual",
                solo_lineas=obj_df.empty,
            )
            narrativa = generate_narrative_retos(linea_summary, area_count, avance_global)

            return {
                "anio": anio,
                "vista": vista_norm,
                "chips": chips,
                "fichas": cards,
                "mindmap": mindmap,
                "narrativa": narrativa,
                "mejoraron": [],
                "en_riesgo": [],
                "periodo_comparacion": "",
                "total_indicadores": chips[0]["value"] if chips else 0,
                "tabla_detalle": build_retos_tabla(linea_df),
            }

        if vista_norm == "consolidado":
            if rango:
                pdi_df = ensure_nivel_cumplimiento(self._strategic.preparar_pdi_cierre_final())
                proy_df = self._proyectos_multi_anio(ANIOS_RANGO)
                ret_linea_df, ret_obj_df, ret_planes_df = self._retos_multi_anio(ANIOS_RANGO)
            else:
                pdi_df = ensure_nivel_cumplimiento(
                    self._strategic.preparar_pdi_con_cierre(anio, 12)
                )
                proy_df = ensure_nivel_cumplimiento(
                    self._strategic.preparar_proyectos_con_cierre(anio, 12), regimen="plan_anual"
                )
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

            ind_count = (
                int(pdi_df["Id"].nunique()) if not pdi_df.empty and "Id" in pdi_df.columns else 0
            )
            proy_count = (
                self._count_proyectos_ciclo_vigente()
                if rango
                else (
                    int(proy_df["Id"].nunique())
                    if not proy_df.empty and "Id" in proy_df.columns
                    else 0
                )
            )
            area_count = self._retos.load_area_count(max(ANIOS_RANGO) if rango else anio)

            chips = get_chip_config_consolidado(linea_summary, ind_count, proy_count, area_count)
            cards = build_strategy_cards(linea_summary, None, vista=vista_norm)
            mindmap = build_pdi_mindmap(objetivo_df, cards)
            narrativa = generate_narrative_consolidado(
                linea_summary,
                ind_count=ind_count,
                proy_count=proy_count,
                area_count=area_count,
                anio=anio,
            )

            # Informe Estratégico (cualitativo, autoría directa — ver
            # scripts/generar_narrativa_estrategica.py): solo en el rango
            # fijo "Cierre PDI 2022-2025", que es sobre el que se redactó.
            narrativa_estrategica_data = leer_narrativa_estrategica() if rango else None
            narrativa_estrategica = (
                narrativa_estrategica_data.get("consolidado") if narrativa_estrategica_data else None
            )
            tarjetas_consolidado = TARJETAS_CONSOLIDADO if rango else None

            return {
                "anio": anio,
                "vista": vista_norm,
                "chips": chips,
                "fichas": cards,
                "mindmap": mindmap,
                "narrativa": narrativa,
                "narrativa_estrategica": narrativa_estrategica,
                "tarjetas_consolidado": tarjetas_consolidado,
                "mejoraron": [],
                "en_riesgo": [],
                "periodo_comparacion": "",
                "total_indicadores": ind_count + proy_count,
            }

        return {
            "anio": anio,
            "vista": vista_norm,
            "chips": get_chip_config_indicadores(pd.DataFrame()),
            "fichas": build_strategy_cards(pd.DataFrame(), None, vista=vista_norm),
            "mindmap": build_pdi_mindmap(pd.DataFrame(), []),
            "narrativa": {
                "texto": "Vista en construcción.",
                "estado_color": "#6B728E",
                "estado_icon": "info",
                "health_rate": 0,
            },
            "mejoraron": [],
            "en_riesgo": [],
            "periodo_comparacion": "",
            "total_indicadores": 0,
        }

    def get_resumen_linea(self, *, key: str, anio: int | None = None) -> dict[str, Any] | None:
        """Payload de una línea estratégica individual para la hoja de línea
        del portal Resumen General: Retos + Proyectos PMO + Indicadores CMI.
        Reutiliza build_informe_ejecutivo_lineas (misma fuente que el PDF
        Informe Ejecutivo) — cero lógica de agregación duplicada.
        Si `anio` es None se usa el rango completo (Cierre PDI 2022-2025);
        el bloque CMI/objetivos no varía con el año (cierre final del ciclo)."""
        cache_key = (id(self._excel), "resumen-linea", key, anio)
        return cache_get(
            _RESUMEN_COMPLETO_CACHE,
            cache_key,
            lambda: self._get_resumen_linea_uncached(key=key, anio=anio),
            ttl=self._excel.ttl,
        )

    def _get_resumen_linea_uncached(
        self, *, key: str, anio: int | None = None
    ) -> dict[str, Any] | None:
        target = norm_key(key)
        if target not in {norm_key(d["key"]) for d in STRATEGIC_LINE_DEFS}:
            return None

        anios = [anio] if anio is not None else ANIOS_RANGO
        pdi_df = ensure_nivel_cumplimiento(self._strategic.preparar_pdi_cierre_final())
        # Proyectos PMO: fuente real del Centro de Proyectos (Comienzo/Fin/%
        # completado por proyecto), no la derivada de Cierres/Consolidado
        # (build_proyectos_gantt) — esa solo tiene 33 filas totales y no
        # refleja el maestro PMO real (53 proyectos). Confirmado con negocio
        # 2026-09-27, ver ProyectosPmoLoader.
        proy_gantt = build_proyectos_pmo_gantt(self._proyectos_pmo.load(), anios=anios)
        ret_linea_df, ret_obj_df, ret_planes_df = self._retos_multi_anio(anios)
        signo_lookup = self._build_signo_lookup()

        lineas = build_informe_ejecutivo_lineas(
            pdi_df, proy_gantt, ret_linea_df, ret_obj_df, ret_planes_df, signo_lookup
        )
        linea = next((li for li in lineas if norm_key(li["linea"]) == target), None)
        if linea is None:
            return None

        # Narrativa cualitativa (autoría directa, ver
        # scripts/generar_narrativa_estrategica.py): solo aplica al rango fijo
        # "Cierre PDI 2022-2025" sobre el que se redactó — igual criterio que
        # get_informe_ejecutivo/vista consolidado.
        if anio is None:
            narrativa_data = leer_narrativa_estrategica()
            linea["narrativa"] = narrativa_data.get("lineas", {}).get(target) if narrativa_data else None
        return linea

    def _build_signo_lookup(self) -> dict[str, dict[str, Any]]:
        """Meta_Signo/Ejecucion_s/Decimales_* por Id — no viven en
        preparar_pdi_cierre_final() (solo en el histórico de cierres), pero
        son metadatos fijos por indicador, así que un registro cualquiera
        (el último) alcanza. Ver formatValor.ts (fmtValorSigno) — misma
        lógica de formato, portada a Python en _fmt_valor_signo."""
        cierres = self._load_cierres()
        if cierres.empty or "Id" not in cierres.columns:
            return {}
        cols = [
            c
            for c in ["Id", "Meta_Signo", "Ejecucion_s", "Decimales_Meta", "Decimales_Ejecucion"]
            if c in cierres.columns
        ]
        if "Id" not in cols:
            return {}
        dedup = cierres[cols].dropna(subset=["Id"]).drop_duplicates(subset=["Id"], keep="last")

        def _clean(v: Any) -> Any:
            return None if (v is None or (isinstance(v, float) and pd.isna(v))) else v

        lookup: dict[str, dict[str, Any]] = {}
        for _, row in dedup.iterrows():
            meta_signo = _clean(row.get("Meta_Signo"))
            dec_meta = _clean(row.get("Decimales_Meta"))
            # Ejecucion_s casi nunca viene poblado en el histórico de cierres
            # (columna vacía por indicador) — meta y ejecución de un mismo
            # indicador miden la misma unidad, así que ante ausencia se usa
            # el signo/decimales de Meta en vez de asumir "%" a ciegas.
            lookup[str(row["Id"])] = {
                "meta_signo": meta_signo,
                "ejec_signo": _clean(row.get("Ejecucion_s")) or meta_signo,
                "dec_meta": dec_meta,
                "dec_ejec": _clean(row.get("Decimales_Ejecucion")) or dec_meta,
            }
        return lookup

    def get_informe_ejecutivo(self) -> dict[str, Any]:
        """Payload del Informe Ejecutivo PDF — Cierre PDI 2022-2025.
        Articula por línea: Retos, Proyectos PMO (cronograma) e Indicadores
        CMI (objetivo → indicador), sobre el mismo rango fijo que usa la
        vista Consolidado (ANIOS_RANGO)."""
        pdi_df = ensure_nivel_cumplimiento(self._strategic.preparar_pdi_cierre_final())
        # Proyectos PMO: Centro de Proyectos (raw/Proyectos/centroDeProyectos_
        # PMO_2026.xlsx) es la fuente OFICIAL de proyectos — no Cierres/
        # Consolidado (build_proyectos_gantt), que solo cubre los que ya
        # tienen cierre cargado. Confirmado con negocio, 2026-09-27.
        proy_gantt = build_proyectos_pmo_gantt(self._proyectos_pmo.load())
        ret_linea_df, ret_obj_df, ret_planes_df = self._retos_multi_anio(ANIOS_RANGO)
        signo_lookup = self._build_signo_lookup()

        lineas = build_informe_ejecutivo_lineas(
            pdi_df, proy_gantt, ret_linea_df, ret_obj_df, ret_planes_df, signo_lookup
        )
        # El PDF debe listar las líneas en el orden oficial del documento
        # PDI 2022-2026 (docs/PDI/Plan_de_Desarrollo_Institucional_PDI_2022-
        # 2026.docx: 1. Calidad, 2. Expansión, 3. Educación para Toda la
        # Vida, 4. Experiencia, 5. Transformación Organizacional, 6.
        # Sostenibilidad) — no el orden interno de STRATEGIC_LINE_DEFS, que
        # se usa como clave de emparejamiento en el resto de la app.
        _ORDEN_PDI = [
            "calidad",
            "expansion",
            "educacion para toda la vida",
            "experiencia",
            "transformacion organizacional",
            "sostenibilidad",
        ]
        lineas.sort(key=lambda li: _ORDEN_PDI.index(norm_key(li["linea"])))

        total_ind = int(pdi_df["Id"].nunique()) if not pdi_df.empty and "Id" in pdi_df.columns else 0
        nivel = (
            pdi_df.drop_duplicates("Id")["Nivel de cumplimiento"]
            if not pdi_df.empty and "Nivel de cumplimiento" in pdi_df.columns
            else pd.Series(dtype=str)
        )
        cumplidos = int((nivel.isin(["Cumplimiento", "Sobrecumplimiento"])).sum())
        en_progreso = int((nivel == "Alerta").sum())
        atencion = int((nivel == "Peligro").sum())
        # Auditoría 2026-09-27 (V3): cumplidos+en_progreso+atencion NO sumaba
        # el total de indicadores (36+8+2=46 de 49) porque 3 indicadores sin
        # cierre cargado caían en "Pendiente de reporte" y se perdían sin
        # contar aparte — se exponen explícitamente para que el resumen
        # reconcilie (medidos + sin_medicion = total).
        sin_medicion = int((nivel == "Pendiente de reporte").sum())
        medidos = cumplidos + en_progreso + atencion
        # Auditoría 2026-09-27 (confirmado con negocio, decisión "PROMEDIO"):
        # el dato hero de portada es el promedio de los consolidados de línea
        # (Retos+Proyectos+Indicadores ya blendeados por línea), NO el
        # promedio de indicadores solos — evita que portada divierja del
        # detalle por línea (V2). Ver app/domain/pdi_measurement.py.
        consolidados_linea = [
            li["cumplimiento_consolidado"]
            for li in lineas
            if li.get("cumplimiento_consolidado") is not None
        ]
        cumpl_global = (
            sum(consolidados_linea) / len(consolidados_linea) if consolidados_linea else 0.0
        )

        # Confirmado con negocio 2026-09-28: la portada usa el total de
        # "Resultados Consolidados" (catálogo Id, 44) — es intencional, no un
        # dato desactualizado. Distinto del total del Centro de Proyectos PMO
        # (proy_gantt, 47) que alimenta el detalle por línea; el anexo
        # metodológico documenta ambas fuentes en vez de forzarlas a
        # coincidir.
        proy_count = self._count_proyectos_ciclo_vigente()
        # Total global de áreas (hoja "Areas" — sin desglose por línea en el
        # dato fuente, ver build_informe_ejecutivo_lineas). Mismo criterio
        # que la vista Retos/Consolidado: último año del rango.
        areas_count = self._retos.load_area_count(max(ANIOS_RANGO))

        # Narrativa cualitativa (Informe Estratégico): estática, generada
        # aparte con scripts/generar_narrativa_estrategica.py — se lee del
        # JSON si ya se corrió; si no existe aún, cada línea/el consolidado
        # simplemente no traen texto cualitativo (degradación con gracia).
        narrativa = leer_narrativa_estrategica()
        narrativa_consolidada = narrativa.get("consolidado") if narrativa else None
        narrativa_lineas = narrativa.get("lineas", {}) if narrativa else {}
        for li in lineas:
            nl = narrativa_lineas.get(norm_key(li["linea"]))
            li["narrativa"] = nl

        return {
            "generado": "Cierre PDI 2022-2025",
            "cumplimiento_global": round(cumpl_global, 1),
            "total_indicadores": total_ind,
            "cumplidos": cumplidos,
            "en_progreso": en_progreso,
            "atencion": atencion,
            "sin_medicion": sin_medicion,
            "total_medidos": medidos,
            "total_proyectos": proy_count,
            "total_areas": areas_count,
            "lineas": lineas,
            "narrativa_consolidada": narrativa_consolidada,
        }
