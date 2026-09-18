"""Constructores Plan de Mejoramiento — paridad streamlit_app/pages/plan_mejoramiento.py.

Nota (2026-09-18): el legacy rediseñó este módulo como 2 pestañas planas
("Indicadores" / "Métricas") — ver services/plan_mejoramiento_loader.py y
streamlit_app/pages/plan_mejoramiento.py en Sistema_Indicadores_Poli. Las
funciones `build_kpis`/`build_graficos`/`build_tabla_cna`/`build_filtros_cna`
de arriba corresponden a un diseño ANTERIOR (tabla única por cierre) que ya
no refleja la UI real del legacy. Las funciones de las secciones
"PESTAÑA INDICADORES" y "PESTAÑA MÉTRICAS" más abajo son el puerto fiel del
diseño actual — ver docs/migration/PLAN_MIGRACION_PRIORIZADO.md ítem 0.
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from app.domain.loader_utils import find_col, id_a_str

CORTE_SEMESTRAL = {"Junio": 6, "Diciembre": 12}

# 2026 pertenece al siguiente ciclo del PDI y aun no tiene datos completos —
# se excluye de los filtros de anio por ahora (ver cmi_service.MAX_ANIO_FILTROS).
MAX_ANIO_FILTROS = 2025

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
    "#8dd3c7",
    "#ffffb3",
    "#bebada",
    "#fb8072",
    "#80b1d3",
    "#fdb462",
    "#b3de69",
    "#fccde5",
    "#d9d9d9",
    "#bc80bd",
    "#ccebc5",
    "#ffed6f",
    "#e41a1c",
    "#377eb8",
    "#4daf4a",
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
    return _estado_tiempo_acciones(df)


def _estado_tiempo_acciones(df: pd.DataFrame) -> pd.DataFrame:
    """Deriva Estado_Tiempo — paridad exacta con core/calculos.py:estado_tiempo_acciones."""
    df = df.copy()
    df["Estado_Tiempo"] = "A tiempo"
    if "DIAS_VENCIDA" in df.columns and "ESTADO" in df.columns:
        df.loc[df["DIAS_VENCIDA"] > 0, "Estado_Tiempo"] = "Vencida"
        df.loc[
            (df["DIAS_VENCIDA"] >= -30) & (df["DIAS_VENCIDA"] <= 0) & (df["ESTADO"] != "Cerrada"),
            "Estado_Tiempo",
        ] = "Por vencer"
        df.loc[df["ESTADO"] == "Cerrada", "Estado_Tiempo"] = "Cerrada"
    return df


def build_filtros_corte(cierres: pd.DataFrame) -> dict[str, Any]:
    anios = (
        sorted(
            a
            for a in pd.to_numeric(cierres["Anio"], errors="coerce")
            .dropna()
            .astype(int)
            .unique()
            .tolist()
            if a <= MAX_ANIO_FILTROS
        )
        if not cierres.empty and "Anio" in cierres.columns
        else []
    )
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
    if (
        caracteristica
        and caracteristica not in ("Todas", "Todos")
        and "Caracteristica" in out.columns
    ):
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
    prom = (
        float(df["cumplimiento_pct"].mean())
        if con_dato and "cumplimiento_pct" in df.columns
        else 0.0
    )
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

    factor_list = (
        sorted(df["Factor"].dropna().astype(str).unique().tolist())
        if "Factor" in df.columns
        else []
    )
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
            factor_bars.append(
                {
                    "factor": f,
                    "cumplimiento": _round_pct(row["cumplimiento_pct"]),
                    "color": color_map.get(f, "#888"),
                }
            )

    nivel_donut = []
    if "Nivel de cumplimiento" in df.columns:
        niveles = (
            df["Nivel de cumplimiento"].fillna("Pendiente de reporte").value_counts().reset_index()
        )
        niveles.columns = ["nivel", "cantidad"]
        for _, row in niveles.iterrows():
            n = str(row["nivel"])
            nivel_donut.append(
                {
                    "nivel": n,
                    "cantidad": int(row["cantidad"]),
                    "color": NIVEL_COLOR_EXT.get(n, "#BDBDBD"),
                    "emoji": NIVEL_EMOJI.get(n, "⚪"),
                }
            )

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
                niveles.append(
                    {
                        "nivel": n,
                        "cantidad": int(row["cantidad"]),
                        "color": NIVEL_COLOR_EXT.get(n, "#BDBDBD"),
                    }
                )
            factor_nivel_stacked.append(
                {"factor": factor, "niveles": niveles, "color": color_map.get(factor, "#888")}
            )

    treemap = []
    if "Factor" in df.columns and "Caracteristica" in df.columns:
        counts = (
            df.groupby(["Factor", "Caracteristica"], dropna=False)
            .size()
            .reset_index(name="cantidad")
        )
        for factor in factor_list:
            subset = counts[counts["Factor"].astype(str) == factor]
            children = []
            for _, row in subset.iterrows():
                children.append(
                    {
                        "caracteristica": str(row["Caracteristica"]),
                        "cantidad": int(row["cantidad"]),
                    }
                )
            treemap.append(
                {
                    "factor": factor,
                    "cantidad": int(subset["cantidad"].sum()),
                    "children": children,
                    "color": color_map.get(factor, "#888"),
                }
            )

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
        "Id",
        "Indicador",
        "Factor",
        "Caracteristica",
        "cumplimiento_pct",
        "Nivel de cumplimiento",
        "Meta",
        "Ejecucion",
        "Meta_Signo",
        "Ejecucion_s",
        "EjecS",
        "Decimales_Meta",
        "Decimales_Ejecucion",
        "Sentido",
        "Anio",
        "Mes",
        "Fecha",
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
    tiempo_col = find_col(df, ["Estado_Tiempo", "ESTADO_TIEMPO", "Estado tiempo", "Estado Tiempo"])
    fecha_col = find_col(df, ["FECHA_ESTIMADA_CIERRE", "Fecha compromiso", "Fecha estimada cierre"])
    resp_col = find_col(df, ["RESPONSABLE", "Responsable"])

    total = len(df)
    cerradas = 0
    abiertas = 0
    if estado_col:
        cerradas = int((df[estado_col].astype(str) == "Cerrada").sum())
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
            avance_por_estado.append(
                {
                    "estado": str(row[estado_col]),
                    "avance": _round_pct(row[avance_col]),
                }
            )

    tabla = []
    for _, row in df.head(500).iterrows():
        tabla.append(
            {
                "id_indicador": str(row.get("_id", row.get(id_col, ""))) if id_col else None,
                "accion": str(row[accion_col])
                if accion_col and pd.notna(row.get(accion_col))
                else None,
                "estado": str(row[estado_col])
                if estado_col and pd.notna(row.get(estado_col))
                else None,
                "estado_tiempo": str(row[tiempo_col])
                if tiempo_col and pd.notna(row.get(tiempo_col))
                else None,
                "avance": _round_pct(row[avance_col]) if avance_col else None,
                "fecha_compromiso": str(row[fecha_col])[:10]
                if fecha_col and pd.notna(row.get(fecha_col))
                else None,
                "responsable": str(row[resp_col])
                if resp_col and pd.notna(row.get(resp_col))
                else None,
            }
        )

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


def build_filtros_cna(
    df: pd.DataFrame, catalog: pd.DataFrame, factor_sel: str | None = None
) -> dict[str, Any]:
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
    caracts = (
        sorted(car_pool["Caracteristica"].dropna().astype(str).unique().tolist())
        if "Caracteristica" in car_pool.columns
        else []
    )
    return {"factores": factores, "caracteristicas": caracts}


# ═════════════════════════════════════════════════════════════════════════════
# PESTAÑA INDICADORES — Meta/Ejecución/%Cump 2025-2026 + metas futuras 2026-2030
# Paridad con Sistema_Indicadores_Poli/services/plan_mejoramiento_loader.py
# y streamlit_app/pages/plan_mejoramiento.py (ver PLAN_MIGRACION_PRIORIZADO.md ítem 0).
# ═════════════════════════════════════════════════════════════════════════════

_PLAN_INDICADORES_PATH = "raw/Plan de mejoramiento/Indicadores Plan de Mejoramiento.xlsx"
_SHEET_PLAN_INDICADORES = "Indicadores Plan de Mejor"
_CATALOGO_PLAN_PATH = "raw/Plan de mejoramiento/Catalogo_Indicadores_Plan_Mejoramiento.xlsx"
_SHEET_CATALOGO_PLAN = "Catalogo"

_SIGNO_DEFAULT = "DEC"
_DECIMALES_DEFAULT = 2
_DECIMALES_CUMP_DEFAULT = 1

_FACTOR_NUM_RE = re.compile(r"Factor\s+(\d+)", flags=re.IGNORECASE)

_PLAN_RENAME = {
    "FACTOR": "Factor",
    "CARACTERÍSTICA": "Caracteristica",
    "ACCIÓN DE MEJORA": "Accion_Mejora",
    "INDICADOR DE RESULTADO O IMPACTO": "Indicador",
    "ID Kawak": "Id_Kawak",
    "Indicador o Metrica": "Tipo",
    "Observación Desempeño": "Observacion",
    "Estado": "Estado_raw",
    "Estado de aprobación": "Estado_Aprobacion",
    "Fórmula": "Formula",
    "Fuente": "Fuente",
    "Responsable de la gestión": "Responsable",
    "PERIODICIDAD DE MEDICIÓN": "Periodicidad",
    "Meta 2025": "Meta_2025",
    "Ejecución 2025": "Ejecucion_2025",
    "% Cump 2025": "Cump_2025",
    "Meta 2026": "Meta_2026",
    "Ejecución 2026": "Ejecucion_2026",
    "% Cump 2026": "Cump_2026",
}

# "2026" ya llega renombrado a Meta_2026 (ver _PLAN_RENAME); solo 2027-2030
# son columnas de meta futura crudas en el Excel fuente.
_FUTURE_RAW_YEARS = ("2027", "2028", "2029", "2030")
_METAS_ALL_YEARS = ("2026", "2027", "2028", "2029", "2030")


def _factor_num(factor_label) -> int | None:
    match = _FACTOR_NUM_RE.search(str(factor_label or ""))
    return int(match.group(1)) if match else None


def _factor_nombre(factor_label) -> str:
    text = str(factor_label or "")
    return text.split(".", 1)[1].strip() if "." in text else text.strip()


def _parse_meta_ejecucion(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text or text.lower() in {"n/a", "na", "pendiente", "linea base", "línea base"}:
        return None
    text = text.replace("$", "").replace("%", "").replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def _or_default(value, default: str = "—") -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    text = str(value).strip()
    return text if text else default


def classify_plan_indicador_estado(row: pd.Series) -> str:
    """Activo/Aprobado/Pendiente — paridad exacta con
    plan_mejoramiento_loader.py::_classify_plan_estado.

    Activo:    Estado_Aprobacion=Aprobado AND Tipo=Indicador AND tiene medición
               numérica en 2025 o 2026.
    Aprobado:  Estado_Aprobacion=Aprobado pero sin medición aún.
    Pendiente: cualquier otro caso.
    """
    aprob = str(row.get("Estado_Aprobacion", "")).strip()
    tipo = str(row.get("Tipo", "")).strip()
    tiene_medicion = any(
        pd.notna(row.get(c)) for c in ["Meta_2025", "Ejecucion_2025", "Meta_2026", "Ejecucion_2026"]
    )
    if aprob == "Aprobado" and tipo == "Indicador" and tiene_medicion:
        return "Activo"
    if aprob == "Aprobado":
        return "Aprobado"
    return "Pendiente"


def fmt_valor_plan(value, signo, decimales) -> str:
    """Formatea Meta/Ejecución según el catálogo Signo/Decimales — paridad con
    plan_mejoramiento_utils.py::fmt_valor_plan.

    "%FRAC": el valor crudo es fracción 0-1 (0.95 = 95%) -> se escala x100.
    "%"/"ENT"/"DEC": el valor crudo ya está en su escala final de presentación.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    signo = str(signo or "").strip()
    try:
        decimales = int(decimales)
    except (TypeError, ValueError):
        decimales = _DECIMALES_DEFAULT
    value = float(value)
    if signo == "%FRAC":
        value *= 100
        signo = "%"
    if signo == "%":
        return f"{value:.{decimales}f}%"
    if signo == "ENT":
        return f"{value:,.0f}"
    return f"{value:,.{decimales}f}"


