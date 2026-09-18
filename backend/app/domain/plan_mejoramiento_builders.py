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
import time
from typing import Any

import pandas as pd

from app.core.ttl_cache import cache_get
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
# Desde el ajuste de fuentes 2026-09-18, el archivo trae dos hojas:
# "Indicadores Plan de Mejor" con las metas 2026-2030, y "Indicadores Real"
# con la ejecución y el % de cumplimiento 2025-2026 (ver load_plan_indicadores).
_SHEET_PLAN_INDICADORES = "Indicadores Plan de Mejor"
_SHEET_PLAN_REAL = "Indicadores Real"
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


def _clean(value):
    """None en vez de NaN — pd.DataFrame(list_of_dicts) convierte columnas con
    None mezclado a float64/NaN, y json.dumps no rechaza NaN (emite el
    literal no-estándar "NaN"), lo que rompe el parseo en el frontend."""
    return None if (value is None or (isinstance(value, float) and pd.isna(value))) else value


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


_PLAN_REAL_VALUE_COLS = ["Meta_2025", "Ejecucion_2025", "Cump_2025", "Ejecucion_2026", "Cump_2026"]
_PLAN_DESCRIPTIVO_COLS = [
    "Caracteristica", "Accion_Mejora", "Id_Kawak", "Tipo", "Observacion", "Estado_raw",
    "Estado_Aprobacion", "Formula", "Fuente", "Responsable", "Periodicidad",
]


def _load_plan_sheet(excel, sheet_name: str) -> pd.DataFrame:
    df = excel.read_excel(_PLAN_INDICADORES_PATH, sheet_name=sheet_name, header=1)
    df.columns = [str(c).replace("\n", " ").strip() for c in df.columns]
    df = df.rename(columns={k: v for k, v in _PLAN_RENAME.items() if k in df.columns})
    for col in ("Factor", "Indicador"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df


_plan_indicadores_cache: dict[int, tuple[float, pd.DataFrame]] = {}


def load_plan_indicadores(excel) -> pd.DataFrame:
    """Indicadores del Plan de Mejoramiento — paridad con
    plan_mejoramiento_loader.py::load_plan_indicadores.

    Tanto el dashboard (lista filtrada) como el detalle de un solo
    indicador (modal, get_indicador_detalle) llaman a esta función — sin
    caché, abrir el modal repetía todo el merge/derivación de columnas
    sobre el dataset completo. Se cachea con el mismo TTL que
    ExcelReaderService (mismo patrón que build_metricas_historico)."""
    cache_key = id(excel)
    cached = _plan_indicadores_cache.get(cache_key)
    if cached is not None:
        cached_at, cached_df = cached
        if time.time() - cached_at < getattr(excel, "ttl", 300):
            return cached_df.copy()

    df = _load_plan_indicadores_uncached(excel)
    _plan_indicadores_cache[cache_key] = (time.time(), df)
    return df.copy()


def _load_plan_indicadores_uncached(excel) -> pd.DataFrame:
    """Wide -> derivado: Meta|Ejecución|%Cump x 2025,2026 (+ metas futuras
    2026-2030), Factor_num/Factor_nombre, Estado_final, tiene_medicion,
    Cump_calc_2025/2026 (Ejecución/Meta, clip 1.3), y el catálogo
    Signo/Decimales/Decimales_Cump mergeado por Factor+Indicador.

    Desde el ajuste de fuentes 2026-09-18, las metas 2026-2030 viven en la
    hoja "Indicadores Plan de Mejor" y la ejecución/%cumplimiento 2025-2026
    en "Indicadores Real" — se combinan aquí por (Factor, Indicador)."""
    path = excel.data_root / _PLAN_INDICADORES_PATH
    if not path.exists():
        return pd.DataFrame()
    try:
        df = _load_plan_sheet(excel, _SHEET_PLAN_INDICADORES)
        df_real = _load_plan_sheet(excel, _SHEET_PLAN_REAL)
    except Exception:
        return pd.DataFrame()

    if "Factor" in df.columns and "Indicador" in df.columns and "Factor" in df_real.columns:
        real_cols = ["Factor", "Indicador"] + [c for c in _PLAN_REAL_VALUE_COLS if c in df_real.columns]
        df = df.merge(df_real[real_cols], on=["Factor", "Indicador"], how="outer", suffixes=("", "_real"))
        if "Meta_2025_real" in df.columns:
            df["Meta_2025"] = df["Meta_2025_real"] if "Meta_2025" not in df.columns else df["Meta_2025"].combine_first(df["Meta_2025_real"])
            df = df.drop(columns=["Meta_2025_real"])
        for col in _PLAN_DESCRIPTIVO_COLS:
            real_col = f"{col}_real"
            if real_col in df.columns:
                df[col] = df[real_col] if col not in df.columns else df[col].combine_first(df[real_col])
                df = df.drop(columns=[real_col])

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
    df: pd.DataFrame,
    *,
    factor: str | None = None,
    caracteristica: str | None = None,
    tipo: str | None = None,
    nombre: str | None = None,
) -> pd.DataFrame:
    out = df.copy()
    if factor and factor != "Todos" and "Factor" in out.columns:
        out = out[out["Factor"] == factor]
    if caracteristica and caracteristica != "Todas" and "Caracteristica" in out.columns:
        out = out[out["Caracteristica"] == caracteristica]
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
    """Filas de la sub-vista 'Metas 2026-2030' — todos los indicadores del
    filtro, incluidos los pendientes de meta (celdas en "—")."""
    sort_cols = [c for c in ("Factor_num",) if c in df.columns]
    rows_sorted = df.sort_values(sort_cols).reset_index(drop=True) if sort_cols else df

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
    """Filas de la sub-vista 'Cumplimiento histórico' — todos los indicadores
    del filtro, incluidos los pendientes de dato real (celdas en "—")."""
    sort_cols = [c for c in ("Factor_num",) if c in df.columns]
    rows_sorted = df.sort_values(sort_cols).reset_index(drop=True) if sort_cols else df

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
    "Ejecución", "Ejecución s", "Llave", "Decimales", "DecimalesEje", "Proyecto",
]

