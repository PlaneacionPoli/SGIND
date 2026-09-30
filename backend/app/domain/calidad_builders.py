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

# La pestaña "Calidad de Datos" replica el módulo original de Streamlit
# (informe_por_procesos.py::_DIM_MAP), que solo visualiza estas 4 dimensiones
# — "V. PROTOCOLO" se carga desde el Excel pero nunca se muestra en esa pestaña.
_TAB_DIMS = ["Completitud", "Consistencia", "Oportunidad", "Exactitud"]

_CALIDAD_PATHS = [
    "raw/Monitoreo/Monitoreo_Informacion_Procesos 2025.xlsx",
    "raw/Monitoreo/Monitoreo_Informacion_Procesos.xlsx",
]


def _norm_text(value: object) -> str:
    text = str(value or "").strip().upper()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.category(ch) == "Mn")


def _first_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    # Los encabezados reales del Excel traen una descripción entre paréntesis
    # tras un salto de línea (p.ej. "I. OPORTUNIDAD\n(Entrega en tiempo )"),
    # por eso el match es por prefijo normalizado, no por igualdad exacta.
    cols_norm = [(_norm_text(c), c) for c in df.columns]
    for cand in candidates:
        key = _norm_text(cand)
        for norm, original in cols_norm:
            if norm == key or norm.startswith(key):
                return original
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
        for candidate in (excel.data_root / "raw" / "Monitoreo").glob(
            "Monitoreo_Informacion_Procesos*.xlsx"
        ):
            path = candidate
            break
    if path is None:
        return (
            pd.DataFrame(),
            "No se encontró archivo Monitoreo_Informacion_Procesos en data/raw/Monitoreo/",
        )

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
    for crit, src in zip(_CRITERIOS, c_cols, strict=False):
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


_LABEL_TO_CRIT = {label: crit for crit, label in _DIM_LABELS.items()}


