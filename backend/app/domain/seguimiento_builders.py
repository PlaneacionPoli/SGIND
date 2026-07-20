"""Constructores Seguimiento Operativo — paridad streamlit_app/pages/seguimiento_reportes.py."""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from app.domain.loader_utils import id_a_str

_SEGUIMIENTO_PATH = "output/Seguimiento_Reporte.xlsx"
_SHEET = "Tracking Mensual"

_VENTANA_MESES: dict[str, int] = {
    "mensual": 1,
    "bimestral": 2,
    "trimestral": 3,
    "semestral": 6,
    "anual": 12,
}

_ESTADO_COLORS = {
    "Reportado": "#28a745",
    "Pendiente": "#ffc107",
    "No aplica": "#6c757d",
}

MESES_NOMBRES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


def _nm(s: str) -> str:
    s = str(s or "").strip().lower()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u")):
        s = s.replace(a, b)
    return s


def _ventana(periodicidad: str) -> int:
    return _VENTANA_MESES.get(_nm(periodicidad), 1)


def load_tracking(excel) -> pd.DataFrame:
    """Carga hoja Tracking Mensual desde Seguimiento_Reporte.xlsx."""
    path = excel.data_root / _SEGUIMIENTO_PATH
    if not path.exists():
        return pd.DataFrame()
    try:
        df = excel.read_excel(_SEGUIMIENTO_PATH, sheet_name=_SHEET)
    except Exception:
        return pd.DataFrame()
    df.columns = [str(c).strip() for c in df.columns]
    if "Id" in df.columns:
        df["Id"] = df["Id"].apply(id_a_str)
    if "Año" in df.columns:
        df["Año"] = pd.to_numeric(df["Año"], errors="coerce").astype("Int64")
    if "Mes" in df.columns:
        df["Mes"] = pd.to_numeric(df["Mes"], errors="coerce").astype("Int64")
    return df


