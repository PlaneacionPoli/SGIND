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
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
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


def detectar_vencidos(
    df: pd.DataFrame,
    *,
    referencia: date | None = None,
    proceso: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Indicadores con reporte vencido / por vencer según su periodicidad.

    Se calcula siempre sobre toda la historia del indicador (no sobre el corte
    filtrado), contra `referencia` (hoy por defecto). Los indicadores sin ningún
    reporte quedan como vencidos con `diff_meses=None` ("sin reporte"); los que
    solo figuran como "No aplica" se excluyen.
    """
    hoy = referencia or date.today()
    ym_actual = hoy.year * 12 + hoy.month
    needed = {"Id", "Año", "Mes", "Estado"}
    if not needed.issubset(df.columns):
        return pd.DataFrame(), pd.DataFrame()

    if proceso and proceso != "Todos" and "Proceso" in df.columns:
        df = df[df["Proceso"].astype(str) == proceso]
    estado = df["Estado"].astype(str).str.strip()
    df = df[df["Id"].isin(df.loc[estado != "No aplica", "Id"])]
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    df_rep = df[df["Estado"].astype(str).str.strip() == "Reportado"].copy()
    df_rep["ym"] = pd.to_numeric(df_rep["Año"], errors="coerce").fillna(0).astype(
        int
    ) * 12 + pd.to_numeric(df_rep["Mes"], errors="coerce").fillna(0).astype(int)
    ultimo = df_rep.groupby("Id")["ym"].max().reset_index().rename(columns={"ym": "ultimo_ym"})

    meta_cols = [c for c in ["Id", "Periodicidad", "Proceso", "Indicador"] if c in df.columns]
    meta = df[meta_cols].drop_duplicates(subset=["Id"])
    merged = meta.merge(ultimo, on="Id", how="left")
    merged["sin_reporte"] = merged["ultimo_ym"].isna()
    merged["ultimo_ym"] = merged["ultimo_ym"].fillna(0).astype(int)
    merged["ventana"] = merged.get("Periodicidad", pd.Series("mensual", index=merged.index)).apply(
        _ventana
    )
    merged["diff_meses"] = (ym_actual - merged["ultimo_ym"]).where(~merged["sin_reporte"])
    merged["ultimo_reporte"] = (
        merged["ultimo_ym"].apply(_ym_a_texto).where(~merged["sin_reporte"], "Sin reporte")
    )

    vencidos = merged[merged["sin_reporte"] | (merged["diff_meses"] > merged["ventana"])].copy()
    por_vencer = merged[
        ~merged["sin_reporte"]
        & (merged["diff_meses"] <= merged["ventana"])
        & (merged["diff_meses"] >= (merged["ventana"] * 0.8).astype(int))
        & (merged["diff_meses"] > 0)
    ].copy()
    # Más atrasados primero; "sin reporte" encabeza la lista de vencidos.
    vencidos["_orden"] = vencidos["diff_meses"].fillna(10**6)
    vencidos = vencidos.sort_values("_orden", ascending=False).drop(columns="_orden")
    return vencidos, por_vencer


def _ym_a_texto(ym: int) -> str:
    anio, mes = divmod(int(ym) - 1, 12)
    return f"{MESES_NOMBRES[mes][:3]} {anio}"


def apply_filters(
    df: pd.DataFrame,
    *,
    anio: int | None = None,
    mes: int | None = None,
    proceso: str | None = None,
    estado: str | None = None,
    busqueda: str | None = None,
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
    if busqueda and busqueda.strip():
        q = _nm(busqueda)
        cols = [c for c in ("Id", "Indicador", "Proceso") if c in out.columns]
        texto = out[cols].astype(str).apply(lambda col: col.map(_nm)).agg(" ".join, axis=1)
        out = out[texto.str.contains(q, regex=False)]
    return out


def build_filtros(df: pd.DataFrame) -> dict[str, Any]:
    anios: list[int] = []
    meses_por_anio: dict[str, list[int]] = {}
    if not df.empty and {"Año", "Mes"}.issubset(df.columns):
        ym = df[["Año", "Mes"]].apply(pd.to_numeric, errors="coerce").dropna().astype(int)
        anios = sorted(ym["Año"].unique().tolist())
        meses_por_anio = {str(a): sorted(g["Mes"].unique().tolist()) for a, g in ym.groupby("Año")}
    meses_nums = sorted({m for ms in meses_por_anio.values() for m in ms})
    meses_nombres = [MESES_NOMBRES[m - 1] for m in meses_nums if 1 <= m <= 12]
    procesos = (
        sorted(df["Proceso"].dropna().astype(str).unique().tolist())
        if "Proceso" in df.columns
        else []
    )
    estados = (
        sorted(df["Estado"].dropna().astype(str).unique().tolist())
        if "Estado" in df.columns
        else []
    )
    # Corte por defecto = el más reciente con datos (no un año/mes fijo).
    default_year = anios[-1] if anios else None
    meses_default_year = meses_por_anio.get(str(default_year), [])
    default_mes = (
        meses_default_year[-1] if meses_default_year else (meses_nums[-1] if meses_nums else 12)
    )
    return {
        "anios": anios,
        "anio_default": default_year,
        "meses": meses_nums,
        "meses_por_anio": meses_por_anio,
        "mes_default": default_mes,
        "meses_nombres": meses_nombres,
        "procesos": procesos,
        "estados": estados,
    }


def build_kpis(df: pd.DataFrame) -> dict[str, Any]:
    total = len(df)
    estado = df.get("Estado", pd.Series(dtype=str))
    reportados = int((estado == "Reportado").sum())
    pendientes = int((estado == "Pendiente").sum())
    no_aplica = int((estado == "No aplica").sum())
    exigibles = total - no_aplica
    return {
        "registros": total,
        "reportados": reportados,
        "pendientes": pendientes,
        "no_aplica": no_aplica,
        "cumplimiento_pct": round(reportados / exigibles * 100, 1) if exigibles > 0 else None,
        "procesos_con_pendientes": (
            int(df.loc[estado == "Pendiente", "Proceso"].nunique())
            if "Proceso" in df.columns
            else 0
        ),
    }


def build_estado_por_proceso(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty or "Proceso" not in df.columns or "Estado" not in df.columns:
        return []
    grouped = df.groupby(["Proceso", "Estado"], dropna=False).size().reset_index(name="cantidad")
    result: list[dict[str, Any]] = []
    for proceso in sorted(grouped["Proceso"].astype(str).unique()):
        subset = grouped[grouped["Proceso"].astype(str) == proceso]
        estados = []
        for _, row in subset.iterrows():
            est = str(row["Estado"])
            estados.append(
                {
                    "estado": est,
                    "cantidad": int(row["cantidad"]),
                    "color": _ESTADO_COLORS.get(est, "#94a3b8"),
                }
            )
        result.append({"proceso": proceso, "estados": estados})
    return result


def _con_corte(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega la columna legible `Corte` ("Jun 2026") a partir de Año y Mes."""
    if df.empty or not {"Año", "Mes"}.issubset(df.columns):
        return df
    out = df.copy()
    out["Corte"] = [
        f"{MESES_NOMBRES[int(m) - 1][:3]} {int(a)}"
        if pd.notna(a) and pd.notna(m) and 1 <= int(m) <= 12
        else ""
        for a, m in zip(out["Año"], out["Mes"], strict=True)
    ]
    return out


def build_cumplimiento_por_proceso(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Una fila por proceso: avance del corte y sus indicadores pendientes.

    Ordenado de menor a mayor cumplimiento para que lo que requiere acción
    quede arriba.
    """
    if df.empty or not {"Proceso", "Estado"}.issubset(df.columns):
        return []
    rows: list[dict[str, Any]] = []
    for proceso, g in df.groupby(df["Proceso"].astype(str)):
        estado = g["Estado"].astype(str)
        reportados = int((estado == "Reportado").sum())
        pendientes_df = g[estado == "Pendiente"]
        no_aplica = int((estado == "No aplica").sum())
        exigibles = len(g) - no_aplica
        rows.append(
            {
                "proceso": proceso,
                "total": len(g),
                "reportados": reportados,
                "pendientes": len(pendientes_df),
                "no_aplica": no_aplica,
                "cumplimiento_pct": round(reportados / exigibles * 100, 1) if exigibles else None,
                "indicadores_pendientes": _rows_to_dicts(
                    _con_corte(pendientes_df),
                    ["Id", "Indicador", "Periodicidad", "Corte"],
                    limit=len(pendientes_df),
                ),
            }
        )
    rows.sort(
        key=lambda r: (
            r["cumplimiento_pct"] if r["cumplimiento_pct"] is not None else 101,
            -r["pendientes"],
            r["proceso"],
        )
    )
    return rows


_ORDEN_PERIODICIDAD = ["mensual", "bimestral", "trimestral", "semestral", "anual"]


def _pct(reportados: int, total: int, no_aplica: int) -> float | None:
    exigibles = total - no_aplica
    return round(reportados / exigibles * 100, 1) if exigibles > 0 else None


def _conteo(g: pd.DataFrame) -> tuple[int, int, int]:
    estado = g["Estado"].astype(str)
    return (
        int((estado == "Reportado").sum()),
        int((estado == "Pendiente").sum()),
        int((estado == "No aplica").sum()),
    )


def _ym_valido(df: pd.DataFrame) -> pd.DataFrame:
    """Filas con año y mes válidos, con columna auxiliar `_ym` (año*12+mes)."""
    if df.empty or not {"Año", "Mes", "Estado"}.issubset(df.columns):
        return pd.DataFrame()
    out = df.dropna(subset=["Año", "Mes"]).copy()
    out["_ym"] = out["Año"].astype(int) * 12 + out["Mes"].astype(int)
    return out


def _corte_de_ym(ym: int) -> dict[str, Any]:
    anio, mes0 = divmod(int(ym) - 1, 12)
    return {"anio": anio, "mes": mes0 + 1, "corte": f"{MESES_NOMBRES[mes0][:3]} {anio}"}


def build_tendencia(df: pd.DataFrame, proceso: str | None = None) -> list[dict[str, Any]]:
    """Cumplimiento de reporte por corte (un punto por año-mes), para la serie histórica."""
    if proceso and proceso != "Todos" and "Proceso" in df.columns:
        df = df[df["Proceso"].astype(str) == proceso]
    base = _ym_valido(df)
    if base.empty:
        return []
    out: list[dict[str, Any]] = []
    for ym, g in base.groupby("_ym"):
        rep, pen, na = _conteo(g)
        out.append(
            _corte_de_ym(ym)
            | {
                "reportados": rep,
                "pendientes": pen,
                "no_aplica": na,
                "total": len(g),
                "cumplimiento_pct": _pct(rep, len(g), na),
            }
        )
    return out


def build_matriz_calor(df: pd.DataFrame, ultimos: int = 12) -> dict[str, Any]:
    """Proceso × corte con el % de cumplimiento (None = ese proceso no reporta ese corte)."""
    base = _ym_valido(df)
    if base.empty or "Proceso" not in base.columns:
        return {"cortes": [], "filas": []}
    yms = sorted(base["_ym"].unique())[-ultimos:]
    base = base[base["_ym"].isin(yms)]
    # Una sola tabla cruzada (proceso, corte) × estado en vez de filtrar el DataFrame por celda.
    cruz = pd.crosstab([base["Proceso"].astype(str), base["_ym"]], base["Estado"].astype(str))
    for col in ("Reportado", "Pendiente", "No aplica"):
        if col not in cruz.columns:
            cruz[col] = 0
    conteos = {
        (proc, int(ym)): (int(r.Reportado), int(r.Pendiente), int(r["No aplica"]))
        for (proc, ym), r in cruz.iterrows()
    }
    filas: list[dict[str, Any]] = []
    for proceso in sorted({proc for proc, _ in conteos}):
        celdas: list[dict[str, Any] | None] = []
        for ym in yms:
            rep, pen, na = conteos.get((proceso, int(ym)), (0, 0, 0))
            pct = _pct(rep, rep + pen + na, na)
            celdas.append(None if pct is None else {"pct": pct, "pendientes": pen})
        con_dato = [c["pct"] for c in celdas if c]
        filas.append(
            {
                "proceso": proceso,
                "celdas": celdas,
                "promedio_pct": round(sum(con_dato) / len(con_dato), 1) if con_dato else None,
            }
        )
    filas.sort(
        key=lambda f: (f["promedio_pct"] if f["promedio_pct"] is not None else 101, f["proceso"])
    )
    return {"cortes": [_corte_de_ym(ym) for ym in yms], "filas": filas}


def build_por_periodicidad(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty or not {"Periodicidad", "Estado"}.issubset(df.columns):
        return []
    rows = []
    for per, g in df.groupby(df["Periodicidad"].astype(str)):
        rep, pen, na = _conteo(g)
        rows.append(
            {
                "periodicidad": per,
                "total": len(g),
                "reportados": rep,
                "pendientes": pen,
                "no_aplica": na,
                "cumplimiento_pct": _pct(rep, len(g), na),
            }
        )
    rows.sort(
        key=lambda r: _ORDEN_PERIODICIDAD.index(_nm(r["periodicidad"]))
        if _nm(r["periodicidad"]) in _ORDEN_PERIODICIDAD
        else 99
    )
    return rows


def _variacion_pp(
    tendencia: list[dict[str, Any]], anio: int | None, mes: int | None
) -> float | None:
    """Puntos porcentuales de cambio frente al corte anterior (solo con corte exacto)."""
    if anio is None or mes is None:
        return None
    for i, t in enumerate(tendencia):
        if t["anio"] == anio and t["mes"] == mes:
            previo = tendencia[i - 1]["cumplimiento_pct"] if i > 0 else None
            actual = t["cumplimiento_pct"]
            return round(actual - previo, 1) if actual is not None and previo is not None else None
    return None


_DETALLE_COLS = ["Id", "Indicador", "Proceso", "Periodicidad", "Corte", "Estado"]
_ORDEN_ESTADO = {"Pendiente": 0, "Reportado": 1, "No aplica": 2}


_ORDENABLES = {"Id", "Indicador", "Proceso", "Periodicidad", "Corte", "Estado"}


def _detalle_view(
    df: pd.DataFrame, orden_por: str | None = None, orden_dir: str = "asc"
) -> pd.DataFrame:
    """Vista curada del detalle. Por defecto: pendientes primero, luego proceso e indicador."""
    out = _con_corte(df)
    if out.empty or "Estado" not in out.columns:
        return out
    asc = orden_dir != "desc"
    if orden_por in _ORDENABLES:
        if orden_por == "Corte":
            claves, asc_l = ["Año", "Mes", "Indicador"], [asc, asc, True]
        elif orden_por == "Id":
            out = out.assign(_id=pd.to_numeric(out["Id"], errors="coerce"))
            claves, asc_l = ["_id", "Indicador"], [asc, True]
        elif orden_por == "Estado":
            out = out.assign(_o=out["Estado"].astype(str).map(_ORDEN_ESTADO).fillna(3))
            claves, asc_l = ["_o", "Proceso", "Indicador"], [asc, True, True]
        else:
            claves, asc_l = [orden_por, "Indicador"], [asc, True]
        out = out.sort_values(claves, ascending=asc_l, kind="stable")
        return out.drop(columns=[c for c in ("_id", "_o") if c in out.columns])
    out = out.assign(_o=out["Estado"].astype(str).map(_ORDEN_ESTADO).fillna(3))
    sort_cols = ["_o"] + [c for c in ("Proceso", "Indicador") if c in out.columns]
    return out.sort_values(sort_cols, kind="stable").drop(columns="_o")


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
            elif isinstance(val, int | float):
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
    limit: int = 500,
    offset: int = 0,
    referencia: date | None = None,
    orden_por: str | None = None,
    orden_dir: str = "asc",
    busqueda: str | None = None,
) -> dict[str, Any]:
    filtros = build_filtros(df_raw)
    df_view = apply_filters(
        df_raw, anio=anio, mes=mes, proceso=proceso, estado=estado, busqueda=busqueda
    )
    # Las alertas dependen de la fecha de referencia y del proceso, no del corte.
    vencidos, por_vencer = detectar_vencidos(df_raw, referencia=referencia, proceso=proceso)

    alert_cols = ["Id", "Indicador", "Proceso", "Periodicidad", "diff_meses", "ultimo_reporte"]
    df_page = _detalle_view(df_view, orden_por, orden_dir).iloc[offset : offset + limit]
    tendencia = build_tendencia(df_raw, proceso)
    kpis = build_kpis(df_view)
    kpis["variacion_pp"] = _variacion_pp(tendencia, anio, mes)
    return {
        "filtros": filtros,
        "filtros_aplicados": {
            "anio": anio,
            "mes": mes,
            "mes_nombre": MESES_NOMBRES[mes - 1] if mes and 1 <= mes <= 12 else None,
            "proceso": proceso or "Todos",
            "estado": estado or "Todos",
            "busqueda": (busqueda or "").strip() or None,
        },
        "kpis": kpis,
        "alertas": {
            "referencia": (referencia or date.today()).isoformat(),
            "vencidos_total": len(vencidos),
            "por_vencer_total": len(por_vencer),
            "vencidos": _rows_to_dicts(vencidos, alert_cols, limit=len(vencidos)),
            "por_vencer": _rows_to_dicts(por_vencer, alert_cols, limit=len(por_vencer)),
        },
        "estado_por_proceso": build_estado_por_proceso(df_view),
        "cumplimiento_procesos": build_cumplimiento_por_proceso(df_view),
        "tendencia": tendencia,
        "matriz_calor": build_matriz_calor(df_raw),
        "por_periodicidad": build_por_periodicidad(df_view),
        "detalle": _rows_to_dicts(df_page, _DETALLE_COLS, limit=limit),
        "detalle_total": len(df_view),
        "detalle_limit": limit,
        "detalle_offset": offset,
        "estado_colores": _ESTADO_COLORS,
    }
