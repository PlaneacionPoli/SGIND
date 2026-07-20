"""Constructores de calidad de datos — Monitoreo_Informacion_Procesos (LISTA DE CHEQUEO)."""

from __future__ import annotations

import math
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd

from app.services.excel_reader import ExcelReaderService

_CRITERIOS = [
    "I. OPORTUNIDAD",
    "II. COMPLETITUD",
    "III. CONSISTENCIA",
    "IV. PRECISIÓN",
    "V. PROTOCOLO",
]

_DIM_LABELS = {
    "I. OPORTUNIDAD": "Oportunidad",
    "II. COMPLETITUD": "Completitud",
    "III. CONSISTENCIA": "Consistencia",
    "IV. PRECISIÓN": "Exactitud",
    "V. PROTOCOLO": "Protocolo",
}

_DIM_COLORS = {
    "Oportunidad": "#ffa726",
    "Completitud": "#42a5f5",
    "Consistencia": "#66bb6a",
    "Exactitud": "#ab47bc",
    "Protocolo": "#1A3A5C",
}

_CALIDAD_PATHS = [
    "raw/Monitoreo/Monitoreo_Informacion_Procesos 2025.xlsx",
    "raw/Monitoreo/Monitoreo_Informacion_Procesos.xlsx",
]


def _norm_text(value: object) -> str:
    text = str(value or "").strip().upper()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.category(ch) == "Mn")


def _first_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols_norm = {_norm_text(c): c for c in df.columns}
    for cand in candidates:
        key = _norm_text(cand)
        if key in cols_norm:
            return cols_norm[key]
    return None


def _score_calidad(v: object) -> float | None:
    t = _norm_text(v)
    if not t:
        return None
    if "CUMPLE PARCIAL" in t:
        return 0.5
    if "NO CUMPLE" in t:
        return 0.0
    if "CUMPLE" in t:
        return 1.0
    return None


def _estado_calidad(p: object) -> str:
    try:
        n = float(p)
    except (TypeError, ValueError):
        return "SIN DATO"
    if math.isnan(n):
        return "SIN DATO"
    if n >= 90:
        return "CUMPLE"
    if n >= 70:
        return "CUMPLE PARCIALMENTE"
    return "NO CUMPLE"


def load_calidad_data(excel: ExcelReaderService) -> tuple[pd.DataFrame, str | None]:
    path: Path | None = None
    for rel in _CALIDAD_PATHS:
        candidate = excel.data_root / rel
        if candidate.exists():
            path = candidate
            break
    if path is None:
        for candidate in (excel.data_root / "raw" / "Monitoreo").glob("Monitoreo_Informacion_Procesos*.xlsx"):
            path = candidate
            break
    if path is None:
        return pd.DataFrame(), "No se encontró archivo Monitoreo_Informacion_Procesos en data/raw/Monitoreo/"

    try:
        df = pd.read_excel(path, sheet_name="LISTA DE CHEQUEO", header=4, engine="openpyxl")
    except Exception as exc:
        return pd.DataFrame(), f"No se pudo leer LISTA DE CHEQUEO: {exc}"

    if df.empty:
        return pd.DataFrame(), "La hoja LISTA DE CHEQUEO está vacía."

    df = df.dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]

    proc_col = _first_col(df, ["PROCESO", "Proceso"])
    sub_col = _first_col(df, ["SUBPROCESO", "Subproceso"])
    tem_col = _first_col(df, ["Tematica", "Temática"])
    c_cols = [
        _first_col(df, ["I. OPORTUNIDAD", "OPORTUNIDAD"]),
        _first_col(df, ["II. COMPLETITUD", "COMPLETITUD"]),
        _first_col(df, ["III. CONSISTENCIA", "CONSISTENCIA"]),
        _first_col(df, ["IV. PRECISIÓN", "IV. PRECISION", "PRECISIÓN", "PRECISION"]),
        _first_col(df, ["V. PROTOCOLO", "PROTOCOLO"]),
    ]

    if proc_col is None:
        return pd.DataFrame(), "No se encontró columna Proceso en LISTA DE CHEQUEO."
    if any(c is None for c in c_cols):
        return pd.DataFrame(), "Faltan columnas de criterios de calidad en LISTA DE CHEQUEO."

    out_cols = [c for c in [proc_col, sub_col, tem_col, *c_cols] if c is not None]
    out = df[out_cols].copy()
    rename_map: dict[str, str] = {proc_col: "Proceso"}
    if sub_col:
        rename_map[sub_col] = "Subproceso"
    if tem_col:
        rename_map[tem_col] = "Temática"
    for crit, src in zip(_CRITERIOS, c_cols):
        if src:
            rename_map[src] = crit
    out = out.rename(columns=rename_map)

    for col in _CRITERIOS:
        out[col] = (
            out[col]
            .astype(str)
            .str.replace("✔", "", regex=False)
            .str.replace("⚠", "", regex=False)
            .str.replace("✘", "", regex=False)
            .str.strip()
            .str.upper()
        )

    score_cols = []
    for c in _CRITERIOS:
        sc = f"{c}__score"
        out[sc] = out[c].apply(_score_calidad)
        score_cols.append(sc)

    out["pct_calidad"] = (out[score_cols].mean(axis=1, skipna=True) * 100).round(1)
    out["Estado calidad"] = out["pct_calidad"].apply(_estado_calidad)
    out = out.drop(columns=score_cols, errors="ignore")
    out = out.dropna(subset=["Proceso"]).reset_index(drop=True)
    return out, None