# Umbral para detectar que un indicador con signo "%" guarda la fracción
# cruda (0-1) en vez del valor ya escalado a 0-100 — validado contra
# data/output/Resultados_Consolidados_CNA.xlsx: todo indicador con signo "%"
# en la hoja Metricas guarda la fracción, salvo casos de datos de origen mal
# etiquetados (ver diagnóstico 2026-09-18).
_PCT_FRACCION_MAX = 1.5

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


def _detecta_escala_pct(signo: str | None, valores: list[float]) -> bool:
    """True si el indicador está en escala fracción (0-1) y debe escalarse
    x100 para mostrarse como porcentaje — ver _PCT_FRACCION_MAX arriba."""
    if signo != "%":
        return False
    vals = [v for v in valores if v is not None and pd.notna(v)]
    if not vals:
        return False
    return max(abs(v) for v in vals) <= _PCT_FRACCION_MAX


def _excluye_subtotal_fantasma(df: pd.DataFrame) -> pd.DataFrame:
    """Algunos indicadores traen, junto a las filas de desglose reales
    (p.ej. Presencial - Universitario, Virtual - Maestría, ...), una fila
    adicional con Subindicador vacío que es un subtotal parcial ya
    precalculado en el Excel fuente (p.ej. "Total Presencial" sin
    etiqueta propia). Si se deja mezclada, el desglose la muestra como si
    fuera una categoría más ("—") y la suma/promedio del grupo queda
    contaminada por un valor que ya está contenido en las demás filas —
    ver validación de negocio 2026-09-18 ("Matrícula de estudiantes" daba
    5.881 en vez de 58.398 real). Se excluye solo cuando el mismo
    Factor+Indicador tiene además ≥2 filas con Subindicador real: si el
    indicador no tiene desglose en absoluto, el Subindicador vacío es la
    métrica simple normal y se conserva."""
    if df.empty or "Subindicador" not in df.columns:
        return df
    grupo = df["Factor"].astype(str) + "" + df["Indicador"].astype(str)
    n_con_subindicador = df.groupby(grupo)["Subindicador"].transform(lambda s: s.notna().sum())
    es_subtotal_fantasma = df["Subindicador"].isna() & (n_con_subindicador >= 2)
    return df[~es_subtotal_fantasma]


