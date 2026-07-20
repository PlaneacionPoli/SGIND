"""Constructores Plan de Mejoramiento — paridad streamlit_app/pages/plan_mejoramiento.py."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.domain.loader_utils import find_col, id_a_str

CORTE_SEMESTRAL = {"Junio": 6, "Diciembre": 12}

NIVEL_COLOR_EXT = {
    "Peligro": "#D32F2F",
    "Alerta": "#FBAF17",
    "Cumplimiento": "#43A047",
    "Sobrecumplimiento": "#6699FF",
    "No aplica": "#78909C",
    "Pendiente de reporte": "#BDBDBD",
    "Sin dato": "#BDBDBD",
}

NIVEL_EMOJI = {
    "Peligro": "🔴",
    "Alerta": "🟡",
    "Cumplimiento": "🟢",
    "Sobrecumplimiento": "🔵",
    "No aplica": "⚫",
    "Pendiente de reporte": "⚪",
    "Sin dato": "⚪",
}

_ACCIONES_PATH = "raw/acciones_mejora.xlsx"
_FACTOR_PALETTE = [
    "#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3",
    "#fdb462", "#b3de69", "#fccde5", "#d9d9d9", "#bc80bd",
    "#ccebc5", "#ffed6f", "#e41a1c", "#377eb8", "#4daf4a",
]


def load_acciones_mejora(excel) -> pd.DataFrame:
    path = excel.data_root / _ACCIONES_PATH
    if not path.exists():
        return pd.DataFrame()
    try:
        df = excel.read_excel(_ACCIONES_PATH, sheet_name="Acciones")
    except Exception:
        return pd.DataFrame()
    df.columns = [str(c).strip() for c in df.columns]
    for col in ["FECHA_IDENTIFICACION", "FECHA_ESTIMADA_CIERRE", "FECHA_CIERRE", "FECHA_CREACION"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in ["DIAS_VENCIDA", "MESES_SIN_AVANCE", "AVANCE"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def build_filtros_corte(cierres: pd.DataFrame) -> dict[str, Any]:
    anios = sorted(
        pd.to_numeric(cierres["Anio"], errors="coerce").dropna().astype(int).unique().tolist()
    ) if not cierres.empty and "Anio" in cierres.columns else []
    default_year = 2025 if 2025 in anios else (anios[-1] if anios else None)
    return {
        "anios": anios,
        "anio_default": default_year,
        "corte_default": "Diciembre",
        "cortes": list(CORTE_SEMESTRAL.keys()),
    }


def apply_cna_filters(
    df: pd.DataFrame,
    *,
    factor: str | None = None,
    caracteristica: str | None = None,
    nombre: str | None = None,
) -> pd.DataFrame:
    out = df.copy()
    if factor and factor != "Todos" and "Factor" in out.columns:
        out = out[out["Factor"].astype(str) == factor]
    if caracteristica and caracteristica not in ("Todas", "Todos") and "Caracteristica" in out.columns:
        out = out[out["Caracteristica"].astype(str) == caracteristica]
    if nombre and nombre.strip() and "Indicador" in out.columns:
        out = out[out["Indicador"].astype(str).str.contains(nombre.strip(), case=False, na=False)]
    return out


def _factor_colors(factors: list[str]) -> dict[str, str]:
    return {f: _FACTOR_PALETTE[i % len(_FACTOR_PALETTE)] for i, f in enumerate(factors)}


def _round_pct(val) -> float | None:
    if pd.isna(val):
        return None
    return round(float(val), 1)


def build_kpis(df: pd.DataFrame, catalog: pd.DataFrame) -> dict[str, Any]:
    total = len(df)
    con_dato = int(df["cumplimiento_pct"].notna().sum()) if "cumplimiento_pct" in df.columns else 0
    prom = float(df["cumplimiento_pct"].mean()) if con_dato and "cumplimiento_pct" in df.columns else 0.0
    n_fact = int(df["Factor"].nunique()) if "Factor" in df.columns else 0
    n_car = int(df["Caracteristica"].nunique()) if "Caracteristica" in df.columns else 0
    total_fact_cat = int(catalog["Factor"].nunique()) if not catalog.empty else n_fact
    total_car_cat = int(catalog["Caracteristica"].nunique()) if not catalog.empty else n_car
    return {
        "indicadores_cna": total,
        "factores_visibles": n_fact,
        "caracteristicas_visibles": n_car,
        "con_cumplimiento": con_dato,
        "promedio_cumplimiento": round(prom, 1),
        "catalogo_factores": total_fact_cat,
        "catalogo_caracteristicas": total_car_cat,
    }


def build_graficos(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {"factor_bars": [], "nivel_donut": [], "factor_nivel_stacked": [], "treemap": []}

    factor_list = sorted(df["Factor"].dropna().astype(str).unique().tolist()) if "Factor" in df.columns else []
    color_map = _factor_colors(factor_list)

    factor_bars = []
    if "Factor" in df.columns and "cumplimiento_pct" in df.columns:
        by_factor = (
            df.groupby("Factor", dropna=False)["cumplimiento_pct"]
            .mean()
            .fillna(0)
            .reset_index()
            .sort_values("cumplimiento_pct", ascending=True)
        )
        for _, row in by_factor.iterrows():
            f = str(row["Factor"])
            factor_bars.append({
                "factor": f,
                "cumplimiento": _round_pct(row["cumplimiento_pct"]),
                "color": color_map.get(f, "#888"),
            })

    nivel_donut = []
    if "Nivel de cumplimiento" in df.columns:
        niveles = df["Nivel de cumplimiento"].fillna("Pendiente de reporte").value_counts().reset_index()
        niveles.columns = ["nivel", "cantidad"]
        for _, row in niveles.iterrows():
            n = str(row["nivel"])
            nivel_donut.append({
                "nivel": n,
                "cantidad": int(row["cantidad"]),
                "color": NIVEL_COLOR_EXT.get(n, "#BDBDBD"),
                "emoji": NIVEL_EMOJI.get(n, "⚪"),
            })

    factor_nivel_stacked = []
    if "Factor" in df.columns and "Nivel de cumplimiento" in df.columns:
        stacked = (
            df.groupby(["Factor", "Nivel de cumplimiento"], dropna=False)
            .size()
            .reset_index(name="cantidad")
        )
        for factor in factor_list:
            subset = stacked[stacked["Factor"].astype(str) == factor]
            niveles = []
            for _, row in subset.iterrows():
                n = str(row["Nivel de cumplimiento"])
                niveles.append({
                    "nivel": n,
                    "cantidad": int(row["cantidad"]),
                    "color": NIVEL_COLOR_EXT.get(n, "#BDBDBD"),
                })
            factor_nivel_stacked.append({"factor": factor, "niveles": niveles, "color": color_map.get(factor, "#888")})

    treemap = []
    if "Factor" in df.columns and "Caracteristica" in df.columns:
        counts = df.groupby(["Factor", "Caracteristica"], dropna=False).size().reset_index(name="cantidad")
        for factor in factor_list:
            subset = counts[counts["Factor"].astype(str) == factor]
            children = []
            for _, row in subset.iterrows():
                children.append({
                    "caracteristica": str(row["Caracteristica"]),
                    "cantidad": int(row["cantidad"]),
                })
            treemap.append({"factor": factor, "cantidad": int(subset["cantidad"].sum()), "children": children, "color": color_map.get(factor, "#888")})

    return {
        "factor_bars": factor_bars,
        "nivel_donut": nivel_donut,
        "factor_nivel_stacked": factor_nivel_stacked,
        "treemap": treemap,
        "factor_colors": color_map,
    }


def build_tabla_cna(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []
    cols_order = [
        "Id", "Indicador", "Factor", "Caracteristica", "cumplimiento_pct",
        "Nivel de cumplimiento", "Meta", "Ejecucion",
        "Meta_Signo", "Ejecucion_s", "EjecS", "Decimales_Meta", "Decimales_Ejecucion",
        "Sentido", "Anio", "Mes", "Fecha",
    ]
    present = [c for c in cols_order if c in df.columns]
    sort_cols = [c for c in ["Factor", "Caracteristica", "Id"] if c in df.columns]
    sorted_df = df.sort_values(sort_cols) if sort_cols else df
    records = []
    for _, row in sorted_df.iterrows():
        rec: dict[str, Any] = {}
        for c in present:
            val = row[c]
            if pd.isna(val):
                rec[c] = None
            elif c == "cumplimiento_pct":
                rec["cumplimiento_pct"] = _round_pct(val)
            elif c == "Nivel de cumplimiento":
                n = str(val)
                rec["nivel"] = n
                rec["nivel_emoji"] = NIVEL_EMOJI.get(n, "⚪")
                rec["nivel_color"] = NIVEL_COLOR_EXT.get(n, "#BDBDBD")
            elif isinstance(val, (int, float)):
                rec[c] = float(val) if isinstance(val, float) else int(val)
            else:
                rec[c] = str(val)
        records.append(rec)
    return records


def build_acciones_section(df_acc: pd.DataFrame, ids_cna: set[str] | None = None) -> dict[str, Any]:
    if df_acc.empty:
        return {"kpis": {}, "avance_por_estado": [], "tabla": []}

    df = df_acc.copy()
    id_col = find_col(df, ["ID_INDICADOR", "Id indicador", "Id", "ID"])
    if id_col:
        df["_id"] = df[id_col].apply(id_a_str)
        if ids_cna:
            df = df[df["_id"].isin(ids_cna)]

    estado_col = find_col(df, ["ESTADO", "Estado"])
    avance_col = find_col(df, ["AVANCE", "Avance"])
    accion_col = find_col(df, ["ACCION", "Acción", "Accion"])
    tiempo_col = find_col(df, ["ESTADO_TIEMPO", "Estado tiempo", "Estado Tiempo"])
    fecha_col = find_col(df, ["FECHA_ESTIMADA_CIERRE", "Fecha compromiso", "Fecha estimada cierre"])
    resp_col = find_col(df, ["RESPONSABLE", "Responsable"])

    total = len(df)
    cerradas = 0
    abiertas = 0
    if estado_col:
        estados = df[estado_col].astype(str).str.lower()
        cerradas = int(estados.str.contains("cerrad|complet|finaliz", na=False).sum())
        abiertas = total - cerradas

    avance_prom = 0.0
    if avance_col:
        av = pd.to_numeric(df[avance_col], errors="coerce")
        if av.notna().any():
            avance_prom = round(float(av.mean()), 1)

    vencidas = 0
    tiempo_vals = df[tiempo_col].astype(str).str.lower() if tiempo_col else pd.Series(dtype=str)
    if not tiempo_vals.empty:
        vencidas = int(tiempo_vals.str.contains("vencid", na=False).sum())

    avance_por_estado = []
    if estado_col and avance_col:
        grouped = df.groupby(estado_col)[avance_col].mean().reset_index()
        for _, row in grouped.iterrows():
            avance_por_estado.append({
                "estado": str(row[estado_col]),
                "avance": _round_pct(row[avance_col]),
            })

    tabla = []
    for _, row in df.head(500).iterrows():
        tabla.append({
            "id_indicador": str(row.get("_id", row.get(id_col, ""))) if id_col else None,
            "accion": str(row[accion_col]) if accion_col and pd.notna(row.get(accion_col)) else None,
            "estado": str(row[estado_col]) if estado_col and pd.notna(row.get(estado_col)) else None,
            "estado_tiempo": str(row[tiempo_col]) if tiempo_col and pd.notna(row.get(tiempo_col)) else None,
            "avance": _round_pct(row[avance_col]) if avance_col else None,
            "fecha_compromiso": str(row[fecha_col])[:10] if fecha_col and pd.notna(row.get(fecha_col)) else None,
            "responsable": str(row[resp_col]) if resp_col and pd.notna(row.get(resp_col)) else None,
        })

    return {
        "kpis": {
            "total": total,
            "cerradas": cerradas,
            "abiertas": abiertas,
            "avance_promedio": avance_prom,
            "vencidas": vencidas,
        },
        "avance_por_estado": avance_por_estado,
        "tabla": tabla,
    }


def build_filtros_cna(df: pd.DataFrame, catalog: pd.DataFrame, factor_sel: str | None = None) -> dict[str, Any]:
    factores = sorted(
        catalog["Factor"].dropna().astype(str).unique().tolist()
        if not catalog.empty
        else (df["Factor"].dropna().astype(str).unique().tolist() if "Factor" in df.columns else [])
    )
    if factor_sel and factor_sel != "Todos" and not catalog.empty:
        car_pool = catalog[catalog["Factor"] == factor_sel]
    elif factor_sel and factor_sel != "Todos" and "Factor" in df.columns:
        car_pool = df[df["Factor"] == factor_sel]
    else:
        car_pool = catalog if not catalog.empty else df
    caracts = sorted(car_pool["Caracteristica"].dropna().astype(str).unique().tolist()) if "Caracteristica" in car_pool.columns else []
    return {"factores": factores, "caracteristicas": caracts}