def load_catalogo_plan_indicadores(excel) -> pd.DataFrame:
    """Catálogo Signo/Decimales/Decimales_Cump por indicador del Plan.

    Es un borrador heurístico de negocio, revisado a mano (ver
    scripts/plan_mejoramiento/build_catalogo_indicadores.py en el legacy,
    y la nota de PLAN_MIGRACION_PRIORIZADO.md ítem 0 sobre su estado
    provisional). Vacío si el archivo no existe — load_plan_indicadores
    aplica el fallback DEC/2/1 en ese caso.
    """
    path = excel.data_root / _CATALOGO_PLAN_PATH
    empty = pd.DataFrame(columns=["Factor", "Indicador", "Signo", "Decimales", "Decimales_Cump"])
    if not path.exists():
        return empty
    try:
        df = excel.read_excel(_CATALOGO_PLAN_PATH, sheet_name=_SHEET_CATALOGO_PLAN)
    except Exception:
        return empty
    for col in ("Factor", "Indicador"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    cols = ["Factor", "Indicador", "Signo", "Decimales", "Decimales_Cump"]
    return df[[c for c in cols if c in df.columns]].drop_duplicates(subset=["Factor", "Indicador"])


def load_plan_indicadores(excel) -> pd.DataFrame:
    """Indicadores del Plan de Mejoramiento — paridad con
    plan_mejoramiento_loader.py::load_plan_indicadores.

    Wide -> derivado: Meta|Ejecución|%Cump x 2025,2026 (+ metas futuras
    2026-2030), Factor_num/Factor_nombre, Estado_final, tiene_medicion,
    Cump_calc_2025/2026 (Ejecución/Meta, clip 1.3), y el catálogo
    Signo/Decimales/Decimales_Cump mergeado por Factor+Indicador.
    """
    path = excel.data_root / _PLAN_INDICADORES_PATH
    if not path.exists():
        return pd.DataFrame()
    try:
        df = excel.read_excel(_PLAN_INDICADORES_PATH, sheet_name=_SHEET_PLAN_INDICADORES, header=1)
    except Exception:
        return pd.DataFrame()

    df.columns = [str(c).replace("\n", " ").strip() for c in df.columns]
    df = df.rename(columns={k: v for k, v in _PLAN_RENAME.items() if k in df.columns})

    for col in (
        "Factor", "Caracteristica", "Indicador", "Tipo", "Estado_raw", "Estado_Aprobacion", "Periodicidad",
    ):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    if "Factor" in df.columns:
        df["Factor_num"] = df["Factor"].map(_factor_num)
        df["Factor_nombre"] = df["Factor"].map(_factor_nombre)
    else:
        df["Factor_num"], df["Factor_nombre"] = None, None

    for year in ("2025", "2026"):
        for prefix in ("Meta", "Ejecucion", "Cump"):
            col = f"{prefix}_{year}"
            if col in df.columns:
                if prefix == "Cump":
                    df[f"{prefix}_num_{year}"] = df[col].apply(
                        lambda v: float(v) if isinstance(v, (int, float)) and pd.notna(v) else None
                    )
                else:
                    df[f"{prefix}_num_{year}"] = df[col].apply(_parse_meta_ejecucion)

    if "Meta_2026" in df.columns:
        df["Meta_num_2026"] = df["Meta_2026"].apply(_parse_meta_ejecucion)
    for year in _FUTURE_RAW_YEARS:
        if year in df.columns:
            df[f"Meta_num_{year}"] = df[year].apply(_parse_meta_ejecucion)

    if "Estado_raw" in df.columns and "Estado_Aprobacion" in df.columns:
        df["Estado_final"] = df.apply(classify_plan_indicador_estado, axis=1)
    elif "Estado_raw" in df.columns:
        df["Estado_final"] = df["Estado_raw"]
    else:
        df["Estado_final"] = "Sin estado"

    meta_ejec_cols = [f"Meta_num_{y}" for y in ("2025", "2026")] + [
        f"Ejecucion_num_{y}" for y in ("2025", "2026")
    ]
    existentes = [c for c in meta_ejec_cols if c in df.columns]
    df["tiene_medicion"] = df[existentes].notna().any(axis=1) if existentes else False

    for year in ("2025", "2026"):
        meta_col, ejec_col, cump_col = f"Meta_num_{year}", f"Ejecucion_num_{year}", f"Cump_calc_{year}"
        if meta_col in df.columns and ejec_col in df.columns:
            df[cump_col] = None
            mask = df[meta_col].notna() & df[ejec_col].notna() & (df[meta_col] != 0)
            df.loc[mask, cump_col] = (df.loc[mask, ejec_col] / df.loc[mask, meta_col]).clip(upper=1.3)
        else:
            df[cump_col] = None

    catalogo = load_catalogo_plan_indicadores(excel)
    if not catalogo.empty and "Factor" in df.columns and "Indicador" in df.columns:
        df = df.merge(catalogo, on=["Factor", "Indicador"], how="left")
    else:
        df["Signo"], df["Decimales"], df["Decimales_Cump"] = pd.NA, pd.NA, pd.NA
    df["Signo"] = df["Signo"].fillna(_SIGNO_DEFAULT)
    df["Decimales"] = pd.to_numeric(df["Decimales"], errors="coerce").fillna(_DECIMALES_DEFAULT).astype(int)
    df["Decimales_Cump"] = (
        pd.to_numeric(df["Decimales_Cump"], errors="coerce").fillna(_DECIMALES_CUMP_DEFAULT).astype(int)
    )

    sort_cols = [c for c in ("Factor_num", "Indicador") if c in df.columns]
    return df.sort_values(sort_cols).reset_index(drop=True) if sort_cols else df


def apply_plan_indicadores_filters(
    df: pd.DataFrame, *, factor: str | None = None, tipo: str | None = None, nombre: str | None = None
) -> pd.DataFrame:
    out = df.copy()
    if factor and factor != "Todos" and "Factor" in out.columns:
        out = out[out["Factor"] == factor]
    if tipo and tipo != "Todos" and "Tipo" in out.columns:
        out = out[out["Tipo"] == tipo]
    if nombre and nombre.strip():
        q = nombre.strip().lower()
        hay = (
            out.get("Indicador", pd.Series(dtype=str)).fillna("")
            + " "
            + out.get("Caracteristica", pd.Series(dtype=str)).fillna("")
            + " "
            + out.get("Accion_Mejora", pd.Series(dtype=str)).fillna("")
        ).str.lower()
        out = out[hay.str.contains(q, na=False, regex=False)]
    return out


def build_plan_indicadores_kpis(df: pd.DataFrame) -> dict[str, Any]:
    total = len(df)
    meta_cols = [f"Meta_num_{y}" for y in _METAS_ALL_YEARS]
    existentes = [c for c in meta_cols if c in df.columns]
    con_meta = int(df[existentes].notna().any(axis=1).sum()) if total and existentes else 0
    con_hist = (
        int((df["Cump_calc_2025"].notna() | df["Cump_calc_2026"].notna()).sum())
        if total and "Cump_calc_2025" in df.columns and "Cump_calc_2026" in df.columns
        else 0
    )
    aprobados = int((df.get("Estado_Aprobacion") == "Aprobado").sum()) if total else 0
    return {
        "total": total,
        "con_meta_futura": con_meta,
        "con_cumplimiento_historico": con_hist,
        "aprobados": aprobados,
        "pct_aprobados": round(aprobados / total * 100) if total else 0,
    }


def build_plan_indicadores_tabla_metas(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Filas de la sub-vista 'Metas 2026-2030' — solo indicadores con al menos
    una meta futura definida."""
    meta_cols = [f"Meta_num_{y}" for y in _METAS_ALL_YEARS]
    existentes = [c for c in meta_cols if c in df.columns]
    rows_view = df[df[existentes].notna().any(axis=1)] if existentes else df.iloc[0:0]
    sort_cols = [c for c in ("Factor_num",) if c in rows_view.columns]
    rows_sorted = rows_view.sort_values(sort_cols).reset_index(drop=True) if sort_cols else rows_view

    records = []
    for _, row in rows_sorted.iterrows():
        metas = {}
        for y in _METAS_ALL_YEARS:
            val = row.get(f"Meta_num_{y}")
            metas[y] = {
                "valor": None if pd.isna(val) else float(val),
                "valor_fmt": fmt_valor_plan(val, row.get("Signo"), row.get("Decimales")),
            }
        fnum = row.get("Factor_num")
        records.append(
            {
                "factor": row.get("Factor"),
                "factor_num": None if pd.isna(fnum) else int(fnum),
                "indicador": row.get("Indicador"),
                "tipo": row.get("Tipo"),
                "signo": row.get("Signo"),
                "metas": metas,
            }
        )
    return records


def build_plan_indicadores_tabla_historico(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Filas de la sub-vista 'Cumplimiento histórico' — solo indicadores con
    dato real (Cump_calc) en 2025 y/o 2026."""
    if "Cump_calc_2025" not in df.columns or "Cump_calc_2026" not in df.columns:
        return []
    rows_view = df[df["Cump_calc_2025"].notna() | df["Cump_calc_2026"].notna()]
    sort_cols = [c for c in ("Factor_num",) if c in rows_view.columns]
    rows_sorted = rows_view.sort_values(sort_cols).reset_index(drop=True) if sort_cols else rows_view

    def _valor(row, col, signo, decimales) -> dict[str, Any]:
        v = row.get(col)
        return {
            "valor": None if pd.isna(v) else float(v),
            "valor_fmt": fmt_valor_plan(v, signo, decimales),
        }

    def _cump(v, decimales_cump) -> dict[str, Any]:
        if pd.isna(v):
            return {"valor": None, "valor_fmt": "—"}
        pct = float(v) * 100
        dec = int(decimales_cump) if pd.notna(decimales_cump) else _DECIMALES_CUMP_DEFAULT
        return {"valor": round(pct, dec), "valor_fmt": f"{pct:.{dec}f}%"}

    records = []
    for _, row in rows_sorted.iterrows():
        signo, decimales, dec_cump = row.get("Signo"), row.get("Decimales"), row.get("Decimales_Cump")
        fnum = row.get("Factor_num")
        records.append(
            {
                "factor": row.get("Factor"),
                "factor_num": None if pd.isna(fnum) else int(fnum),
                "indicador": row.get("Indicador"),
                "meta_2025": _valor(row, "Meta_num_2025", signo, decimales),
                "ejecucion_2025": _valor(row, "Ejecucion_num_2025", signo, decimales),
                "cump_2025": _cump(row.get("Cump_calc_2025"), dec_cump),
                "meta_2026": _valor(row, "Meta_num_2026", signo, decimales),
                "ejecucion_2026": _valor(row, "Ejecucion_num_2026", signo, decimales),
                "cump_2026": _cump(row.get("Cump_calc_2026"), dec_cump),
            }
        )
    return records


def build_indicador_cump_texto(row: pd.Series) -> str:
    """Línea combinada 'Meta/Ejecución/%Cump — 2025 y 2026' del modal de
    detalle — paridad con plan_mejoramiento_utils.py::build_indicador_cump_texto."""
    signo, decimales, dec_cump = row.get("Signo"), row.get("Decimales"), row.get("Decimales_Cump")
    cump_2025, cump_2026 = row.get("Cump_calc_2025"), row.get("Cump_calc_2026")
    return (
        f"2025 — Meta: {fmt_valor_plan(row.get('Meta_num_2025'), signo, decimales)} · "
        f"Ejecución: {fmt_valor_plan(row.get('Ejecucion_num_2025'), signo, decimales)} · "
        f"% Cump: {fmt_valor_plan(cump_2025 * 100 if pd.notna(cump_2025) else None, '%', dec_cump)}"
        "   |   "
        f"2026 — Meta: {fmt_valor_plan(row.get('Meta_num_2026'), signo, decimales)} · "
        f"Ejecución: {fmt_valor_plan(row.get('Ejecucion_num_2026'), signo, decimales)} · "
        f"% Cump: {fmt_valor_plan(cump_2026 * 100 if pd.notna(cump_2026) else None, '%', dec_cump)}"
    )


def build_indicador_metas_futuras_texto(row: pd.Series) -> str:
    """Línea 'Metas 2026-2030' del modal de detalle — paridad con
    plan_mejoramiento_utils.py::build_indicador_metas_futuras_texto."""
    signo, decimales = row.get("Signo"), row.get("Decimales")
    partes = [f"{y}: {fmt_valor_plan(row.get(f'Meta_num_{y}'), signo, decimales)}" for y in _METAS_ALL_YEARS]
    return " · ".join(partes)


def build_indicador_detalle(row: pd.Series) -> dict[str, Any]:
    """Datos del modal de detalle de un indicador del Plan — paridad con
    pages/plan_mejoramiento.py::_open_indicador_modal."""
    return {
        "indicador": row.get("Indicador"),
        "factor": row.get("Factor"),
        "caracteristica": _or_default(row.get("Caracteristica")),
        "accion_mejora": _or_default(row.get("Accion_Mejora")),
        "tipo": row.get("Tipo"),
        "estado": _or_default(row.get("Estado_raw")),
        "estado_aprobacion": _or_default(row.get("Estado_Aprobacion")),
        "responsable": _or_default(row.get("Responsable")),
        "fuente": _or_default(row.get("Fuente")),
        "periodicidad": _or_default(row.get("Periodicidad"), "No definida"),
        "formula": _or_default(row.get("Formula"), "No registrada"),
        "observacion": _or_default(row.get("Observacion"), "Sin observaciones"),
        "cumplimiento_texto": build_indicador_cump_texto(row),
        "metas_futuras_texto": build_indicador_metas_futuras_texto(row),
    }


# ═════════════════════════════════════════════════════════════════════════════
# PESTAÑA MÉTRICAS — serie histórica anual CNA (Subindicador, tendencia, sparkline)
# Paridad con plan_mejoramiento_loader.py::build_metricas_historico y
# pages/plan_mejoramiento.py::_render_tab_metricas / _open_metrica_modal.
# ═════════════════════════════════════════════════════════════════════════════

_METRICAS_CNA_PATH = "output/Resultados_Consolidados_CNA.xlsx"
_SHEET_METRICAS = "Metricas"

_METRICAS_COLS = [
    "Id", "Indicador", "Subindicador", "Factor", "Caracteristica", "Proceso",
    "Periodicidad", "Sentido", "Fecha", "Año", "Mes", "Periodo", "Meta",
    "Ejecución", "Ejecución s", "Llave", "DecimalesEje", "Proyecto",
]

TENDENCIA_METRICAS_FILTRO_OPTIONS = ["Toda tendencia", "Creciente", "Decreciente", "Estable"]


def _parse_ejecucion_metrica(value, unidad: str) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("$", "").replace("%", "").replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def _split_periodo(periodo) -> tuple[int, int]:
    """'2019-1' -> (2019, 1). Valores inválidos ordenan al final."""
    try:
        anio_str, sem_str = str(periodo).split("-")
        return int(anio_str), int(sem_str)
    except (ValueError, AttributeError):
        return 9999, 9


def load_metricas_raw(excel) -> pd.DataFrame:
    """Hoja 'Metricas' del consolidado CNA, limpia y con columnas derivadas —
    paridad con plan_mejoramiento_loader.py::load_metricas_raw."""
    path = excel.data_root / _METRICAS_CNA_PATH
    empty = pd.DataFrame(columns=_METRICAS_COLS)
    if not path.exists():
        return empty
    try:
        df = excel.read_excel(_METRICAS_CNA_PATH, sheet_name=_SHEET_METRICAS)
    except Exception:
        return empty

    keep = [c for c in _METRICAS_COLS if c in df.columns]
    df = df[keep].copy()
    for col in (
        "Factor", "Caracteristica", "Indicador", "Subindicador", "Periodo", "Sentido", "Proceso", "Periodicidad",
    ):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    df["Factor_num"] = df["Factor"].map(_factor_num) if "Factor" in df.columns else None
    df["Factor_nombre"] = df["Factor"].map(_factor_nombre) if "Factor" in df.columns else None

    if "Periodo" in df.columns:
        periodo_split = df["Periodo"].map(_split_periodo)
        df["Periodo_anio"] = periodo_split.map(lambda t: t[0])
        df["Periodo_sem"] = periodo_split.map(lambda t: t[1])
    else:
        df["Periodo_anio"], df["Periodo_sem"] = None, None

    if "Ejecución" in df.columns:
        df["Ejecucion_num"] = [
            _parse_ejecucion_metrica(val, unidad)
            for val, unidad in zip(df["Ejecución"], df.get("Ejecución s", pd.Series(dtype=str)), strict=False)
        ]
    else:
        df["Ejecucion_num"] = None
    df["Meta_num"] = pd.to_numeric(df.get("Meta"), errors="coerce") if "Meta" in df.columns else None

    return df.sort_values(["Periodo_anio", "Periodo_sem"]).reset_index(drop=True)


def _classify_tendencia_historico(variacion_promedio_pct: float | None, n_anios_con_dato: int) -> str:
    """Paridad con plan_mejoramiento_loader.py::_classify_tendencia_historico:
    >+3% Creciente, <-3% Decreciente, si no Estable, "Sin suficiente historia"
    si hay menos de 2 años con dato."""
    if n_anios_con_dato < 2 or variacion_promedio_pct is None or pd.isna(variacion_promedio_pct):
        return "Sin suficiente historia"
    if variacion_promedio_pct > 3:
        return "Creciente"
    if variacion_promedio_pct < -3:
        return "Decreciente"
    return "Estable"


def build_metricas_historico(excel) -> pd.DataFrame:
    """Una fila por (Factor, Característica, Indicador, Subindicador): serie
    anual completa + último valor + variaciones + tendencia — paridad con
    plan_mejoramiento_loader.py::build_metricas_historico."""
    df = load_metricas_raw(excel)
    if df.empty:
        return pd.DataFrame()

    group_cols = ["Factor", "Factor_num", "Caracteristica", "Indicador", "Subindicador"]
    anual = df.sort_values(["Periodo_anio", "Periodo_sem"]).drop_duplicates(
        subset=group_cols + ["Periodo_anio"], keep="last"
    )

    rows = []
    for keys, grupo in anual.groupby(group_cols, dropna=False):
        grupo = grupo.sort_values("Periodo_anio")
        serie = [
            {
                "anio": int(anio),
                "ejecucion": None if pd.isna(ejec) else float(ejec),
                "meta": None if pd.isna(meta) else float(meta),
            }
            for anio, ejec, meta in zip(grupo["Periodo_anio"], grupo["Ejecucion_num"], grupo["Meta_num"], strict=True)
            if pd.notna(anio)
        ]

        con_dato = grupo.dropna(subset=["Ejecucion_num"])
        n_anios_con_dato = len(con_dato)
        ultimo_anio = int(con_dato["Periodo_anio"].iloc[-1]) if n_anios_con_dato else None
        ultimo_valor = float(con_dato["Ejecucion_num"].iloc[-1]) if n_anios_con_dato else None

        variacion_ultima_pct = None
        if n_anios_con_dato >= 2:
            previo = con_dato["Ejecucion_num"].iloc[-2]
            if pd.notna(previo) and previo != 0:
                variacion_ultima_pct = float((con_dato["Ejecucion_num"].iloc[-1] - previo) / previo * 100)

        variaciones = []
        valores_lista = con_dato["Ejecucion_num"].tolist()
        for i in range(1, len(valores_lista)):
            previo, actual = valores_lista[i - 1], valores_lista[i]
            if previo not in (0, None) and pd.notna(previo) and pd.notna(actual):
                variaciones.append((actual - previo) / previo * 100)
        variacion_promedio_pct = float(pd.Series(variaciones).mean()) if variaciones else None

        row = dict(zip(group_cols, keys, strict=True))
        row.update(
            {
                "Proceso": grupo["Proceso"].dropna().iloc[-1] if not grupo["Proceso"].dropna().empty else None,
                "Sentido": grupo["Sentido"].dropna().iloc[-1] if not grupo["Sentido"].dropna().empty else None,
                "Periodicidad": (
                    grupo["Periodicidad"].dropna().iloc[-1] if not grupo["Periodicidad"].dropna().empty else None
                ),
                "serie": serie,
                "ultimo_anio": ultimo_anio,
                "ultimo_valor": ultimo_valor,
                "variacion_ultima_pct": variacion_ultima_pct,
                "variacion_promedio_pct": variacion_promedio_pct,
                "n_anios_con_dato": n_anios_con_dato,
                "tendencia": _classify_tendencia_historico(variacion_promedio_pct, n_anios_con_dato),
            }
        )
        rows.append(row)

    return pd.DataFrame(rows).sort_values("Factor_num").reset_index(drop=True)


def apply_metricas_filters(
    df: pd.DataFrame, *, factor: str | None = None, tendencia: str | None = None, nombre: str | None = None
) -> pd.DataFrame:
    out = df.copy()
    if factor and factor != "Todos" and "Factor" in out.columns:
        out = out[out["Factor"] == factor]
    if tendencia and tendencia != "Toda tendencia" and "tendencia" in out.columns:
        out = out[out["tendencia"] == tendencia]
    if nombre and nombre.strip():
        q = nombre.strip().lower()
        hay = (
            out.get("Indicador", pd.Series(dtype=str)).fillna("")
            + " "
            + out.get("Subindicador", pd.Series(dtype=str)).fillna("")
        ).str.lower()
        out = out[hay.str.contains(q, na=False, regex=False)]
    return out


def build_metricas_kpis(df: pd.DataFrame) -> dict[str, Any]:
    total = len(df)
    n_factores = int(df["Factor"].nunique()) if total and "Factor" in df.columns else 0
    n_creciente = int((df["tendencia"] == "Creciente").sum()) if total and "tendencia" in df.columns else 0
    n_decreciente = int((df["tendencia"] == "Decreciente").sum()) if total and "tendencia" in df.columns else 0
    return {
        "total": total,
        "factores_cubiertos": n_factores,
        "n_creciente": n_creciente,
        "n_decreciente": n_decreciente,
        "pct_creciente": round(n_creciente / total * 100) if total else 0,
        "pct_decreciente": round(n_decreciente / total * 100) if total else 0,
    }


def build_metricas_por_factor(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Conteo de métricas con histórico por factor — insumo del gráfico
    clickable chart_metricas_por_factor (clic en un punto filtra la tabla)."""
    if df.empty or "Factor" not in df.columns:
        return []
    counts = df.groupby(["Factor", "Factor_num"], dropna=False).size().reset_index(name="cantidad")
    counts = counts.sort_values("Factor_num")
    return [
        {
            "factor": row["Factor"],
            "factor_num": None if pd.isna(row["Factor_num"]) else int(row["Factor_num"]),
            "cantidad": int(row["cantidad"]),
        }
        for _, row in counts.iterrows()
    ]


def build_metricas_tabla(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Filas de la pestaña Métricas, incluida la serie para la columna
    sparkline (equivalente a st.column_config.LineChartColumn en el legacy)."""
    if df.empty:
        return []
    rows_sorted = df.sort_values("ultimo_anio", ascending=False, na_position="last").reset_index(drop=True)
    records = []
    for _, row in rows_sorted.iterrows():
        ind, sub = row.get("Indicador"), row.get("Subindicador")
        fnum = row.get("Factor_num")
        tendencia = row.get("tendencia")
        records.append(
            {
                "factor": row.get("Factor"),
                "factor_num": None if pd.isna(fnum) else int(fnum),
                "metrica": ind if (not sub or sub == ind) else f"{ind} · {sub}",
                "indicador": ind,
                "subindicador": sub,
                "proceso": row.get("Proceso"),
                "ultimo_anio": row.get("ultimo_anio"),
                "ultimo_valor": row.get("ultimo_valor"),
                "variacion_ultima_pct": row.get("variacion_ultima_pct"),
                "tendencia": tendencia if tendencia in ("Creciente", "Decreciente", "Estable") else "—",
                "serie": [p["ejecucion"] for p in row.get("serie", []) if p.get("ejecucion") is not None],
            }
        )
    return records


def build_metrica_detalle(row: pd.Series) -> dict[str, Any]:
    """Datos del modal de detalle de una métrica — paridad con
    pages/plan_mejoramiento.py::_open_metrica_modal."""
    return {
        "indicador": row.get("Indicador"),
        "subindicador": row.get("Subindicador"),
        "factor": row.get("Factor"),
        "proceso": _or_default(row.get("Proceso")),
        "sentido": _or_default(row.get("Sentido")),
        "periodicidad": _or_default(row.get("Periodicidad")),
        "variacion_ultima_pct": row.get("variacion_ultima_pct"),
        "variacion_promedio_pct": row.get("variacion_promedio_pct"),
        "serie": row.get("serie", []),
    }