_metricas_historico_cache: dict[int, tuple[float, pd.DataFrame]] = {}


def build_metricas_historico(excel) -> pd.DataFrame:
    """Una fila por (Factor, Característica, Indicador, Subindicador): serie
    anual completa + último valor + variaciones + tendencia — paridad con
    plan_mejoramiento_loader.py::build_metricas_historico.

    El groupby + loop en Python de más abajo es costoso sobre el histórico
    completo (se recorre una vez por cada combinación Factor/Característica/
    Indicador/Subindicador). Tanto la pestaña Métricas como el modal de
    detalle de una sola métrica llaman a esta función — sin caché, abrir un
    modal recalculaba todo el histórico desde cero (causa de las esperas de
    varios segundos / >30s reportadas). Se cachea con el mismo TTL que
    ExcelReaderService, para invalidarse junto con la lectura del Excel."""
    cache_key = id(excel)
    cached = _metricas_historico_cache.get(cache_key)
    if cached is not None:
        cached_at, cached_df = cached
        if time.time() - cached_at < getattr(excel, "ttl", 300):
            return cached_df.copy()

    df = _build_metricas_historico_uncached(excel)
    _metricas_historico_cache[cache_key] = (time.time(), df)
    return df.copy()


def _build_metricas_historico_uncached(excel) -> pd.DataFrame:
    df = load_metricas_raw(excel)
    if df.empty:
        return pd.DataFrame()
    df = _excluye_subtotal_fantasma(df)

    group_cols = ["Factor", "Factor_num", "Caracteristica", "Indicador", "Subindicador"]
    anual = df.sort_values(["Periodo_anio", "Periodo_sem"]).drop_duplicates(
        subset=group_cols + ["Periodo_anio"], keep="last"
    )

    rows = []
    for keys, grupo in anual.groupby(group_cols, dropna=False):
        grupo = grupo.sort_values("Periodo_anio")

        signo = grupo["Ejecución s"].dropna().iloc[-1] if not grupo["Ejecución s"].dropna().empty else None
        decimales = grupo["Decimales"].dropna().iloc[-1] if "Decimales" in grupo and not grupo["Decimales"].dropna().empty else _DECIMALES_DEFAULT
        pct_scale = _detecta_escala_pct(signo, grupo["Ejecucion_num"].tolist())
        factor_valor = 100.0 if pct_scale else 1.0

        con_anio = grupo[grupo["Periodo_anio"] != 9999]
        con_dato = con_anio.dropna(subset=["Ejecucion_num"])

        serie = [
            {
                "anio": int(anio),
                "ejecucion": None if pd.isna(ejec) else float(ejec) * factor_valor,
                "meta": None if pd.isna(meta) else float(meta) * factor_valor,
            }
            for anio, ejec, meta in zip(con_anio["Periodo_anio"], con_anio["Ejecucion_num"], con_anio["Meta_num"], strict=True)
            if pd.notna(anio)
        ]

        n_anios_con_dato = len(con_dato)
        if n_anios_con_dato:
            ultimo_anio = int(con_dato["Periodo_anio"].iloc[-1])
            ultimo_valor = float(con_dato["Ejecucion_num"].iloc[-1]) * factor_valor
        else:
            # Sin año real disponible: se conserva el último dato reportado
            # (si existe) para no perder la métrica del tablero.
            sin_anio_con_dato = grupo.dropna(subset=["Ejecucion_num"])
            ultimo_anio = None
            ultimo_valor = (
                float(sin_anio_con_dato["Ejecucion_num"].iloc[-1]) * factor_valor
                if not sin_anio_con_dato.empty
                else None
            )

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
                "signo": signo,
                "decimales": decimales,
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
    df: pd.DataFrame,
    *,
    factor: str | None = None,
    caracteristica: str | None = None,
    tendencia: str | None = None,
    nombre: str | None = None,
) -> pd.DataFrame:
    out = df.copy()
    if factor and factor != "Todos" and "Factor" in out.columns:
        out = out[out["Factor"] == factor]
    if caracteristica and caracteristica != "Todas" and "Caracteristica" in out.columns:
        out = out[out["Caracteristica"] == caracteristica]
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


