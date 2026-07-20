"""Constructores Gestión OM — paridad streamlit_app/pages/gestion_om.py."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.domain.loader_utils import id_a_str

MESES_NOMBRES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]
MES_A_NUM = {m: i + 1 for i, m in enumerate(MESES_NOMBRES)}

TIPO_ACCION_COLORS = {
    "OM Kawak": "#2563EB",
    "Reto Plan Anual": "#D97706",
    "Proyecto Institucional": "#0EA5A4",
    "Otro": "#6B7280",
    "Sin acción": "#94A3B8",
}

CATEGORIA_COLORS = {
    "Peligro": "#C62828",
    "Alerta": "#F9A825",
    "Cumplimiento": "#2E7D32",
    "Sobrecumplimiento": "#6699FF",
    "Sin dato": "#6E7781",
}

_PLAN_ACCION_DIR = "raw/Plan de accion"


def _mes_a_nombre(val) -> str:
    if pd.isna(val):
        return ""
    if isinstance(val, str) and val in MESES_NOMBRES:
        return val
    try:
        n = int(float(val))
        return MESES_NOMBRES[n - 1] if 1 <= n <= 12 else str(val)
    except (TypeError, ValueError):
        return str(val)


def _parse_avance(v) -> float | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip()
    if not s or s.lower() in {"nan", "none", "-"}:
        return None
    has_percent = "%" in s
    s = s.replace("%", "").replace(" ", "")
    if "," in s and "." in s and s.rfind(",") > s.rfind("."):
        s = s.replace(".", "")
    s = s.replace(",", ".")
    n = pd.to_numeric(s, errors="coerce")
    if pd.isna(n):
        return None
    n = float(n)
    if has_percent or n > 1:
        return round(min(100.0, n if has_percent or n > 1 else n * 100), 1)
    return round(n * 100, 1)


def load_avance_om(excel) -> dict[str, float]:
    base = excel.data_root / _PLAN_ACCION_DIR
    if not base.exists():
        return {}
    dfs = []
    for f in base.glob("*.xlsx"):
        try:
            df = pd.read_excel(f, dtype=str, na_filter=False)
            cols = df.columns.tolist()
            avance_col = next((c for c in cols if "Avance" in c and "%" in c), None)
            if not avance_col:
                avance_col = next((c for c in cols if "Avance" in c), None)
            id_om_col = next((c for c in cols if "Id Oportunidad de mejora" in c), None)
            if not id_om_col:
                id_om_col = next((c for c in cols if c.startswith("Id ") and "Oportunidad" in c), None)
            id_accion_col = next((c for c in cols if str(c).strip().lower() in {"id acción", "id accion"}), None)
            if id_om_col and avance_col:
                subset_cols = [id_om_col, avance_col]
                if id_accion_col:
                    subset_cols.append(id_accion_col)
                sub = df[subset_cols].copy()
                if id_accion_col:
                    sub.columns = ["Id_OM", "Avance", "Id_Accion"]
                else:
                    sub.columns = ["Id_OM", "Avance"]
                dfs.append(sub)
        except Exception:
            continue
    if not dfs:
        return {}
    df_all = pd.concat(dfs, ignore_index=True)
    df_all["Avance"] = df_all["Avance"].apply(_parse_avance)
    df_all["Id_OM"] = df_all["Id_OM"].astype(str).str.strip()
    df_all = df_all.dropna(subset=["Id_OM", "Avance"])
    df_all = df_all[(df_all["Id_OM"] != "") & (df_all["Id_OM"].str.lower() != "nan")]
    if "Id_Accion" in df_all.columns:
        df_all["Id_Accion"] = df_all["Id_Accion"].astype(str).str.strip()
        con_id = df_all[df_all["Id_Accion"] != ""].drop_duplicates(subset=["Id_OM", "Id_Accion"])
        sin_id = df_all[df_all["Id_Accion"] == ""]
        df_all = pd.concat([con_id, sin_id], ignore_index=True)
    return df_all.groupby("Id_OM")["Avance"].mean().round(1).to_dict()


def filter_indicadores_riesgo(
    df: pd.DataFrame,
    *,
    anio: int,
    mes: str,
    proceso: str | None = None,
    subproceso: str | None = None,
    mostrar_alerta: bool = False,
) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    mes_num = MES_A_NUM.get(mes)
    if "Anio" in out.columns:
        out = out[pd.to_numeric(out["Anio"], errors="coerce") == anio]
    if mes_num and "Mes" in out.columns:
        out["Mes_num"] = out["Mes"].apply(lambda x: MES_A_NUM.get(_mes_a_nombre(x), pd.to_numeric(x, errors="coerce")))
        out = out[pd.to_numeric(out["Mes_num"], errors="coerce") == mes_num]
    cat_col = "Categoria" if "Categoria" in out.columns else "Nivel de cumplimiento"
    if cat_col in out.columns:
        cats = ["Peligro"] + (["Alerta"] if mostrar_alerta else [])
        out = out[out[cat_col].astype(str).isin(cats)]
    if proceso and proceso != "Todos":
        proc_col = "Proceso" if "Proceso" in out.columns else "Proceso_padre"
        if proc_col in out.columns:
            out = out[out[proc_col].astype(str) == proceso]
    if subproceso and subproceso != "Todos":
        sub_col = "Subproceso" if "Subproceso" in out.columns else "Subproceso_final"
        if sub_col in out.columns:
            out = out[out[sub_col].astype(str) == subproceso]
    return out


def merge_om_registros(
    df_riesgo: pd.DataFrame,
    registros: list[dict[str, Any]],
    avances_om: dict[str, float],
) -> pd.DataFrame:
    if df_riesgo.empty:
        return pd.DataFrame()
    df = df_riesgo.copy()
    df["Id"] = df["Id"].apply(id_a_str) if "Id" in df.columns else df.index.astype(str)

    om_by_id: dict[str, dict] = {}
    for reg in registros:
        key = id_a_str(reg.get("id_indicador", ""))
        if key:
            om_by_id[key] = reg

    rows = []
    for _, row in df.iterrows():
        rid = id_a_str(row.get("Id", ""))
        om = om_by_id.get(rid, {})
        if "Cumplimiento_pct" in row.index and pd.notna(row.get("Cumplimiento_pct")):
            cumpl = pd.to_numeric(row["Cumplimiento_pct"], errors="coerce")
            cumpl_pct = round(float(cumpl), 1) if pd.notna(cumpl) else None
        elif "cumplimiento_pct" in row.index:
            cumpl = pd.to_numeric(row["cumplimiento_pct"], errors="coerce")
            cumpl_pct = round(float(cumpl), 1) if pd.notna(cumpl) else None
        else:
            cumpl_pct = None

        cat = str(row.get("Categoria", row.get("Nivel de cumplimiento", "Sin dato")))
        tipo_accion = om.get("tipo_accion") or "Sin acción"
        numero_om = om.get("numero_om") or om.get("comentario") or ""
        tiene_om = int(om.get("tiene_om", 0) or 0)
        avance_om = avances_om.get(str(numero_om).strip()) if numero_om else None
        if avance_om is None and tiene_om:
            avance_om = avances_om.get(rid)

        rows.append({
            "id": rid,
            "indicador": str(row.get("Indicador", "")),
            "proceso": str(row.get("Proceso", row.get("Proceso_padre", ""))),
            "subproceso": str(row.get("Subproceso", row.get("Subproceso_final", ""))),
            "periodicidad": str(row.get("Periodicidad", row.get("Frecuencia", ""))),
            "meta": row.get("Meta"),
            "ejecucion": row.get("Ejecucion"),
            "cumplimiento_pct": cumpl_pct,
            "categoria": cat,
            "categoria_color": CATEGORIA_COLORS.get(cat, "#6E7781"),
            "tipo_accion": tipo_accion,
            "tipo_accion_color": TIPO_ACCION_COLORS.get(tipo_accion, TIPO_ACCION_COLORS["Sin acción"]),
            "tiene_om": tiene_om,
            "numero_om": str(numero_om) if numero_om else "",
            "om_id": om.get("id"),
            "avance_om": avance_om,
            "row_bg": "#FFF5F5" if cat == "Peligro" else ("#FFFBEB" if cat == "Alerta" else "#FFFFFF"),
        })
    return pd.DataFrame(rows)


def build_filtros(df: pd.DataFrame) -> dict[str, Any]:
    anios = ["2026"]
    if "Anio" in df.columns:
        available = sorted(pd.to_numeric(df["Anio"], errors="coerce").dropna().astype(int).unique().tolist())
        anios = [str(y) for y in available] or anios
        if 2025 in available and "2025" not in anios:
            anios = ["2025"] + [a for a in anios if a != "2025"]
    procesos = sorted(df["Proceso"].dropna().astype(str).unique().tolist()) if "Proceso" in df.columns else []
    if not procesos and "Proceso_padre" in df.columns:
        procesos = sorted(df["Proceso_padre"].dropna().astype(str).unique().tolist())
    subprocesos = sorted(df["Subproceso"].dropna().astype(str).unique().tolist()) if "Subproceso" in df.columns else []
    if not subprocesos and "Subproceso_final" in df.columns:
        subprocesos = sorted(df["Subproceso_final"].dropna().astype(str).unique().tolist())
    return {
        "anios": anios,
        "anio_default": "2025" if "2025" in anios else (anios[0] if anios else "2025"),
        "meses": MESES_NOMBRES,
        "mes_default": "Diciembre",
        "procesos": procesos,
        "subprocesos": subprocesos,
    }


def build_kpis_matriz(df_tabla: pd.DataFrame) -> dict[str, Any]:
    if df_tabla.empty:
        return {"peligro": 0, "alerta": 0, "con_om": 0, "total": 0, "avance_om_promedio": None}
    total = len(df_tabla)
    peligro = int((df_tabla["categoria"] == "Peligro").sum()) if "categoria" in df_tabla.columns else 0
    alerta = int((df_tabla["categoria"] == "Alerta").sum()) if "categoria" in df_tabla.columns else 0
    con_om = int(df_tabla["tiene_om"].sum()) if "tiene_om" in df_tabla.columns else 0
    avance = pd.to_numeric(df_tabla.get("avance_om"), errors="coerce")
    avance_prom = round(float(avance.mean()), 1) if avance.notna().any() else None
    return {
        "peligro": peligro,
        "alerta": alerta,
        "con_om": con_om,
        "total": total,
        "avance_om_promedio": avance_prom,
    }


def matriz_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []
    records = []
    for _, row in df.iterrows():
        rec = {}
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                rec[col] = None
            elif isinstance(val, (int, float)):
                rec[col] = float(val) if isinstance(val, float) else int(val)
            else:
                rec[col] = str(val)
        records.append(rec)
    return records