def _compute_scored_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Una fila por indicador (Temática) con las 4 dimensiones de la pestaña en escala 0-100."""
    work = pd.DataFrame(index=df.index)
    work["Indicador"] = df.get("Temática", pd.Series("", index=df.index)).astype(str).str.strip()
    work["Proceso"] = df.get("Proceso", pd.Series("", index=df.index)).astype(str).str.strip()
    work["Subproceso"] = df.get("Subproceso", pd.Series("", index=df.index)).astype(str).str.strip()
    for dim in _TAB_DIMS:
        crit = _LABEL_TO_CRIT[dim]
        if crit in df.columns:
            work[dim] = df[crit].apply(_score_calidad).apply(
                lambda v: None if v is None else v * 100
            )
        else:
            work[dim] = None
    dim_frame = work[_TAB_DIMS].apply(pd.to_numeric, errors="coerce")
    work["Score Total"] = dim_frame.mean(axis=1, skipna=True).round(0)
    return work


def _dim_scores_global(scored: pd.DataFrame) -> dict[str, float]:
    out: dict[str, float] = {}
    for dim in _TAB_DIMS:
        vals = pd.to_numeric(scored.get(dim), errors="coerce").dropna()
        out[dim] = round(float(vals.mean()), 1) if not vals.empty else 0.0
    return out


def _build_alertas(scored: pd.DataFrame, dim_scores: dict[str, float]) -> list[dict[str, Any]]:
    if not dim_scores:
        return []
    worst_dim = min(dim_scores, key=dim_scores.get)
    best_dim = max(dim_scores, key=dim_scores.get)
    worst_score = dim_scores[worst_dim]
    best_score = dim_scores[best_dim]
    alertas: list[dict[str, Any]] = []

    if worst_score < 90:
        col = pd.to_numeric(scored.get(worst_dim), errors="coerce")
        n_total = int(col.notna().sum())
        n_no_cumple = int((col == 0).sum())
        n_parcial = int((col == 50).sum())
        indicadores = [
            str(v)
            for v in scored.loc[col == 0, "Indicador"].tolist()
            if str(v) not in ("nan", "")
        ]
        detalle = f"{n_no_cumple} NO CUMPLE"
        if n_parcial:
            detalle += f" · {n_parcial} PARCIAL"
        if n_total:
            detalle += f" / {n_total}"
        alertas.append(
            {
                "tipo": "critica",
                "titulo": f"Crítica: {worst_dim} · {worst_score:.0f}/100",
                "detalle": detalle,
                "indicadores": indicadores[:3],
                "indicadores_extra": max(0, len(indicadores) - 3),
            }
        )

    if best_score >= 90:
        col = pd.to_numeric(scored.get(best_dim), errors="coerce")
        n_total = int(col.notna().sum())
        n_cumple = int((col == 100).sum())
        alertas.append(
            {
                "tipo": "fortaleza",
                "titulo": f"Fortaleza: {best_dim} · {best_score:.0f}/100",
                "detalle": f"{n_cumple}/{n_total} indicadores CUMPLEN al 100%." if n_total else "—",
                "indicadores": [],
                "indicadores_extra": 0,
            }
        )
    return alertas


def _build_recomendaciones(scored: pd.DataFrame, dim_scores: dict[str, float]) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []

    peores = scored.dropna(subset=["Score Total"]).copy()
    if not peores.empty:
        peores["Score Total"] = pd.to_numeric(peores["Score Total"], errors="coerce")
        peores = peores.sort_values("Score Total")
        worst_row = peores.iloc[0]
        ws_score = float(worst_row["Score Total"])
        dims_fallando = [
            f"{d} ({float(worst_row[d]):.0f}%)"
            for d in _TAB_DIMS
            if pd.notna(worst_row.get(d)) and float(worst_row[d]) < 100
        ]
        items = [f"Score: {ws_score:.0f}/100"]
        if dims_fallando:
            items.append(", ".join(dims_fallando))
        items.append("Convocar responsable para corregir NO CUMPLE.")
        recs.append(
            {
                "prioridad": "Alta",
                "titulo": f"«{worst_row['Indicador']}»",
                "items": items,
            }
        )

    if dim_scores:
        wdim = min(dim_scores, key=dim_scores.get)
        wdim_score = dim_scores[wdim]
        if wdim_score < 90:
            col = pd.to_numeric(scored.get(wdim), errors="coerce")
            ind_nc = [
                str(v)
                for v in scored.loc[col < 100, "Indicador"].tolist()
                if str(v) not in ("nan", "")
            ]
            listado = ", ".join(f"«{i}»" for i in ind_nc[:2])
            if len(ind_nc) > 2:
                listado += f" +{len(ind_nc) - 2}"
            items_m = [f"{wdim}: {wdim_score:.0f}/100 — {len(ind_nc)} sin cumplimiento."]
            if listado:
                items_m.append(listado)
            items_m.append("Meta: ≥ 90% antes del próximo corte.")
            recs.append({"prioridad": "Media", "titulo": f"Fortalecer: {wdim}", "items": items_m})

        bdim = max(dim_scores, key=dim_scores.get)
        bscore = dim_scores[bdim]
        col = pd.to_numeric(scored.get(bdim), errors="coerce")
        n_ok = int((col == 100).sum())
        n_tot = int(col.notna().sum())
        recs.append(
            {
                "prioridad": "Baja",
                "titulo": f"Mantener: {bdim}",
                "items": [
                    f"{n_ok}/{n_tot} CUMPLEN al 100% (score: {bscore:.0f}/100).",
                    "Documentar prácticas y auditar trimestralmente.",
                ],
            }
        )
    return recs


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
            "alertas": [],
            "recomendaciones": [],
            "detalle_indicadores": [],
            "registros": [],
        }

    work = df.copy()
    if "Subproceso" not in work.columns:
        work["Subproceso"] = "Sin subproceso"
    work["pct_calidad"] = pd.to_numeric(work.get("pct_calidad"), errors="coerce")

    scored = _compute_scored_rows(work)
    dim_scores = _dim_scores_global(scored)
    score_global = (
        round(float(pd.Series(list(dim_scores.values())).mean()), 1) if dim_scores else None
    )
    alertas = _build_alertas(scored, dim_scores)
    recomendaciones = _build_recomendaciones(scored, dim_scores)

    detalle_indicadores = []
    for _, row in scored.iterrows():
        detalle_indicadores.append(
            {
                "indicador": row["Indicador"],
                "proceso": row["Proceso"],
                "subproceso": row["Subproceso"],
                "dimensiones": {
                    dim: (None if pd.isna(row.get(dim)) else float(row[dim])) for dim in _TAB_DIMS
                },
                "score_total": None if pd.isna(row.get("Score Total")) else float(row["Score Total"]),
            }
        )

    alertas_dim = [
        {"dimension": dim, "score": score, "color": _DIM_COLORS.get(dim, "#1A3A5C")}
        for dim, score in dim_scores.items()
        if score < 90
    ]
    alertas_dim.sort(key=lambda x: x["score"])

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
    por_proceso_list = por_proceso.sort_values("pct_calidad", ascending=False).to_dict(
        orient="records"
    )

    por_sub = (
        work.groupby(["Proceso", "Subproceso"], dropna=False)
        .agg(registros=("Subproceso", "size"), pct_calidad=("pct_calidad", "mean"))
        .reset_index()
    )
    por_sub["pct_calidad"] = por_sub["pct_calidad"].round(1)
    por_sub_list = (
        por_sub.sort_values("pct_calidad", ascending=False).head(30).to_dict(orient="records")
    )

    registros = []
    for _, row in work.head(100).iterrows():
        registros.append(
            {
                "proceso": str(row.get("Proceso", "")),
                "subproceso": str(row.get("Subproceso", "")),
                "tematica": str(row.get("Temática", "")),
                "pct_calidad": row.get("pct_calidad"),
                "estado": str(row.get("Estado calidad", "SIN DATO")),
                "criterios": {
                    crit: str(row.get(crit, "")) for crit in _CRITERIOS if crit in row.index
                },
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
        "alertas_dim": alertas_dim,
        "alertas": alertas,
        "recomendaciones": recomendaciones,
        "detalle_indicadores": detalle_indicadores,
        "registros": registros,
    }
