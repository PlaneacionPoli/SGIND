"""Constructores de datos para CMI Estratégico — paridad con Streamlit tabulado."""

from __future__ import annotations

import math
import unicodedata
from datetime import date
from typing import Any

import pandas as pd

from app.domain.resumen_builders import compute_trends, ensure_nivel_cumplimiento

CORTE_SEMESTRAL: dict[str, int] = {"Junio": 6, "Diciembre": 12}
CORTE_POR_MES: dict[int, str] = {6: "Junio", 12: "Diciembre"}

LINEA_COLORES: dict[str, str] = {
    "Expansión": "#FBAF17",
    "Transformación organizacional": "#42F2F2",
    "Calidad": "#EC0677",
    "Experiencia": "#1FB2DE",
    "Sostenibilidad": "#A6CE38",
    "Educación para toda la vida": "#0F385A",
}

COLOR_CATEGORIA: dict[str, str] = {
    "Sobrecumplimiento": "#6699FF",
    "Cumplimiento": "#43A047",
    "Alerta": "#FBAF17",
    "Peligro": "#D32F2F",
    "Pendiente de reporte": "#9E9E9E",
}

CATALOGO_LINEAS = list(LINEA_COLORES.keys())

LINEA_DISPLAY_MAP: dict[str, str] = {
    "expansion": "Expansión",
    "transformacion organizacional": "Transformación Organizacional",
    "calidad": "Calidad",
    "experiencia": "Experiencia",
    "sostenibilidad": "Sostenibilidad",
    "educacion para toda la vida": "Educación para toda la vida",
}

from app.domain.linea_order import LINEA_ORDER, linea_sort_key


def default_anio(anios: list[int]) -> int:
    if 2025 in anios:
        return 2025
    if anios:
        return anios[-1]
    return date.today().year


def default_corte(anio: int | None) -> str:
    if anio is None:
        return "Diciembre"
    today = date.today()
    if int(anio) < today.year:
        return "Diciembre"
    if today > date(today.year, 7, 20):
        return "Junio"
    return "Diciembre"


def normalize_linea_key(linea: Any) -> str:
    txt = str(linea or "").strip().lower().replace("_", " ")
    txt = unicodedata.normalize("NFD", txt)
    return "".join(ch for ch in txt if unicodedata.category(ch) != "Mn")


def linea_color(linea: str) -> str:
    key = normalize_linea_key(linea)
    for name, color in LINEA_COLORES.items():
        if normalize_linea_key(name) == key:
            return color
    for name, color in LINEA_COLORES.items():
        nk = normalize_linea_key(name)
        if nk in key or key in nk:
            return color
    if "expansi" in key:
        return "#FBAF17"
    if "transform" in key:
        return "#42F2F2"
    if "calidad" in key:
        return "#EC0677"
    if "experien" in key:
        return "#1FB2DE"
    if "sostenib" in key or "sustentab" in key:
        return "#A6CE38"
    if "educaci" in key or "toda la vida" in key:
        return "#0F385A"
    return "#1A3A5C"