def filter_calidad(
    df: pd.DataFrame,
    *,
    proceso: str | None = None,
    subproceso: str | None = None,
    unidad: str | None = None,
    map_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if proceso and proceso != "Todos":
        out = out[out["Proceso"].astype(str).map(_norm_text) == _norm_text(proceso)]
    if subproceso and subproceso != "Todos" and "Subproceso" in out.columns:
        out = out[out["Subproceso"].astype(str).map(_norm_text) == _norm_text(subproceso)]
    if unidad and unidad != "Todos" and map_df is not None and not map_df.empty:
        if {"Proceso", "Unidad"}.issubset(map_df.columns):
            proc_unidad = map_df[["Proceso", "Unidad"]].drop_duplicates()
            out = out.merge(proc_unidad, on="Proceso", how="left")
            out = out[out["Unidad"].astype(str) == unidad]
    return out


def build_dim_scores(df: pd.DataFrame) -> dict[str, float]:
    scores: dict[str, float] = {}
    for crit, label in _DIM_LABELS.items():
        if crit not in df.columns:
            scores[label] = 0.0
            continue
        vals = df[crit].apply(_score_calidad).dropna() * 100
        scores[label] = round(float(vals.mean()), 1) if not vals.empty else 0.0
    return scores


def build_calidad_dashboard(
    df: pd.DataFrame,
    *,
    mensaje: str | None = None,
) -> dict[str, Any]:
    if df.empty:
        return {
            "disponible": False,
            "mensaje": mensaje or "Sin datos de calidad para el filtro seleccionado.",
            "score_global": None,
            "dim_scores": {},
            "dim_colors": _DIM_COLORS,
            "kpis": {"total_registros": 0, "total_subprocesos": 0, "promedio": None},
            "por_proceso": [],
            "por_subproceso": [],
            "alertas_dim": [],
            "registros": [],
        }

    work = df.copy()
    if "Subproceso" not in work.columns:
        work["Subproceso"] = "Sin subproceso"
    work["pct_calidad"] = pd.to_numeric(work.get("pct_calidad"), errors="coerce")
    score_global = round(float(work["pct_calidad"].mean()), 1) if work["pct_calidad"].notna().any() else None
    dim_scores = build_dim_scores(work)

    alertas = [
        {"dimension": dim, "score": score, "color": _DIM_COLORS.get(dim, "#1A3A5C")}
        for dim, score in dim_scores.items()
        if score < 90
    ]
    alertas.sort(key=lambda x: x["score"])

    por_proceso = (
        work.groupby("Proceso", dropna=False)
        .agg(
            registros=("Proceso", "size"),
            subprocesos=("Subproceso", "nunique"),
            pct_calidad=("pct_calidad", "mean"),
            cumple=("Estado calidad", lambda s: int((s == "CUMPLE").sum())),
            parcial=("Estado calidad", lambda s: int((s == "CUMPLE PARCIALMENTE").sum())),
            no_cumple=("Estado calidad", lambda s: int((s == "NO CUMPLE").sum())),
        )
        .reset_index()
    )
    por_proceso["pct_calidad"] = por_proceso["pct_calidad"].round(1)
    por_proceso_list = por_proceso.sort_values("pct_calidad", ascending=False).to_dict(orient="records")

    por_sub = (
        work.groupby(["Proceso", "Subproceso"], dropna=False)
        .agg(registros=("Subproceso", "size"), pct_calidad=("pct_calidad", "mean"))
        .reset_index()
    )
    por_sub["pct_calidad"] = por_sub["pct_calidad"].round(1)
    por_sub_list = por_sub.sort_values("pct_calidad", ascending=False).head(30).to_dict(orient="records")

    registros = []
    for _, row in work.head(100).iterrows():
        registros.append(
            {
                "proceso": str(row.get("Proceso", "")),
                "subproceso": str(row.get("Subproceso", "")),
                "tematica": str(row.get("Temática", "")),
                "pct_calidad": row.get("pct_calidad"),
                "estado": str(row.get("Estado calidad", "SIN DATO")),
                "criterios": {crit: str(row.get(crit, "")) for crit in _CRITERIOS if crit in row.index},
            }
        )

    return {
        "disponible": True,
        "mensaje": None,
        "score_global": score_global,
        "dim_scores": dim_scores,
        "dim_colors": _DIM_COLORS,
        "kpis": {
            "total_registros": len(work),
            "total_subprocesos": int(work["Subproceso"].nunique()),
            "promedio": score_global,
        },
        "por_proceso": por_proceso_list,
        "por_subproceso": por_sub_list,
        "alertas_dim": alertas,
        "registros": registros,
    }
