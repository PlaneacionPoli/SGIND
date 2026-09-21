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

from app.domain.agregacion_anual import (
    IDS_SIN_TOTAL_GLOBAL,
    IDS_SUMA_SEMESTRAL,
    IDS_TOTAL_NO_APLICA,
)
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
        sort_factores(df["Factor"].dropna().astype(str).unique().tolist())
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
            elif isinstance(val, int | float):
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
    factores = sort_factores(
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

# Meta_2026 llega de la hoja "Indicadores Real" (columna "Meta 2026", ver
# _PLAN_REAL_VALUE_COLS); 2027-2030 son columnas de meta futura crudas
# ("2027".."2030") en la hoja "Indicadores Plan de Mejor".
_FUTURE_RAW_YEARS = ("2027", "2028", "2029", "2030")
_METAS_ALL_YEARS = ("2026", "2027", "2028", "2029", "2030")


def _factor_num(factor_label) -> int | None:
    match = _FACTOR_NUM_RE.search(str(factor_label or ""))
    return int(match.group(1)) if match else None


def sort_factores(factores) -> list[str]:
    """Factores en orden numérico (Factor 1, 2, … 12), no alfabético — el orden
    de texto pone "Factor 10" antes que "Factor 2". Etiquetas sin número, al final."""
    return sorted(
        factores,
        key=lambda f: (
            _factor_num(f) is None,
            _factor_num(f) or 0,
            str(f),
        ),
    )


def _factor_nombre(factor_label) -> str:
    text = str(factor_label or "")
    return text.split(".", 1)[1].strip() if "." in text else text.strip()


def _parse_meta_ejecucion(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, int | float):
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


def _num_es(value: float, decimales: int) -> str:
    """Formato colombiano: separador de miles "." y decimales ","."""
    texto = f"{value:,.{decimales}f}"
    return texto.translate(str.maketrans(",.", ".,"))


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
        return f"{_num_es(value, decimales)}%"
    if signo == "ENT":
        return _num_es(value, 0)
    return _num_es(value, decimales)


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


_PLAN_REAL_VALUE_COLS = [
    "Meta_2025",
    "Meta_2026",
    "Ejecucion_2025",
    "Cump_2025",
    "Ejecucion_2026",
    "Cump_2026",
]
_PLAN_DESCRIPTIVO_COLS = [
    "Caracteristica",
    "Accion_Mejora",
    "Id_Kawak",
    "Tipo",
    "Observacion",
    "Estado_raw",
    "Estado_Aprobacion",
    "Formula",
    "Fuente",
    "Responsable",
    "Periodicidad",
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
        real_cols = ["Factor", "Indicador"] + [
            c for c in (*_PLAN_REAL_VALUE_COLS, *_PLAN_DESCRIPTIVO_COLS) if c in df_real.columns
        ]
        # La hoja "Indicadores Plan de Mejor" es el maestro: un indicador que ya no
        # está allí no se lista aunque siga en "Indicadores Real".
        df = df.merge(
            df_real[real_cols], on=["Factor", "Indicador"], how="left", suffixes=("", "_real")
        )
        if "Meta_2025_real" in df.columns:
            df["Meta_2025"] = (
                df["Meta_2025_real"]
                if "Meta_2025" not in df.columns
                else df["Meta_2025"].combine_first(df["Meta_2025_real"])
            )
            df = df.drop(columns=["Meta_2025_real"])
        for col in _PLAN_DESCRIPTIVO_COLS:
            real_col = f"{col}_real"
            if real_col in df.columns:
                df[col] = (
                    df[real_col] if col not in df.columns else df[col].combine_first(df[real_col])
                )
                df = df.drop(columns=[real_col])

    for col in (
        "Factor",
        "Caracteristica",
        "Indicador",
        "Tipo",
        "Estado_raw",
        "Estado_Aprobacion",
        "Periodicidad",
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
                        lambda v: float(v) if isinstance(v, int | float) and pd.notna(v) else None
                    )
                else:
                    df[f"{prefix}_num_{year}"] = df[col].apply(_parse_meta_ejecucion)

    if "Meta_2026" in df.columns:
        df["Meta_num_2026"] = df["Meta_2026"].apply(_parse_meta_ejecucion)
        if "2026" in df.columns:
            df["Meta_num_2026"] = df["Meta_num_2026"].combine_first(
                df["2026"].apply(_parse_meta_ejecucion)
            )
    elif "2026" in df.columns:
        df["Meta_num_2026"] = df["2026"].apply(_parse_meta_ejecucion)
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
        meta_col, ejec_col, cump_col = (
            f"Meta_num_{year}",
            f"Ejecucion_num_{year}",
            f"Cump_calc_{year}",
        )
        if meta_col in df.columns and ejec_col in df.columns:
            df[cump_col] = None
            mask = df[meta_col].notna() & df[ejec_col].notna() & (df[meta_col] != 0)
            df.loc[mask, cump_col] = (df.loc[mask, ejec_col] / df.loc[mask, meta_col]).clip(
                upper=1.3
            )
        else:
            df[cump_col] = None

    catalogo = load_catalogo_plan_indicadores(excel)
    if not catalogo.empty and "Factor" in df.columns and "Indicador" in df.columns:
        df = df.merge(catalogo, on=["Factor", "Indicador"], how="left")
    else:
        df["Signo"], df["Decimales"], df["Decimales_Cump"] = pd.NA, pd.NA, pd.NA
    df["Signo"] = df["Signo"].fillna(_SIGNO_DEFAULT)
    df["Decimales"] = (
        pd.to_numeric(df["Decimales"], errors="coerce").fillna(_DECIMALES_DEFAULT).astype(int)
    )
    df["Decimales_Cump"] = (
        pd.to_numeric(df["Decimales_Cump"], errors="coerce")
        .fillna(_DECIMALES_CUMP_DEFAULT)
        .astype(int)
    )

    return sort_plan_indicadores(df)


_TIPO_ORDEN = {"Indicador": 0, "Pendiente": 1}


def sort_plan_indicadores(df: pd.DataFrame) -> pd.DataFrame:
    """Orden de la tabla: Tipo (Indicador, luego Pendiente, luego el resto),
    después Factor y nombre del indicador."""
    if df.empty:
        return df
    out = df.assign(
        _tipo_orden=df["Tipo"].map(_TIPO_ORDEN).fillna(len(_TIPO_ORDEN))
        if "Tipo" in df.columns
        else 0
    )
    sort_cols = ["_tipo_orden"] + [c for c in ("Factor_num", "Indicador") if c in df.columns]
    return out.sort_values(sort_cols).drop(columns="_tipo_orden").reset_index(drop=True)


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
    rows_sorted = sort_plan_indicadores(df)

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
    rows_sorted = sort_plan_indicadores(df)

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
        signo, decimales, dec_cump = (
            row.get("Signo"),
            row.get("Decimales"),
            row.get("Decimales_Cump"),
        )
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
    partes = [
        f"{y}: {fmt_valor_plan(row.get(f'Meta_num_{y}'), signo, decimales)}"
        for y in _METAS_ALL_YEARS
    ]
    return " · ".join(partes)


def build_indicador_cump_tabla(row: pd.Series) -> list[dict[str, str]]:
    """Filas (año, meta, ejecución, % cump) del modal de detalle, ya formateadas."""
    signo, decimales, dec_cump = row.get("Signo"), row.get("Decimales"), row.get("Decimales_Cump")
    filas = []
    for y in ("2025", "2026"):
        cump = row.get(f"Cump_calc_{y}")
        filas.append(
            {
                "anio": y,
                "meta": fmt_valor_plan(row.get(f"Meta_num_{y}"), signo, decimales),
                "ejecucion": fmt_valor_plan(row.get(f"Ejecucion_num_{y}"), signo, decimales),
                "cump": fmt_valor_plan(cump * 100 if pd.notna(cump) else None, "%", dec_cump),
            }
        )
    return filas


def build_indicador_metas_futuras_tabla(row: pd.Series) -> list[dict[str, str]]:
    """Filas (año, meta) 2026-2030 del modal de detalle, ya formateadas."""
    signo, decimales = row.get("Signo"), row.get("Decimales")
    return [
        {"anio": y, "meta": fmt_valor_plan(row.get(f"Meta_num_{y}"), signo, decimales)}
        for y in _METAS_ALL_YEARS
    ]


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
        "cumplimiento": build_indicador_cump_tabla(row),
        "metas_futuras": build_indicador_metas_futuras_tabla(row),
    }


# ═════════════════════════════════════════════════════════════════════════════
# PESTAÑA MÉTRICAS — serie histórica anual CNA (Subindicador, tendencia, sparkline)
# Paridad con plan_mejoramiento_loader.py::build_metricas_historico y
# pages/plan_mejoramiento.py::_render_tab_metricas / _open_metrica_modal.
# ═════════════════════════════════════════════════════════════════════════════

_METRICAS_CNA_PATH = "output/Resultados_Consolidados_CNA.xlsx"
_SHEET_METRICAS = "Metricas"

_METRICAS_COLS = [
    "Id",
    "Indicador",
    "Subindicador",
    "Factor",
    "Caracteristica",
    "Proceso",
    "Periodicidad",
    "Sentido",
    "Fecha",
    "Año",
    "Mes",
    "Periodo",
    "Meta",
    "Ejecución",
    "Ejecución s",
    "Llave",
    "Decimales",
    "DecimalesEje",
    "Proyecto",
    "Fuente",
    "Variable",
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
    if isinstance(value, int | float):
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


_PERIODO_RE = r"(?:19|20)\d{2}(?:-[12](?!\d))?"
_RANGO_FINAL = re.compile(
    rf"\s*(?:(?:entre|desde)\s+)?({_PERIODO_RE})[\s-]*(?:a|y|al|hasta)?[\s-]*({_PERIODO_RE})\s*$",
    re.IGNORECASE,
)
_HASTA_FINAL = re.compile(rf"\s+a\s+({_PERIODO_RE})\s*$", re.IGNORECASE)
_SEMESTRE_FINAL = re.compile(r"\s+((?:19|20)\d{2}-[12])\s*$")


def _limpia_rango_periodo(nombre) -> tuple[Any, str | None]:
    """Quita del final de un nombre de métrica el periodo de inicio y fin
    ("... 2019-2 a 2025-1", "... entre 2019-2025-1", "... a 2025-1") y lo
    devuelve aparte ("2019-2 a 2025-1"): el rango vive en la ficha, no en el
    nombre, que además quedaba desactualizado cuando la serie avanzaba. Solo
    actúa al final: en categorías como "2019-2020 - # Convenios" el año al
    inicio ES la etiqueta y no se toca."""
    if not isinstance(nombre, str):
        return nombre, None
    for patron in (_RANGO_FINAL, _HASTA_FINAL, _SEMESTRE_FINAL):
        m = patron.search(nombre)
        if m:
            limpio = re.sub(r"[\s\-–,]+$", "", nombre[: m.start()])
            limpio = re.sub(r"\s+(?:entre|desde)$", "", limpio, flags=re.IGNORECASE)
            return limpio, " a ".join(m.groups())
    return nombre, None


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
    # Posición original en el archivo: el orden de las categorías del desglose
    # (p.ej. PRESENCIAL - ..., VIRTUAL - ...) es el del Excel, no alfabético.
    df["Orden"] = range(len(df))
    for col in (
        "Factor",
        "Caracteristica",
        "Indicador",
        "Subindicador",
        "Periodo",
        "Sentido",
        "Proceso",
        "Fuente",
        "Periodicidad",
    ):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    df["Periodo_nombre"] = None
    for col in ("Indicador", "Subindicador"):
        if col in df.columns:
            limpios = df[col].map(_limpia_rango_periodo)
            df[col] = limpios.map(lambda t: t[0])
            df["Periodo_nombre"] = df["Periodo_nombre"].where(
                df["Periodo_nombre"].notna(), limpios.map(lambda t: t[1])
            )

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
            for val, unidad in zip(
                df["Ejecución"], df.get("Ejecución s", pd.Series(dtype=str)), strict=False
            )
        ]
    else:
        df["Ejecucion_num"] = None
    df["Meta_num"] = (
        pd.to_numeric(df.get("Meta"), errors="coerce") if "Meta" in df.columns else None
    )

    return df.sort_values(["Periodo_anio", "Periodo_sem"]).reset_index(drop=True)


def _variacion_pct(previo: float | None, actual: float | None) -> float | None:
    """Variación porcentual entre dos datos consecutivos. 0 -> 0 es 0% (sin
    cambio, no "sin dato"), para que series que caen a 0 y se mantienen
    sigan mostrando su variación; 0 -> N no tiene base de comparación."""
    if previo is None or actual is None or pd.isna(previo) or pd.isna(actual):
        return None
    if previo == 0:
        return 0.0 if actual == 0 else None
    return float((actual - previo) / previo * 100)


def _anota_variaciones(serie: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrega a cada punto `variacion_pct` respecto al dato anterior con valor."""
    previo = None
    for p in serie:
        p["variacion_pct"] = _variacion_pct(previo, p["ejecucion"])
        if p["ejecucion"] is not None:
            previo = p["ejecucion"]
    return serie


_UMBRAL_TENDENCIA_PCT = 3.0


def _tendencia_lineal(serie: list[dict[str, Any]]) -> str:
    """Tendencia de una serie anual según la pendiente de su recta de mínimos
    cuadrados (la misma "Tendencia (lineal)" que se dibuja en el gráfico),
    expresada como % del nivel promedio de la serie por año: >+3% Creciente,
    <-3% Decreciente, si no Estable; "Sin suficiente historia" con menos de 2
    datos.

    Antes se promediaban las variaciones año a año (paridad con el loader
    legacy), pero un solo salto porcentual enorme (65 -> 2.578 = +3.866%)
    dominaba el promedio y una serie que en conjunto baja salía "Creciente"."""
    puntos = [(i, p["ejecucion"]) for i, p in enumerate(serie) if p.get("ejecucion") is not None]
    if len(puntos) < 2:
        return "Sin suficiente historia"
    n = len(puntos)
    media_x = sum(x for x, _ in puntos) / n
    media_y = sum(y for _, y in puntos) / n
    sxx = sum((x - media_x) ** 2 for x, _ in puntos)
    nivel = sum(abs(y) for _, y in puntos) / n
    if sxx == 0 or nivel == 0:
        return "Estable"
    pendiente = sum((x - media_x) * (y - media_y) for x, y in puntos) / sxx
    pct_anual = pendiente / nivel * 100
    if pct_anual > _UMBRAL_TENDENCIA_PCT:
        return "Creciente"
    if pct_anual < -_UMBRAL_TENDENCIA_PCT:
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

    # Una sola categoría + fila sin Subindicador con los MISMOS valores por
    # periodo: es una copia (total sintético de versiones anteriores de la
    # extracción) y sumarla duplicaría el resultado. Si difiere, se conserva.
    una_sola = n_con_subindicador == 1
    for idx in df[una_sola].groupby(grupo[una_sola]).groups.values():
        bloque = df.loc[idx]
        con_sub = bloque[bloque["Subindicador"].notna()].set_index("Periodo")["Ejecucion_num"]
        sin_sub = bloque[bloque["Subindicador"].isna()]
        if sin_sub.empty:
            continue
        iguales = sin_sub.set_index("Periodo")["Ejecucion_num"].eq(con_sub.reindex(sin_sub["Periodo"]))
        if iguales.all():
            es_subtotal_fantasma.loc[sin_sub.index] = True
    return df[~es_subtotal_fantasma]


def _excluye_subtotales_de_grupo(df: pd.DataFrame) -> pd.DataFrame:
    """Tablas de 3 niveles (Total > Modalidad > Nivel, p.ej. Tabla 7 y 214): la
    hoja trae el subtotal de cada modalidad como una fila más, con el nombre
    del grupo repetido ("Virtual - Virtual"). Como fila de desglose el total
    del indicador contaba cada dato dos veces (13.064 en vez de 6.532).

    El subtotal se descarta solo si se valida contra los datos: repite su
    etiqueta, tiene hermanas en su grupo ("Virtual - ...") y en todos los
    periodos comparables su valor es igual a la suma de ellas. El nivel
    intermedio no se pierde: se reconstruye desde las hojas (ver
    _detecta_grupos_intermedios). Sin hermanas ("Cátedra - Cátedra") o si no
    suma, la fila se conserva."""
    if df.empty or "Subindicador" not in df.columns:
        return df

    def normaliza(texto: str) -> str:
        return " ".join(texto.split()).casefold()

    descartar: list[tuple[Any, Any, str]] = []
    for (factor, indicador), g in df.groupby(["Factor", "Indicador"], dropna=False):
        subs = [x for x in g["Subindicador"].dropna().unique() if isinstance(x, str)]
        candidatas = {}
        for sub in subs:
            partes = [normaliza(x) for x in sub.split(" - ")]
            if len(partes) >= 2 and partes[-1] == partes[-2]:
                candidatas[sub] = " - ".join(partes[:-1]) + " - "
        if not candidatas:
            continue
        piv = g.pivot_table(index="Periodo", columns="Subindicador", values="Ejecucion_num", aggfunc="last")
        for sub, prefijo in candidatas.items():
            hermanas = [
                c for c in piv.columns if c != sub and c not in candidatas and normaliza(c).startswith(prefijo)
            ]
            if not hermanas or sub not in piv.columns:
                continue
            suma = piv[hermanas].sum(axis=1, min_count=1)
            comparables = piv[sub].notna() & suma.notna()
            # El Excel redondea en millones: 124.322 + 337.600 = 461.922 vs 461.923.
            holgura = (suma.abs() * 1e-3).clip(lower=1e-9)
            if comparables.any() and ((piv[sub] - suma).abs() <= holgura)[comparables].all():
                descartar.append((factor, indicador, sub))
    if not descartar:
        return df
    marca = pd.Series(False, index=df.index)
    for factor, indicador, sub in descartar:
        marca |= (df["Factor"] == factor) & (df["Indicador"] == indicador) & (df["Subindicador"] == sub)
    return df[~marca]


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
    df = _excluye_subtotales_de_grupo(df)

    group_cols = ["Factor", "Factor_num", "Caracteristica", "Indicador", "Subindicador"]
    claves_anio = [*group_cols, "Periodo_anio"]
    anual = df.sort_values(["Periodo_anio", "Periodo_sem"]).drop_duplicates(subset=claves_anio, keep="last")
    # Indicadores de participación/actividad: el dato del año es la SUMA de sus
    # semestres, no solo el último (ver agregacion_anual.py).
    if "Id" in df.columns:
        suma_ids = df["Id"].astype(str).isin(IDS_SUMA_SEMESTRAL)
        if suma_ids.any():
            totales = (
                df[suma_ids]
                .groupby(claves_anio, dropna=False)[["Ejecucion_num", "Meta_num"]]
                .sum(min_count=1)
                .reset_index()
            )
            es_suma = anual["Id"].astype(str).isin(IDS_SUMA_SEMESTRAL)
            sumados = (
                anual[es_suma]
                .drop(columns=["Ejecucion_num", "Meta_num"])
                .merge(totales, on=claves_anio, how="left")
            )
            anual = pd.concat([anual[~es_suma], sumados], ignore_index=True)

    rows = []
    for keys, grupo in anual.groupby(group_cols, dropna=False):
        grupo = grupo.sort_values("Periodo_anio")

        signo = (
            grupo["Ejecución s"].dropna().iloc[-1]
            if not grupo["Ejecución s"].dropna().empty
            else None
        )
        decimales = (
            grupo["Decimales"].dropna().iloc[-1]
            if "Decimales" in grupo and not grupo["Decimales"].dropna().empty
            else _DECIMALES_DEFAULT
        )
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
            for anio, ejec, meta in zip(
                con_anio["Periodo_anio"],
                con_anio["Ejecucion_num"],
                con_anio["Meta_num"],
                strict=True,
            )
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

        _anota_variaciones(serie)
        con_variacion = [p for p in serie if p["ejecucion"] is not None]
        variacion_ultima_pct = con_variacion[-1]["variacion_pct"] if con_variacion else None
        variaciones = [
            p["variacion_pct"] for p in serie if p["variacion_pct"] is not None
        ]
        variacion_promedio_pct = float(pd.Series(variaciones).mean()) if variaciones else None

        row = dict(zip(group_cols, keys, strict=True))
        row.update(
            {
                "Proceso": grupo["Proceso"].dropna().iloc[-1]
                if not grupo["Proceso"].dropna().empty
                else None,
                "Fuente": _ultimo_texto(grupo.get("Fuente")),
                "Id": _ultimo_texto(grupo.get("Id")),
                "Es_variable": bool(grupo["Variable"].notna().any()) if "Variable" in grupo.columns else False,
                "Periodo_nombre": _ultimo_texto(grupo.get("Periodo_nombre")),
                "Sentido": grupo["Sentido"].dropna().iloc[-1]
                if not grupo["Sentido"].dropna().empty
                else None,
                "Periodicidad": (
                    grupo["Periodicidad"].dropna().iloc[-1]
                    if not grupo["Periodicidad"].dropna().empty
                    else None
                ),
                "signo": signo,
                "decimales": decimales,
                "orden": int(grupo["Orden"].min()),
                "serie": serie,
                "ultimo_anio": ultimo_anio,
                "ultimo_valor": ultimo_valor,
                "variacion_ultima_pct": variacion_ultima_pct,
                "variacion_promedio_pct": variacion_promedio_pct,
                "n_anios_con_dato": n_anios_con_dato,
                "tendencia": _tendencia_lineal(serie),
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
    (Factor, Indicador) y ya filtrada, para que coincidan con lo que se ve en
    la tabla (antes contaban filas por Subindicador, inflando el total muy
    por encima de las métricas realmente distintas). Incluye el conteo por
    tendencia."""
    total = len(records)
    factores = {r["factor"] for r in records if r.get("factor")}
    conteo = {
        t: sum(1 for r in records if r.get("tendencia") == t)
        for t in ("Creciente", "Estable", "Decreciente")
    }

    def pct(n: int) -> int:
        return round(n / total * 100) if total else 0

    return {
        "total": total,
        "factores_cubiertos": len(factores),
        "n_creciente": conteo["Creciente"],
        "n_estable": conteo["Estable"],
        "n_decreciente": conteo["Decreciente"],
        "n_sin_tendencia": total - sum(conteo.values()),
        "pct_creciente": pct(conteo["Creciente"]),
        "pct_estable": pct(conteo["Estable"]),
        "pct_decreciente": pct(conteo["Decreciente"]),
    }


def build_metricas_tabla(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Filas de la pestaña Métricas, incluida la serie para la columna
    sparkline (equivalente a st.column_config.LineChartColumn en el legacy)."""
    if df.empty:
        return []
    rows_sorted = df.sort_values("ultimo_anio", ascending=False, na_position="last").reset_index(
        drop=True
    )
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
                "fuente": _clean(row.get("Fuente")),
                "ultimo_anio": int(ultimo_anio) if ultimo_anio is not None else None,
                "ultimo_valor": ultimo_valor,
                "valor_fmt": fmt_valor_plan(ultimo_valor, row.get("signo"), row.get("decimales")),
                "variacion_ultima_pct": _clean(row.get("variacion_ultima_pct")),
                "tendencia": tendencia
                if tendencia in ("Creciente", "Decreciente", "Estable")
                else "—",
                "serie": [
                    p["ejecucion"] for p in row.get("serie", []) if p.get("ejecucion") is not None
                ],
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
        "fuente": _clean(row.get("Fuente")),
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
        valor = (
            float(pd.Series(valores).mean())
            if signo in _TASA_SIGNOS
            else float(pd.Series(valores).sum())
        )
    anios = [f["ultimo_anio"] for f in filas if f["ultimo_anio"] is not None]
    variaciones = [
        f["variacion_ultima_pct"] for f in filas if f["variacion_ultima_pct"] is not None
    ]
    tendencias = [f["tendencia"] for f in filas if f["tendencia"] != "—"]
    return {
        "ultimo_anio": max(anios) if anios else None,
        "ultimo_valor": valor,
        "valor_fmt": fmt_valor_plan(valor, signo, decimales),
        "variacion_ultima_pct": float(pd.Series(variaciones).mean()) if variaciones else None,
        "tendencia": pd.Series(tendencias).mode().iloc[0] if tendencias else "—",
    }


def _agrega_series(filas: pd.DataFrame, signo: str | None) -> list[dict[str, Any]]:
    """Serie anual del consolidado: por cada año, suma (magnitudes) o
    promedio (tasas) de las series de todas las categorías del desglose —
    misma regla de agregación que _agrega_filas, pero año a año, para poder
    graficar el consolidado y calcular su variación y tendencia."""
    por_anio: dict[int, dict[str, list[float]]] = {}
    for serie in filas["serie"]:
        for p in serie:
            slot = por_anio.setdefault(p["anio"], {"ejecucion": [], "meta": []})
            for campo in ("ejecucion", "meta"):
                if p.get(campo) is not None:
                    slot[campo].append(p[campo])

    def combina(valores: list[float]) -> float | None:
        if not valores:
            return None
        return sum(valores) / len(valores) if signo in _TASA_SIGNOS else float(sum(valores))

    return _anota_variaciones(
        [
            {"anio": anio, "ejecucion": combina(s["ejecucion"]), "meta": combina(s["meta"])}
            for anio, s in sorted(por_anio.items())
        ]
    )


def _estadisticas_serie(serie: list[dict[str, Any]]) -> dict[str, Any]:
    """Último dato, variaciones y tendencia de una serie anual — misma
    lógica que _build_metricas_historico_uncached, aplicada a series ya
    construidas (consolidados)."""
    con_dato = [p for p in serie if p.get("ejecucion") is not None]
    variaciones = [p["variacion_pct"] for p in serie if p.get("variacion_pct") is not None]
    variacion_ultima = con_dato[-1].get("variacion_pct") if con_dato else None
    variacion_promedio = sum(variaciones) / len(variaciones) if variaciones else None
    return {
        "ultimo_anio": con_dato[-1]["anio"] if con_dato else None,
        "ultimo_valor": con_dato[-1]["ejecucion"] if con_dato else None,
        "variacion_ultima_pct": variacion_ultima,
        "variacion_promedio_pct": variacion_promedio,
        "tendencia": _tendencia_lineal(serie),
    }


def _partes_grupo(subindicadores: list[str | None]) -> list[tuple[int, str, str]] | None:
    """(posición, grupo, hoja) si el Subindicador sigue el patrón uniforme
    "Grupo - Hoja" en TODAS las filas con nombre y hay al menos dos grupos con
    varias hojas; si no, None (categorías de una sola palabra, sin separador
    consistente, o un único grupo)."""
    partes: list[tuple[int, str, str]] = []
    for i, texto in enumerate(subindicadores):
        if not texto:
            continue
        if " - " not in texto:
            return None
        prefijo, _, sufijo = texto.partition(" - ")
        prefijo, sufijo = prefijo.strip(), sufijo.strip()
        if not prefijo or not sufijo:
            return None
        partes.append((i, prefijo, sufijo))
    prefijos = {p for _, p, _ in partes}
    if len(partes) < 2 or len(prefijos) < 2 or len(prefijos) >= len(partes):
        return None
    return partes


def _agregado_serie(serie: list[dict[str, Any]], signo: str | None, decimales) -> dict[str, Any] | None:
    """Campos de la fila principal a partir de una serie anual ya agregada
    (None si la serie no trae ningún dato)."""
    est = _estadisticas_serie(serie)
    if est["ultimo_valor"] is None:
        return None
    return {
        "ultimo_anio": est["ultimo_anio"],
        "ultimo_valor": est["ultimo_valor"],
        "valor_fmt": fmt_valor_plan(est["ultimo_valor"], signo, decimales),
        "variacion_ultima_pct": est["variacion_ultima_pct"],
        "tendencia": _tendencia_visible(est["tendencia"]),
    }


def _id_no_aplica(df: pd.DataFrame) -> bool:
    """Ítems de naturaleza distinta: el total no se suma y se muestra "No aplica"."""
    return "Id" in df.columns and bool(df["Id"].astype(str).isin(IDS_TOTAL_NO_APLICA).any())


def _id_sin_total_global(df: pd.DataFrame) -> bool:
    return "Id" in df.columns and bool(df["Id"].astype(str).isin(IDS_SIN_TOTAL_GLOBAL).any())


def _es_total_sub(sub: Any) -> bool:
    return isinstance(sub, str) and sub.split(" - ")[0].strip().casefold() == "total"


def _es_tabla_de_variables(df: pd.DataFrame) -> bool:
    """Tablas con subvariables (Títulos/Volúmenes, Tabla 40): cada fila del
    histórico es ÁREA - variable y las variables no se suman entre sí."""
    return "Es_variable" in df.columns and len(df) > 1 and bool(df["Es_variable"].fillna(False).astype(bool).all())


def _agregado_variables(hojas: list[dict[str, Any]]) -> dict[str, Any]:
    """Fila de un grupo/total con subvariables: el valor muestra todas
    ("Títulos: 1.844 · Volúmenes: 5.366"); serie, variación y tendencia son las
    de la primera variable."""
    if not hojas:
        return {
            "ultimo_anio": None,
            "ultimo_valor": None,
            "valor_fmt": "—",
            "variacion_ultima_pct": None,
            "tendencia": "—",
            "serie": [],
        }
    primera = hojas[0]
    anios = [h["ultimo_anio"] for h in hojas if h["ultimo_anio"] is not None]
    return {
        "ultimo_anio": max(anios) if anios else None,
        "ultimo_valor": primera["ultimo_valor"],
        "valor_fmt": " · ".join(f"{h['subindicador']}: {h['valor_fmt']}" for h in hojas),
        "variacion_ultima_pct": primera["variacion_ultima_pct"],
        "tendencia": primera["tendencia"],
        "serie": primera["serie"],
    }


def _fila_variables(
    factor: Any, fnum: Any, indicador: Any, grupo: pd.DataFrame, desglose: list[dict[str, Any]]
) -> dict[str, Any]:
    """Registro de la tabla para un indicador con subvariables: la fila
    principal es el TOTAL, las áreas son el nivel 2 y sus variables el nivel 3."""
    totales, areas = [], []
    for d in desglose:
        sub = d["subindicador"] or ""
        prefijo, _, variable = sub.rpartition(" - ")
        (totales if _es_total_sub(sub) else areas).append((prefijo or sub, {**d, "subindicador": variable or sub}))
    grupos = []
    for nombre in dict.fromkeys(pref for pref, _ in areas):
        hojas = [h for pref, h in areas if pref == nombre]
        grupos.append({"nombre": nombre, "n_hojas": len(hojas), "hojas": hojas, **_agregado_variables(hojas)})
    return {
        "factor": factor,
        "factor_num": None if fnum is None or pd.isna(fnum) else int(fnum),
        "indicador": indicador,
        "fuente": _ultimo_texto(grupo["Fuente"]) if "Fuente" in grupo.columns else None,
        **_agregado_variables([h for _, h in totales]),
        "n_desglose": len(areas),
        "desglose": [d for d in desglose if not _es_total_sub(d["subindicador"])],
        "grupos": grupos or None,
    }


def _detecta_grupos_intermedios(
    grupo: pd.DataFrame, desglose: list[dict[str, Any]]
) -> list[dict[str, Any]] | None:
    """Reconstruye el nivel intermedio real (Presencial/Virtual) que el Excel
    fuente sí tiene pero que el campo Subindicador aplana en "Grupo - Hoja" —
    ver validación de negocio 2026-09-18. Cada grupo trae su propio total,
    serie y tendencia, calculados desde sus hojas (que coinciden con el
    subtotal de la hoja: ver _excluye_subtotales_de_grupo)."""
    partes = _partes_grupo([d["subindicador"] for d in desglose])
    if partes is None:
        return None

    # signo/decimales del subgrupo: todas sus hojas comparten unidad porque
    # ya se validó homogeneidad a nivel del indicador completo (homogeneo).
    signo_sub = grupo["signo"].iloc[0]
    decimales_sub = grupo["decimales"].iloc[0]

    grupos = []
    for prefijo in dict.fromkeys(p for _, p, _ in partes):  # orden de aparición
        items = [(i, sufijo) for i, p, sufijo in partes if p == prefijo]
        hojas = [{**desglose[i], "subindicador": sufijo} for i, sufijo in items]
        serie = _agrega_series(grupo.iloc[[i for i, _ in items]], signo_sub)
        agregado = _agregado_serie(serie, signo_sub, decimales_sub) or _agrega_filas(
            hojas, signo_sub, decimales_sub
        )
        grupos.append(
            {
                "nombre": prefijo,
                "n_hojas": len(hojas),
                "hojas": hojas,
                **agregado,
                "serie": [p["ejecucion"] for p in serie if p["ejecucion"] is not None],
            }
        )
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
        grupo = grupo.sort_values("orden")  # orden del archivo fuente
        fnum = grupo["Factor_num"].iloc[0]

        desglose = [_fila_desglose(row) for _, row in grupo.iterrows()]
        if _es_tabla_de_variables(grupo):
            records.append(_fila_variables(factor, fnum, indicador, grupo, desglose))
            continue

        unidades = grupo[["signo", "decimales"]].drop_duplicates()
        homogeneo = len(unidades) <= 1 and not _id_no_aplica(grupo)
        grupos_intermedios = None

        if len(grupo) == 1:
            principal = desglose[0]
            agregado = {
                k: principal[k]
                for k in (
                    "ultimo_anio",
                    "ultimo_valor",
                    "valor_fmt",
                    "variacion_ultima_pct",
                    "tendencia",
                )
            }
            serie = principal["serie"]
        elif homogeneo:
            signo, decimales = grupo["signo"].iloc[0], grupo["decimales"].iloc[0]
            serie_agregada = _agrega_series(grupo, signo)
            # Sin serie anual (Periodo vacío en el Excel): último dato de cada categoría.
            agregado = _agregado_serie(serie_agregada, signo, decimales) or _agrega_filas(
                desglose, signo, decimales
            )
            serie = [p["ejecucion"] for p in serie_agregada if p["ejecucion"] is not None]
            grupos_intermedios = _detecta_grupos_intermedios(grupo, desglose)
            if grupos_intermedios and _id_sin_total_global(grupo):
                # Activos = Pasivos + Patrimonio: la fila principal muestra cada grupo.
                agregado = _agregado_variables([{**g, "subindicador": g["nombre"]} for g in grupos_intermedios])
                serie = agregado.pop("serie")
        else:
            # Unidades mezcladas o ítems distintos: no se inventa un total.
            agregado = {
                "ultimo_anio": None,
                "ultimo_valor": None,
                "valor_fmt": "No aplica",
                "variacion_ultima_pct": None,
                "tendencia": "—",
            }
            serie = []

        records.append(
            {
                "factor": factor,
                "factor_num": None if fnum is None or pd.isna(fnum) else int(fnum),
                "indicador": indicador,
                "fuente": _ultimo_texto(grupo["Fuente"]) if "Fuente" in grupo.columns else None,
                **agregado,
                "serie": serie,
                "n_desglose": len(desglose),
                "desglose": desglose,
                "grupos": grupos_intermedios,
            }
        )

    records.sort(key=lambda r: (r["ultimo_anio"] is None, -(r["ultimo_anio"] or 0)))
    return records


def _ultimo_texto(serie: pd.Series | None) -> str | None:
    """Último valor no vacío de una columna de texto (None si no hay)."""
    if serie is None:
        return None
    vals = [v for v in serie.dropna().astype(str).str.strip() if v and v.lower() != "nan"]
    return vals[-1] if vals else None


def _int_o_none(value) -> int | None:
    value = _clean(value)
    return None if value is None else int(value)


def _tendencia_visible(tendencia: str | None) -> str:
    return tendencia if tendencia in ("Creciente", "Decreciente", "Estable") else "—"


def _rango_anios(serie: list[dict[str, Any]], texto_nombre: str | None) -> dict[str, Any]:
    """Año de inicio y fin de la serie (para la ficha); si no hay serie anual
    (tablas sin periodo) se usa el periodo que traía el nombre."""
    anios = [p["anio"] for p in serie if p.get("ejecucion") is not None]
    return {
        "anio_inicio": min(anios) if anios else None,
        "anio_fin": max(anios) if anios else None,
        "periodo_texto": texto_nombre,
    }


def _detalle_variables(base: dict[str, Any], match: pd.DataFrame, grupo: str | None) -> dict[str, Any]:
    """Ficha de un total o de un grupo con subvariables (Títulos/Volúmenes):
    cada variable con su propio valor, variación, tendencia y serie."""
    es_total = match["Subindicador"].map(_es_total_sub)
    filas = match if grupo is not None else match[es_total]
    resto = match.iloc[0:0] if grupo is not None else match[~es_total]

    def datos(row: pd.Series) -> dict[str, Any]:
        return {
            "subindicador": _clean(row.get("Subindicador")),
            "nombre": str(row.get("Subindicador")).rpartition(" - ")[2],
            "valor_fmt": fmt_valor_plan(_clean(row.get("ultimo_valor")), row.get("signo"), row.get("decimales")),
            "ultimo_anio": _int_o_none(row.get("ultimo_anio")),
            "variacion_ultima_pct": _clean(row.get("variacion_ultima_pct")),
            "variacion_promedio_pct": _clean(row.get("variacion_promedio_pct")),
            "tendencia": _tendencia_visible(row.get("tendencia")),
            "serie": row.get("serie", []),
        }

    variables = [datos(r) for _, r in filas.iterrows()]
    primera = variables[0] if variables else {}
    anios = [v["ultimo_anio"] for v in variables if v["ultimo_anio"] is not None]
    referencia = filas.iloc[0] if not filas.empty else match.iloc[0]
    return {
        **base,
        "subindicador": grupo,
        "consolidado": True,
        "agregacion": None,
        "signo": _clean(referencia.get("signo")),
        "decimales": _int_o_none(referencia.get("decimales")),
        "ultimo_anio": max(anios) if anios else None,
        "ultimo_valor": primera.get("ultimo_valor"),
        "valor_fmt": " · ".join(f"{v['nombre']}: {v['valor_fmt']}" for v in variables) or "—",
        "tendencia": primera.get("tendencia", "—"),
        "variacion_ultima_pct": primera.get("variacion_ultima_pct"),
        "variacion_promedio_pct": primera.get("variacion_promedio_pct"),
        "serie": primera.get("serie", []),
        **_rango_anios([p for v in variables for p in v["serie"]], _ultimo_texto(match.get("Periodo_nombre"))),
        "variables": variables,
        "desglose": [datos(r) for _, r in resto.iterrows()],
        "grupos": None,
    }


def build_metrica_detalle(
    match: pd.DataFrame, *, consolidado: bool = False, grupo: str | None = None
) -> dict[str, Any]:
    """Datos del modal de detalle de una métrica — paridad con
    pages/plan_mejoramiento.py::_open_metrica_modal.

    `match` trae las filas del histórico del indicador. Con consolidado=True
    (indicador con desglose y sin subindicador elegido) la ficha muestra el
    total (o promedio, si son tasas) año a año de todas las categorías, y
    el desglose de cada una en el orden del archivo. Si las categorías
    mezclan unidades no hay agregado con sentido: solo se lista el desglose."""
    match = match.sort_values("orden")
    first = match.iloc[0]
    base = {
        "indicador": first.get("Indicador"),
        "factor": first.get("Factor"),
        "fuente": _or_default(first.get("Fuente")),
        "sentido": _or_default(first.get("Sentido")),
        "periodicidad": _or_default(first.get("Periodicidad")),
    }

    if not consolidado:
        return {
            **base,
            "subindicador": first.get("Subindicador"),
            "consolidado": False,
            "agregacion": None,
            "signo": _clean(first.get("signo")),
            "decimales": _int_o_none(first.get("decimales")),
            "ultimo_anio": _int_o_none(first.get("ultimo_anio")),
            "ultimo_valor": _clean(first.get("ultimo_valor")),
            "valor_fmt": fmt_valor_plan(
                _clean(first.get("ultimo_valor")), first.get("signo"), first.get("decimales")
            ),
            "tendencia": _tendencia_visible(first.get("tendencia")),
            "variacion_ultima_pct": _clean(first.get("variacion_ultima_pct")),
            "variacion_promedio_pct": _clean(first.get("variacion_promedio_pct")),
            "serie": first.get("serie", []),
            **_rango_anios(first.get("serie", []), _ultimo_texto(match.get("Periodo_nombre"))),
            "desglose": [],
            "grupos": None,
        }

    if _es_tabla_de_variables(match):
        return _detalle_variables(base, match, grupo)

    unidades = match[["signo", "decimales"]].drop_duplicates()
    signo, decimales = first["signo"], first["decimales"]
    desglose = [
        {
            "subindicador": _clean(row.get("Subindicador")),
            "valor_fmt": fmt_valor_plan(
                _clean(row.get("ultimo_valor")), row.get("signo"), row.get("decimales")
            ),
            "ultimo_anio": _int_o_none(row.get("ultimo_anio")),
            "variacion_ultima_pct": _clean(row.get("variacion_ultima_pct")),
            "tendencia": _tendencia_visible(row.get("tendencia")),
            "serie": row.get("serie", []),
        }
        for _, row in match.iterrows()
    ]
    serie: list[dict[str, Any]] = []
    est: dict[str, Any] = {}
    grupos: list[dict[str, Any]] | None = None
    if len(unidades) <= 1 and not _id_no_aplica(match):
        serie = _agrega_series(match, signo)
        est = _estadisticas_serie(serie)
        partes = _partes_grupo([d["subindicador"] for d in desglose])
        if partes is not None:
            grupos = []
            for prefijo in dict.fromkeys(p for _, p, _ in partes):
                posiciones = [i for i, p, _ in partes if p == prefijo]
                serie_g = _agrega_series(match.iloc[posiciones], signo)
                est_g = _estadisticas_serie(serie_g)
                grupos.append(
                    {
                        "nombre": prefijo,
                        "valor_fmt": fmt_valor_plan(est_g["ultimo_valor"], signo, decimales),
                        "variacion_ultima_pct": est_g["variacion_ultima_pct"],
                        "tendencia": _tendencia_visible(est_g["tendencia"]),
                        "serie": serie_g,
                    }
                )
            for i, p, sufijo in partes:
                desglose[i] = {**desglose[i], "grupo": p, "nombre": sufijo}
    variables_grupos: list[dict[str, Any]] | None = None
    if grupos and grupo is None and _id_sin_total_global(match):
        # Estado financiero: la ficha muestra una línea por grupo (Activos, Pasivos, Patrimonio).
        variables_grupos = []
        for g in grupos:
            est_g = _estadisticas_serie(g["serie"])
            variables_grupos.append(
                {
                    "subindicador": g["nombre"],
                    "nombre": g["nombre"],
                    "valor_fmt": g["valor_fmt"],
                    "ultimo_anio": est_g["ultimo_anio"],
                    "variacion_ultima_pct": est_g["variacion_ultima_pct"],
                    "variacion_promedio_pct": est_g["variacion_promedio_pct"],
                    "tendencia": _tendencia_visible(est_g["tendencia"]),
                    "serie": g["serie"],
                }
            )
    if variables_grupos:
        primera = variables_grupos[0]
        return {
            **base,
            "subindicador": None,
            "consolidado": True,
            "agregacion": None,
            "signo": _clean(signo),
            "decimales": _int_o_none(decimales),
            "ultimo_anio": max((v["ultimo_anio"] for v in variables_grupos if v["ultimo_anio"] is not None), default=None),
            "ultimo_valor": None,
            "valor_fmt": " · ".join(f"{v['nombre']}: {v['valor_fmt']}" for v in variables_grupos),
            "tendencia": primera["tendencia"],
            "variacion_ultima_pct": primera["variacion_ultima_pct"],
            "variacion_promedio_pct": primera["variacion_promedio_pct"],
            "serie": primera["serie"],
            **_rango_anios([p for v in variables_grupos for p in v["serie"]], _ultimo_texto(match.get("Periodo_nombre"))),
            "variables": variables_grupos,
            "desglose": desglose,
            "grupos": grupos,
        }
    if grupo is not None:
        # Ficha de un subtotal (p.ej. Virtual): las categorías se nombran sin el prefijo del grupo.
        prefijo = f"{grupo} - "
        desglose = [
            {**d, "nombre": (d["subindicador"] or "")[len(prefijo) :]}
            if (d["subindicador"] or "").startswith(prefijo)
            else d
            for d in desglose
        ]
    return {
        **base,
        "subindicador": grupo,
        "consolidado": True,
        "signo": _clean(signo),
        "decimales": _int_o_none(decimales),
        "agregacion": None if not serie else ("Promedio" if signo in _TASA_SIGNOS else "Total"),
        "ultimo_anio": est.get("ultimo_anio"),
        "ultimo_valor": est.get("ultimo_valor"),
        "valor_fmt": fmt_valor_plan(est.get("ultimo_valor"), signo, decimales) if serie else "No aplica",
        "tendencia": _tendencia_visible(est.get("tendencia")),
        "variacion_ultima_pct": est.get("variacion_ultima_pct"),
        "variacion_promedio_pct": est.get("variacion_promedio_pct"),
        "serie": serie,
        **_rango_anios(
            serie or [p for c in desglose for p in c["serie"]], _ultimo_texto(match.get("Periodo_nombre"))
        ),
        "desglose": desglose,
        "grupos": grupos,
    }