def _safe_float(val: Any, default: float | None = None) -> float | None:
    if val is None or (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
        return default
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except (TypeError, ValueError):
        return default


def _clean_value(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    if pd.isna(val):
        return None
    if isinstance(val, (int, float, str, bool)):
        return val
    return str(val)


def df_to_records(df: pd.DataFrame, columns: list[str] | None = None) -> list[dict[str, Any]]:
    if df.empty:
        return []
    cols = [c for c in (columns or df.columns.tolist()) if c in df.columns]
    records: list[dict[str, Any]] = []
    for row in df[cols].to_dict(orient="records"):
        records.append({k: _clean_value(v) for k, v in row.items()})
    return records


def calcular_kpis(df: pd.DataFrame) -> dict[str, Any]:
    total = len(df)
    con_dato = int(df["cumplimiento_pct"].notna().sum()) if "cumplimiento_pct" in df.columns else 0
    promedio = _safe_float(df["cumplimiento_pct"].mean(), 0.0) if con_dato else 0.0
    top_nivel = "Sin dato"
    conteo_estados: dict[str, int] = {}
    if total > 0 and "Nivel de cumplimiento" in df.columns:
        vc = df["Nivel de cumplimiento"].value_counts()
        if not vc.empty:
            top_nivel = str(vc.idxmax())
        conteo_estados = {str(k): int(v) for k, v in vc.to_dict().items()}
    en_riesgo = conteo_estados.get("Peligro", 0) + conteo_estados.get("Alerta", 0)
    return {
        "total": total,
        "con_dato": con_dato,
        "promedio": round(promedio or 0.0, 1),
        "top_nivel": top_nivel,
        "n_lineas_vis": int(df["Linea"].nunique()) if "Linea" in df.columns else 0,
        "n_obj_vis": int(df["Objetivo"].nunique()) if "Objetivo" in df.columns else 0,
        "conteo_estados": conteo_estados,
        "en_riesgo": en_riesgo,
    }


def build_cumplimiento_por_linea(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty or "Linea" not in df.columns or "cumplimiento_pct" not in df.columns:
        return []
    by_linea = (
        df.groupby("Linea", dropna=False)["cumplimiento_pct"]
        .mean()
        .fillna(0)
        .reset_index()
    )
    by_linea["_order"] = by_linea["Linea"].map(lambda x: linea_sort_key(str(x)))
    by_linea = by_linea.sort_values("_order")
    result = []
    for _, row in by_linea.iterrows():
        linea = str(row["Linea"])
        cumpl = round(_safe_float(row["cumplimiento_pct"], 0.0) or 0.0, 1)
        result.append({"linea": linea, "cumplimiento": cumpl, "color": linea_color(linea)})
    return result


def build_distribucion_nivel(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty or "Nivel de cumplimiento" not in df.columns:
        return []
    niveles = df["Nivel de cumplimiento"].fillna("Pendiente de reporte").value_counts().reset_index()
    niveles.columns = ["nivel", "cantidad"]
    total = int(niveles["cantidad"].sum()) or 1
    result = []
    for _, row in niveles.iterrows():
        nivel = str(row["nivel"])
        cantidad = int(row["cantidad"])
        result.append(
            {
                "nivel": nivel,
                "cantidad": cantidad,
                "porcentaje": round(cantidad / total * 100, 1),
                "color": COLOR_CATEGORIA.get(nivel, "#9E9E9E"),
            }
        )
    return result


def _nivel_counts(df_linea: pd.DataFrame) -> dict[str, int]:
    if "Nivel de cumplimiento" not in df_linea.columns:
        return {
            "n_sobrecumplimiento": 0,
            "n_cumplimiento": 0,
            "n_alerta": 0,
            "n_riesgo": 0,
        }
    niveles = df_linea["Nivel de cumplimiento"].astype(str).str.strip()
    return {
        "n_sobrecumplimiento": int((niveles == "Sobrecumplimiento").sum()),
        "n_cumplimiento": int((niveles == "Cumplimiento").sum()),
        "n_alerta": int((niveles == "Alerta").sum()),
        "n_riesgo": int((niveles == "Peligro").sum()),
    }


def _estado_linea_card(cump: float, tiene_datos: bool) -> dict[str, str]:
    if not tiene_datos:
        return {
            "estado_label": "Sin datos",
            "estado_icon": "—",
            "estado_color": "#6B7280",
            "estado_bg": "#F3F4F6",
            "estado_text": "#4B5563",
        }
    if cump >= 100:
        return {
            "estado_label": "Meta alcanzada",
            "estado_icon": "↑",
            "estado_color": "#43A047",
            "estado_bg": "#E8F5E9",
            "estado_text": "#2E7D32",
        }
    if cump >= 80:
        return {
            "estado_label": "En proceso",
            "estado_icon": "→",
            "estado_color": "#FBAF17",
            "estado_bg": "#FFF8E1",
            "estado_text": "#F57F17",
        }
    return {
        "estado_label": "Requiere atención",
        "estado_icon": "⚠",
        "estado_color": "#D32F2F",
        "estado_bg": "#FFEBEE",
        "estado_text": "#B71C1C",
    }


def _estado_linea(cump: float) -> tuple[str, str]:
    if cump >= 100:
        return "Sobrecumplimiento", COLOR_CATEGORIA["Sobrecumplimiento"]
    if cump >= 95:
        return "Cumplimiento", COLOR_CATEGORIA["Cumplimiento"]
    if cump >= 80:
        return "Alerta", COLOR_CATEGORIA["Alerta"]
    return "Peligro", COLOR_CATEGORIA["Peligro"]


def build_vista_rapida_lineas(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty or "Linea" not in df.columns:
        return []
    presentes = sorted(
        [ln for ln in df["Linea"].dropna().unique() if str(ln).strip()],
        key=linea_sort_key,
    )
    catalogo_por_clave = {normalize_linea_key(ln): ln for ln in CATALOGO_LINEAS}
    presentes_por_clave = {normalize_linea_key(ln): ln for ln in presentes}
    lineas = [presentes_por_clave[k] for k in presentes_por_clave] + [
        catalogo_por_clave[k] for k in catalogo_por_clave if k not in presentes_por_clave
    ]

    cards = []
    for linea in lineas:
        mask = df["Linea"].apply(normalize_linea_key) == normalize_linea_key(linea)
        df_l = df[mask]
        cump = _safe_float(df_l["cumplimiento_pct"].mean(), 0.0) if not df_l.empty else 0.0
        cump = cump or 0.0
        estado, estado_color = _estado_linea(cump)
        counts = _nivel_counts(df_l)
        n_obj = int(df_l["Objetivo"].nunique()) if "Objetivo" in df_l.columns and not df_l.empty else 0
        card_estado = _estado_linea_card(cump, not df_l.empty)
        cump_safe = max(0.0, cump)
        progress_meta = "Meta 100%"
        if cump_safe > 100:
            progress_meta = f"Meta 100% | +{(cump_safe - 100):.1f}%"
        linea_key_norm = normalize_linea_key(linea)
        linea_display = LINEA_DISPLAY_MAP.get(linea_key_norm, str(linea).strip().replace("_", " "))
        cards.append(
            {
                "linea": str(linea),
                "linea_display": linea_display,
                "linea_key": linea_key_norm,
                "color": linea_color(str(linea)),
                "cumplimiento": round(cump, 1),
                "estado": estado,
                "estado_color": estado_color,
                **card_estado,
                "progress_meta_label": progress_meta,
                "progress_width": round(min(100.0, cump_safe), 1),
                "total_indicadores": len(df_l),
                "n_objetivos": n_obj,
                **counts,
                "tiene_datos": not df_l.empty,
            }
        )
    return cards


def build_insights(kpis: dict[str, Any]) -> list[dict[str, str]]:
    conteo = kpis.get("conteo_estados", {})
    peligro = conteo.get("Peligro", 0)
    alerta = conteo.get("Alerta", 0)
    cump = conteo.get("Cumplimiento", 0)
    sobre = conteo.get("Sobrecumplimiento", 0)
    insights: list[dict[str, str]] = []

    if peligro > 0:
        insights.append(
            {
                "tipo": "peligro",
                "titulo": "Atención requerida",
                "mensaje": f"Hay {peligro} indicadores en Peligro que requieren revisión inmediata.",
            }
        )
    if alerta > 0:
        insights.append(
            {
                "tipo": "alerta",
                "titulo": "Monitoreo",
                "mensaje": f"{alerta} indicadores se encuentran en Alerta. Se sugiere seguimiento cercano.",
            }
        )
    if cump + sobre > 0:
        insights.append(
            {
                "tipo": "positivo",
                "titulo": "Buen desempeño",
                "mensaje": f"{cump + sobre} indicadores han alcanzado o superado la meta institucional.",
            }
        )
    if peligro == 0 and alerta == 0 and insights:
        insights.append(
            {
                "tipo": "excelente",
                "titulo": "Excelente",
                "mensaje": "Todos los indicadores están en estado favorable.",
            }
        )
    if not insights:
        insights.append(
            {
                "tipo": "info",
                "titulo": "Sin datos suficientes",
                "mensaje": "No hay indicadores con cumplimiento reportado para este corte.",
            }
        )
    return insights


def build_top_indicadores(df_linea: pd.DataFrame, limit: int = 6) -> list[dict[str, Any]]:
    cols = ["Indicador", "cumplimiento_pct", "Nivel de cumplimiento"]
    if df_linea.empty or not all(c in df_linea.columns for c in cols[:2]):
        return []
    work = df_linea[cols].dropna(subset=["Indicador"]).copy()
    work["cumplimiento_pct"] = pd.to_numeric(work["cumplimiento_pct"], errors="coerce")
    work = work.sort_values("cumplimiento_pct", ascending=False).head(limit)
    return df_to_records(work)


def build_objetivos_estructura(
    df_linea: pd.DataFrame,
    pdi_catalog: pd.DataFrame | None = None,
) -> list[dict[str, Any]]:
    if df_linea.empty or "Objetivo" not in df_linea.columns:
        return []
    objetivos = sorted(df_linea["Objetivo"].dropna().astype(str).unique().tolist())
    result = []
    ind_cols = [
        c
        for c in [
            "Id",
            "Indicador",
            "Meta",
            "Ejecucion",
            "Meta_Signo",
            "Ejecucion_s",
            "EjecS",
            "Decimales_Meta",
            "Decimales_Ejecucion",
            "cumplimiento_pct",
            "Nivel de cumplimiento",
            "Proceso",
            "Meta_Estrategica",
        ]
        if c in df_linea.columns
    ]

    for obj in objetivos:
        df_obj = df_linea[df_linea["Objetivo"] == obj].copy()
        metas_block: list[dict[str, Any]] = []
        if "Meta_Estrategica" in df_obj.columns:
            metas = sorted(df_obj["Meta_Estrategica"].dropna().astype(str).str.strip().unique().tolist())
            metas = [m for m in metas if m]
            for meta in metas:
                df_meta = df_obj[df_obj["Meta_Estrategica"].astype(str).str.strip() == meta]
                metas_block.append(
                    {
                        "meta": meta,
                        "indicadores": df_to_records(df_meta[ind_cols]),
                    }
                )
        if not metas_block:
            metas_block.append({"meta": None, "indicadores": df_to_records(df_obj[ind_cols])})
        result.append({"objetivo": obj, "metas": metas_block})
    return result


def build_linea_historico(cierres: pd.DataFrame, ids: list[str]) -> list[dict[str, Any]]:
    if cierres.empty or not ids:
        return []
    work = cierres[cierres["Id"].astype(str).isin({str(i) for i in ids})].copy()
    if work.empty or "Anio" not in work.columns:
        return []
    work = ensure_nivel_cumplimiento(work)
    work["Periodo"] = work["Anio"].astype(str) + "-" + work.get("Mes", pd.Series([12] * len(work))).astype(int).astype(str).str.zfill(2)
    hist = work.groupby("Periodo")["cumplimiento_pct"].mean().reset_index().sort_values("Periodo")
    return [
        {
            "periodo": str(r["Periodo"]),
            "cumplimiento": round(_safe_float(r["cumplimiento_pct"], 0.0) or 0.0, 1),
        }
        for _, r in hist.iterrows()
    ]


def previous_corte(anio: int, mes: int) -> tuple[int, int]:
    if int(mes) == 12:
        return int(anio), 6
    return int(anio) - 1, 12


def _indicadores_riesgo(df_linea: pd.DataFrame, limit: int = 8) -> list[dict[str, Any]]:
    if df_linea.empty or "Nivel de cumplimiento" not in df_linea.columns:
        return []
    cols = [c for c in ["Id", "Indicador", "Objetivo", "cumplimiento_pct", "Nivel de cumplimiento"] if c in df_linea.columns]
    work = df_linea[df_linea["Nivel de cumplimiento"].isin(["Peligro", "Alerta"])].copy()
    if work.empty or "cumplimiento_pct" not in work.columns:
        return []
    work["cumplimiento_pct"] = pd.to_numeric(work["cumplimiento_pct"], errors="coerce")
    work = work.sort_values("cumplimiento_pct", ascending=True).head(limit)
    return df_to_records(work[cols])


def generate_linea_narrativa_heuristica(
    linea: str,
    cumplimiento_promedio: float,
    total_ind: int,
    total_riesgo: int,
    df_linea: pd.DataFrame,
) -> dict[str, Any]:
    """Port de _analisis_heuristico_linea (ai_analysis.py) — sin dependencia de Anthropic."""
    cump = cumplimiento_promedio or 0.0
    riesgo_ratio = (float(total_riesgo) / float(total_ind)) if total_ind else 0.0

    if cump >= 100:
        estado = "La línea presenta desempeño agregado favorable y supera la meta institucional."
        estado_color = "#16A34A"
        estado_icon = "success"
    elif cump >= 95:
        estado = "La línea presenta desempeño estable, con brechas acotadas que requieren monitoreo cercano."
        estado_color = "#2563EB"
        estado_icon = "chart"
    else:
        estado = "La línea presenta desviación relevante frente a la meta y requiere priorización de acciones."
        estado_color = "#DC2626"
        estado_icon = "alert"

    foco_urgente = "No se pudo identificar un indicador crítico con los datos disponibles."
    if not df_linea.empty and "Nivel de cumplimiento" in df_linea.columns:
        work = df_linea.copy()
        if "cumplimiento_pct" in work.columns:
            work["cumplimiento_pct"] = pd.to_numeric(work["cumplimiento_pct"], errors="coerce")

        def _nivel_rank(nivel: Any) -> int:
            txt = str(nivel or "").strip().lower()
            if "peligro" in txt:
                return 0
            if "alerta" in txt:
                return 1
            return 2

        work["_rank"] = work["Nivel de cumplimiento"].map(_nivel_rank)
        sort_cols = ["_rank"] + (["cumplimiento_pct"] if "cumplimiento_pct" in work.columns else [])
        crit = work.sort_values(sort_cols, ascending=True).iloc[0]
        indic = str(crit.get("Indicador", "Indicador sin nombre")).strip() or "Indicador sin nombre"
        objetivo = str(crit.get("Objetivo", "Objetivo no informado")).strip() or "Objetivo no informado"
        nivel = str(crit.get("Nivel de cumplimiento", "Sin nivel")).strip() or "Sin nivel"
        cump_row = _safe_float(crit.get("cumplimiento_pct"), 0.0) or 0.0
        foco_urgente = (
            f"Se prioriza <strong>{indic}</strong> (objetivo: {objetivo}), con nivel "
            f"<strong>{nivel}</strong> y cumplimiento de <strong>{cump_row:.1f}%</strong>."
        )

    dir_1 = (
        "Enfocar seguimiento semanal en indicadores en riesgo y asegurar cierre de brechas "
        "operativas de corto plazo."
    )
    if riesgo_ratio > 0.25:
        dir_2 = (
            "Activar comité táctico por línea con responsables por objetivo y compromisos "
            "de recuperación por periodo."
        )
    else:
        dir_2 = (
            "Consolidar prácticas de los indicadores con mejor desempeño para replicarlas "
            "en objetivos rezagados."
        )

    directrices = [dir_1, dir_2]
    texto = (
        f"{estado} En la línea <strong>{linea}</strong>, se observan "
        f"<strong>{total_riesgo}</strong> indicadores en alerta/peligro sobre "
        f"<strong>{total_ind}</strong>.<br/><br/>"
        f"<strong>Foco urgente:</strong> {foco_urgente}<br/>"
        f"<strong>Directriz 1:</strong> {dir_1}<br/>"
        f"<strong>Directriz 2:</strong> {dir_2}"
    )
    return {
        "titulo": "Insights y Directrices Estratégicas",
        "estado": estado,
        "estado_color": estado_color,
        "estado_icon": estado_icon,
        "foco_urgente": foco_urgente,
        "directrices": directrices,
        "texto_html": texto,
        "fuente": "heuristica",
    }


def build_linea_analisis(
    df_linea: pd.DataFrame,
    cierres: pd.DataFrame,
    *,
    df_previous: pd.DataFrame | None = None,
    anio: int | None = None,
    mes: int | None = None,
) -> dict[str, Any]:
    ids = df_linea["Id"].dropna().astype(str).tolist() if "Id" in df_linea.columns else []
    historico = build_linea_historico(cierres, ids)

    cump_actual = _safe_float(df_linea["cumplimiento_pct"].mean(), 0.0) if "cumplimiento_pct" in df_linea.columns else 0.0
    cump_actual = cump_actual or 0.0
    counts = _nivel_counts(df_linea)
    n_riesgo = counts["n_alerta"] + counts["n_riesgo"]

    cump_anterior: float | None = None
    variacion_pp: float | None = None
    periodo_comparacion = ""
    if df_previous is not None and not df_previous.empty and "cumplimiento_pct" in df_previous.columns:
        cump_anterior = _safe_float(df_previous["cumplimiento_pct"].mean(), None)
        if cump_anterior is not None:
            variacion_pp = round(cump_actual - cump_anterior, 1)
        if anio is not None and mes is not None:
            prev_anio, prev_mes = previous_corte(int(anio), int(mes))
            periodo_comparacion = f"{prev_anio}-{str(prev_mes).zfill(2)}"

    mejoraron: list[dict[str, Any]] = []
    empeoraron: list[dict[str, Any]] = []
    if df_previous is not None and not df_previous.empty:
        mejoraron, empeoraron = compute_trends(df_linea, df_previous)

    narrativa = generate_linea_narrativa_heuristica(
        str(df_linea["Linea"].iloc[0]) if "Linea" in df_linea.columns and not df_linea.empty else "",
        cump_actual,
        len(df_linea),
        n_riesgo,
        df_linea,
    )

    return {
        "historico": historico,
        "cumplimiento_actual": round(cump_actual, 1),
        "cumplimiento_anterior": round(cump_anterior, 1) if cump_anterior is not None else None,
        "variacion_pp": variacion_pp,
        "periodo_comparacion": periodo_comparacion,
        "mejoraron": mejoraron,
        "empeoraron": empeoraron,
        "indicadores_riesgo": _indicadores_riesgo(df_linea),
        "narrativa": narrativa,
    }


def build_lineas_detalle(
    df: pd.DataFrame,
    cierres: pd.DataFrame,
    pdi_catalog: pd.DataFrame | None = None,
    *,
    df_previous: pd.DataFrame | None = None,
    anio: int | None = None,
    mes: int | None = None,
) -> list[dict[str, Any]]:
    if df.empty or "Linea" not in df.columns:
        return []
    lineas = sorted([str(ln).strip() for ln in df["Linea"].dropna().unique() if str(ln).strip()], key=linea_sort_key)
    result = []
    for linea in lineas:
        df_linea = df[df["Linea"] == linea].copy()
        cump = _safe_float(df_linea["cumplimiento_pct"].mean(), 0.0) if "cumplimiento_pct" in df_linea.columns else 0.0
        cump = cump or 0.0
        counts = _nivel_counts(df_linea)
        n_meta = 0
        if pdi_catalog is not None and not pdi_catalog.empty and "Meta_Estrategica" in pdi_catalog.columns:
            if "Linea" in pdi_catalog.columns:
                metas = pdi_catalog[pdi_catalog["Linea"].astype(str).str.strip() == linea]["Meta_Estrategica"]
                n_meta = int(metas.astype(str).str.strip().replace("", pd.NA).dropna().nunique())
        elif "Meta_Estrategica" in df_linea.columns:
            n_meta = int(df_linea["Meta_Estrategica"].astype(str).str.strip().replace("", pd.NA).dropna().nunique())

        ids = df_linea["Id"].dropna().astype(str).tolist() if "Id" in df_linea.columns else []
        df_prev_linea = None
        if df_previous is not None and not df_previous.empty and "Linea" in df_previous.columns:
            df_prev_linea = df_previous[df_previous["Linea"] == linea].copy()

        result.append(
            {
                "linea": linea,
                "linea_key": normalize_linea_key(linea),
                "color": linea_color(linea),
                "cumplimiento_promedio": round(cump, 1),
                "total_indicadores": len(df_linea),
                "n_objetivos": int(df_linea["Objetivo"].nunique()) if "Objetivo" in df_linea.columns else 0,
                "n_metas": n_meta,
                **counts,
                "top_indicadores": build_top_indicadores(df_linea),
                "objetivos": build_objetivos_estructura(df_linea, pdi_catalog),
                "historico": build_linea_historico(cierres, ids),
                "analisis": build_linea_analisis(
                    df_linea,
                    cierres,
                    df_previous=df_prev_linea,
                    anio=anio,
                    mes=mes,
                ),
            }
        )
    return result


def build_alertas(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty or "Nivel de cumplimiento" not in df.columns:
        return {"peligro": 0, "alerta": 0, "items": []}
    df_alertas = df[df["Nivel de cumplimiento"].isin(["Peligro", "Alerta"])].copy()
    conteo = df_alertas["Nivel de cumplimiento"].value_counts().to_dict()
    cols = [
        c
        for c in [
            "Id",
            "Indicador",
            "Linea",
            "Objetivo",
            "Meta",
            "Ejecucion",
            "Meta_Signo",
            "Ejecucion_s",
            "EjecS",
            "Decimales_Meta",
            "Decimales_Ejecucion",
            "cumplimiento_pct",
            "Nivel de cumplimiento",
            "Proceso",
        ]
        if c in df_alertas.columns
    ]
    items = df_to_records(df_alertas.sort_values("cumplimiento_pct", na_position="last")[cols])
    return {
        "peligro": int(conteo.get("Peligro", 0)),
        "alerta": int(conteo.get("Alerta", 0)),
        "items": items,
    }


def build_indicadores_listado(df: pd.DataFrame) -> list[dict[str, Any]]:
    cols = [
        c
        for c in [
            "Id",
            "Indicador",
            "Linea",
            "Objetivo",
            "Meta_Estrategica",
            "Meta",
            "Ejecucion",
            "Meta_Signo",
            "Ejecucion_s",
            "EjecS",
            "Decimales_Meta",
            "Decimales_Ejecucion",
            "cumplimiento_pct",
            "Nivel de cumplimiento",
            "Proceso",
            "Periodicidad",
            "Anio",
            "Descripcion",
            "Responsable del calculo",
            "Fuente V1",
            "Formula",
            "Frecuencia",
        ]
        if c in df.columns
    ]
    return df_to_records(df, cols)