def build_caracteristicas_cascade(df: pd.DataFrame, factor: str | None = None) -> list[str]:
    """Características disponibles, dependientes del Factor seleccionado —
    filtro en cascada compartido por Indicadores y Métricas (Factor y
    Característica son globales al módulo, no independientes por pestaña;
    ver docs/migration/PLAN_MIGRACION_PRIORIZADO.md)."""
    if df.empty or "Caracteristica" not in df.columns:
        return []
    pool = df
    if factor and factor != "Todos" and "Factor" in df.columns:
        pool = df[df["Factor"] == factor]
    return sorted(pool["Caracteristica"].dropna().unique().tolist())


def build_metricas_kpis(records: list[dict[str, Any]]) -> dict[str, Any]:
    """KPIs de la pestaña Métricas — calculados sobre la tabla ya agrupada por
    (Factor, Indicador) para que coincidan con lo que se cuenta en la tabla
    (ver build_metricas_tabla_agrupada; antes contaban filas por
    Subindicador, inflando el total muy por encima de las métricas
    realmente distintas)."""
    total = len(records)
    factores = {r["factor"] for r in records if r.get("factor")}
    n_creciente = sum(1 for r in records if r.get("tendencia") == "Creciente")
    n_decreciente = sum(1 for r in records if r.get("tendencia") == "Decreciente")
    return {
        "total": total,
        "factores_cubiertos": len(factores),
        "n_creciente": n_creciente,
        "n_decreciente": n_decreciente,
        "pct_creciente": round(n_creciente / total * 100) if total else 0,
        "pct_decreciente": round(n_decreciente / total * 100) if total else 0,
    }