def detectar_vencidos(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    hoy = date.today()
    ym_actual = hoy.year * 12 + hoy.month
    needed = {"Id", "Año", "Mes", "Estado"}
    if not needed.issubset(df.columns):
        return pd.DataFrame(), pd.DataFrame()

    df_rep = df[df["Estado"].astype(str).str.strip() == "Reportado"].copy()
    df_rep["ym"] = (
        pd.to_numeric(df_rep["Año"], errors="coerce").fillna(0).astype(int) * 12
        + pd.to_numeric(df_rep["Mes"], errors="coerce").fillna(0).astype(int)
    )
    ultimo = df_rep.groupby("Id")["ym"].max().reset_index().rename(columns={"ym": "ultimo_ym"})

    meta_cols = [c for c in ["Id", "Periodicidad", "Proceso", "Indicador"] if c in df.columns]
    meta = df[meta_cols].drop_duplicates(subset=["Id"])
    merged = meta.merge(ultimo, on="Id", how="left")
    merged["ultimo_ym"] = merged["ultimo_ym"].fillna(0).astype(int)
    merged["ventana"] = merged.get("Periodicidad", pd.Series("mensual", index=merged.index)).apply(_ventana)
    merged["diff_meses"] = ym_actual - merged["ultimo_ym"]

    vencidos = merged[merged["diff_meses"] > merged["ventana"]].copy()
    por_vencer = merged[
        (merged["diff_meses"] <= merged["ventana"])
        & (merged["diff_meses"] >= (merged["ventana"] * 0.8).astype(int))
        & (merged["diff_meses"] > 0)
    ].copy()
    return vencidos, por_vencer


def apply_filters(
    df: pd.DataFrame,
    *,
    anio: int | None = None,
    mes: int | None = None,
    proceso: str | None = None,
    estado: str | None = None,
) -> pd.DataFrame:
    out = df.copy()
    if anio is not None and "Año" in out.columns:
        out = out[out["Año"] == anio]
    if mes is not None and "Mes" in out.columns:
        out = out[out["Mes"] == mes]
    if proceso and proceso != "Todos" and "Proceso" in out.columns:
        out = out[out["Proceso"].astype(str) == proceso]
    if estado and estado != "Todos" and "Estado" in out.columns:
        out = out[out["Estado"].astype(str) == estado]
    return out


def build_filtros(df: pd.DataFrame) -> dict[str, Any]:
    anios = sorted(
        pd.to_numeric(df.get("Año", pd.Series(dtype=float)), errors="coerce")
        .dropna().astype(int).unique().tolist()
    ) if not df.empty else []
    meses_nums = sorted(
        pd.to_numeric(df.get("Mes", pd.Series(dtype=float)), errors="coerce")
        .dropna().astype(int).unique().tolist()
    ) if not df.empty else []
    meses_nombres = [MESES_NOMBRES[m - 1] for m in meses_nums if 1 <= m <= 12]
    procesos = sorted(df["Proceso"].dropna().astype(str).unique().tolist()) if "Proceso" in df.columns else []
    estados = sorted(df["Estado"].dropna().astype(str).unique().tolist()) if "Estado" in df.columns else []
    default_year = 2025 if 2025 in anios else (anios[-1] if anios else None)
    default_mes = 12 if 12 in meses_nums else (meses_nums[-1] if meses_nums else 12)
    return {
        "anios": anios,
        "anio_default": default_year,
        "meses": meses_nums,
        "mes_default": default_mes,
        "meses_nombres": meses_nombres,
        "procesos": procesos,
        "estados": estados,
    }


def build_kpis(df: pd.DataFrame) -> dict[str, int]:
    total = len(df)
    estado = df.get("Estado", pd.Series(dtype=str))
    return {
        "registros": total,
        "reportados": int((estado == "Reportado").sum()),
        "pendientes": int((estado == "Pendiente").sum()),
        "no_aplica": int((estado == "No aplica").sum()),
    }


def build_estado_por_proceso(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty or "Proceso" not in df.columns or "Estado" not in df.columns:
        return []
    grouped = (
        df.groupby(["Proceso", "Estado"], dropna=False)
        .size()
        .reset_index(name="cantidad")
    )
    result: list[dict[str, Any]] = []
    for proceso in sorted(grouped["Proceso"].astype(str).unique()):
        subset = grouped[grouped["Proceso"].astype(str) == proceso]
        estados = []
        for _, row in subset.iterrows():
            est = str(row["Estado"])
            estados.append({
                "estado": est,
                "cantidad": int(row["cantidad"]),
                "color": _ESTADO_COLORS.get(est, "#94a3b8"),
            })
        result.append({"proceso": proceso, "estados": estados})
    return result


def _rows_to_dicts(df: pd.DataFrame, cols: list[str], limit: int = 20) -> list[dict[str, Any]]:
    if df.empty:
        return []
    present = [c for c in cols if c in df.columns]
    out = df[present].head(limit).copy()
    records = []
    for _, row in out.iterrows():
        rec = {}
        for c in present:
            val = row[c]
            if pd.isna(val):
                rec[c] = None
            elif isinstance(val, (int, float)):
                rec[c] = float(val) if isinstance(val, float) else int(val)
            else:
                rec[c] = str(val)
        records.append(rec)
    return records


def build_dashboard(
    df_raw: pd.DataFrame,
    *,
    anio: int | None = None,
    mes: int | None = None,
    proceso: str | None = None,
    estado: str | None = None,
) -> dict[str, Any]:
    filtros = build_filtros(df_raw)
    df_view = apply_filters(df_raw, anio=anio, mes=mes, proceso=proceso, estado=estado)
    vencidos, por_vencer = detectar_vencidos(df_raw)

    alert_cols = ["Id", "Indicador", "Proceso", "Periodicidad", "diff_meses"]
    return {
        "filtros": filtros,
        "filtros_aplicados": {
            "anio": anio,
            "mes": mes,
            "mes_nombre": MESES_NOMBRES[mes - 1] if mes and 1 <= mes <= 12 else None,
            "proceso": proceso or "Todos",
            "estado": estado or "Todos",
        },
        "kpis": build_kpis(df_view),
        "alertas": {
            "vencidos_total": len(vencidos),
            "por_vencer_total": len(por_vencer),
            "vencidos": _rows_to_dicts(vencidos, alert_cols),
            "por_vencer": _rows_to_dicts(por_vencer, alert_cols),
        },
        "estado_por_proceso": build_estado_por_proceso(df_view),
        "detalle": _rows_to_dicts(df_view, list(df_view.columns), limit=5000),
        "estado_colores": _ESTADO_COLORS,
    }