def build_metricas_por_factor(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Conteo de métricas (por Indicador, no por Subindicador) por factor —
    insumo del gráfico clickable chart_metricas_por_factor (clic en un punto
    filtra la tabla)."""
    counts: dict[tuple[str | None, int | None], int] = {}
    for r in records:
        key = (r.get("factor"), r.get("factor_num"))
        counts[key] = counts.get(key, 0) + 1
    rows = [
        {"factor": factor, "factor_num": fnum, "cantidad": cantidad}
        for (factor, fnum), cantidad in counts.items()
    ]
    rows.sort(key=lambda r: (r["factor_num"] is None, r["factor_num"] or 0))
    return rows


def build_metricas_tabla(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Filas de la pestaña Métricas, incluida la serie para la columna
    sparkline (equivalente a st.column_config.LineChartColumn en el legacy)."""
    if df.empty:
        return []
    rows_sorted = df.sort_values("ultimo_anio", ascending=False, na_position="last").reset_index(drop=True)
    records = []
    for _, row in rows_sorted.iterrows():
        ind, sub = row.get("Indicador"), _clean(row.get("Subindicador"))
        fnum = row.get("Factor_num")
        tendencia = row.get("tendencia")
        ultimo_valor = _clean(row.get("ultimo_valor"))
        ultimo_anio = _clean(row.get("ultimo_anio"))
        records.append(
            {
                "factor": row.get("Factor"),
                "factor_num": None if pd.isna(fnum) else int(fnum),
                "metrica": ind if (not sub or sub == ind) else f"{ind} · {sub}",
                "indicador": ind,
                "subindicador": sub,
                "proceso": _clean(row.get("Proceso")),
                "ultimo_anio": int(ultimo_anio) if ultimo_anio is not None else None,
                "ultimo_valor": ultimo_valor,
                "valor_fmt": fmt_valor_plan(ultimo_valor, row.get("signo"), row.get("decimales")),
                "variacion_ultima_pct": _clean(row.get("variacion_ultima_pct")),
                "tendencia": tendencia if tendencia in ("Creciente", "Decreciente", "Estable") else "—",
                "serie": [p["ejecucion"] for p in row.get("serie", []) if p.get("ejecucion") is not None],
            }
        )
    return records


_TASA_SIGNOS = ("%", "%FRAC")


def _fila_desglose(row: pd.Series) -> dict[str, Any]:
    valor = _clean(row.get("ultimo_valor"))
    anio = _clean(row.get("ultimo_anio"))
    tendencia = row.get("tendencia")
    return {
        "subindicador": _clean(row.get("Subindicador")),
        "proceso": _clean(row.get("Proceso")),
        "ultimo_anio": int(anio) if anio is not None else None,
        "ultimo_valor": valor,
        "valor_fmt": fmt_valor_plan(valor, row.get("signo"), row.get("decimales")),
        "variacion_ultima_pct": _clean(row.get("variacion_ultima_pct")),
        "tendencia": tendencia if tendencia in ("Creciente", "Decreciente", "Estable") else "—",
        "serie": [p["ejecucion"] for p in row.get("serie", []) if p.get("ejecucion") is not None],
    }


def _agrega_filas(filas: list[dict[str, Any]], signo: str | None, decimales) -> dict[str, Any]:
    """Agrega un conjunto de filas homogéneas (mismo signo/decimales):
    promedio para tasas (%/%FRAC, no son sumables sin ponderar), suma para
    magnitudes aditivas (ENT/DEC, p.ej. conteos de estudiantes/profesores
    que se descomponen por categoría) — ver validación de negocio
    2026-09-18 ("Matrícula de estudiantes" debía sumar ~58.398, no
    promediar)."""
    valores = [f["ultimo_valor"] for f in filas if f["ultimo_valor"] is not None]
    valor = None
    if valores:
        valor = float(pd.Series(valores).mean()) if signo in _TASA_SIGNOS else float(pd.Series(valores).sum())
    anios = [f["ultimo_anio"] for f in filas if f["ultimo_anio"] is not None]
    variaciones = [f["variacion_ultima_pct"] for f in filas if f["variacion_ultima_pct"] is not None]
    tendencias = [f["tendencia"] for f in filas if f["tendencia"] != "—"]
    return {
        "ultimo_anio": max(anios) if anios else None,
        "ultimo_valor": valor,
        "valor_fmt": fmt_valor_plan(valor, signo, decimales),
        "variacion_ultima_pct": float(pd.Series(variaciones).mean()) if variaciones else None,
        "tendencia": pd.Series(tendencias).mode().iloc[0] if tendencias else "—",
    }


def _detecta_grupos_intermedios(grupo: pd.DataFrame, desglose: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    """Si el Subindicador sigue el patrón uniforme "Grupo - Hoja" en TODAS
    las filas con nombre (p.ej. "Presencial - Universitario",
    "Virtual - Maestría"), reconstruye el nivel intermedio real
    (Presencial/Virtual) que el Excel fuente sí tiene pero que el campo
    Subindicador aplana en un solo texto — ver validación de negocio
    2026-09-18. Si el patrón no es uniforme (categorías de una sola
    palabra, sin separador consistente, o un único grupo), no aplica y se
    deja el desglose plano de 2 niveles."""
    con_nombre = [d for d in desglose if d["subindicador"]]
    if len(con_nombre) < 2:
        return None

    partes = []
    for d in con_nombre:
        texto = d["subindicador"]
        if " - " not in texto:
            return None
        prefijo, _, sufijo = texto.partition(" - ")
        prefijo, sufijo = prefijo.strip(), sufijo.strip()
        if not prefijo or not sufijo:
            return None
        partes.append((prefijo, sufijo, d))

    prefijos = sorted({p for p, _, _ in partes})
    if len(prefijos) < 2 or len(prefijos) >= len(partes):
        return None

    # signo/decimales del subgrupo: todas sus hojas comparten unidad porque
    # ya se validó homogeneidad a nivel del indicador completo (homogeneo).
    signo_sub = grupo["signo"].iloc[0]
    decimales_sub = grupo["decimales"].iloc[0]

    grupos = []
    for prefijo in prefijos:
        hojas = [{**d, "subindicador": sufijo} for p, sufijo, d in partes if p == prefijo]
        agregado = _agrega_filas(hojas, signo_sub, decimales_sub)
        grupos.append({"nombre": prefijo, "n_hojas": len(hojas), "hojas": hojas, **agregado})

    grupos.sort(key=lambda g: (g["ultimo_anio"] is None, -(g["ultimo_anio"] or 0)))
    return grupos


def build_metricas_tabla_agrupada(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Filas de la pestaña Métricas agrupadas por (Factor, Indicador): una
    fila principal por indicador con un 'desglose' expandible por
    Subindicador — evita mostrar 10-60 filas repetidas para el mismo
    indicador cuando trae desglose por modalidad/cohorte/sede (ver
    diagnóstico 2026-09-18).

    El valor de la fila principal:
    - Indicador sin desglose real (1 solo Subindicador): se muestra el valor
      de ese único subindicador directamente.
    - Desglose homogéneo (mismo signo y decimales en todos los
      subindicadores): se agrega con _agrega_filas (suma o promedio según
      el signo).
    - Desglose heterogéneo (unidades mixtas, p.ej. conteos y porcentajes en
      el mismo indicador): no se inventa un agregado sin sentido — la fila
      principal solo indica cuántos subindicadores tiene y obliga a
      desplegar para ver el detalle real.

    Cuando el Subindicador sigue un patrón "Grupo - Hoja" uniforme, se
    agrega además un nivel intermedio real en 'grupos' (ver
    _detecta_grupos_intermedios); si no aplica, 'grupos' es None y el
    frontend usa 'desglose' (plano) directamente.
    """
    if df.empty:
        return []

    records = []
    for (factor, indicador), grupo in df.groupby(["Factor", "Indicador"], dropna=False):
        grupo = grupo.sort_values("ultimo_anio", ascending=False, na_position="last")
        fnum = grupo["Factor_num"].iloc[0]

        desglose = [_fila_desglose(row) for _, row in grupo.iterrows()]

        unidades = grupo[["signo", "decimales"]].drop_duplicates()
        homogeneo = len(unidades) <= 1
        grupos_intermedios = None

        if len(grupo) == 1:
            principal = desglose[0]
            agregado = {k: principal[k] for k in ("ultimo_anio", "ultimo_valor", "valor_fmt", "variacion_ultima_pct", "tendencia")}
            serie = principal["serie"]
        elif homogeneo:
            agregado = _agrega_filas(desglose, grupo["signo"].iloc[0], grupo["decimales"].iloc[0])
            serie = []
            grupos_intermedios = _detecta_grupos_intermedios(grupo, desglose)
        else:
            agregado = {"ultimo_anio": None, "ultimo_valor": None, "valor_fmt": "—", "variacion_ultima_pct": None, "tendencia": "—"}
            serie = []

        records.append(
            {
                "factor": factor,
                "factor_num": None if fnum is None or pd.isna(fnum) else int(fnum),
                "indicador": indicador,
                "proceso": grupo["Proceso"].dropna().iloc[-1] if not grupo["Proceso"].dropna().empty else None,
                **agregado,
                "serie": serie,
                "n_desglose": len(desglose),
                "desglose": desglose,
                "grupos": grupos_intermedios,
            }
        )

    records.sort(key=lambda r: (r["ultimo_anio"] is None, -(r["ultimo_anio"] or 0)))
    return records


_METRICAS_AGRUPADO_TOTAL_CACHE: dict[int, tuple[float, list]] = {}


def get_metricas_agrupado_total(excel) -> list[dict[str, Any]]:
    """Agrupado por (Factor, Indicador) sobre el histórico COMPLETO sin
    filtrar — insumo de los KPIs y el gráfico por factor de la pestaña
    Métricas (build_metricas_kpis/build_metricas_por_factor), que siempre
    reflejan el total sin importar los filtros de la tabla. Es idéntico en
    cada request (mismo excel), así que se cachea aparte del cálculo sobre
    la tabla ya filtrada (ese sí varía por request y el dataset es pequeño,
    no amerita caché)."""
    return cache_get(
        _METRICAS_AGRUPADO_TOTAL_CACHE,
        id(excel),
        lambda: build_metricas_tabla_agrupada(build_metricas_historico(excel)),
        ttl=getattr(excel, "ttl", 300),
    )


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
