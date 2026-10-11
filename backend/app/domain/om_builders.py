"""Constructores Gestión OM — paridad streamlit_app/pages/gestion_om.py."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.domain.constants import COLOR_CATEGORIA as CATEGORIA_COLORS
from app.domain.loader_utils import id_a_str

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
MES_A_NUM = {m: i + 1 for i, m in enumerate(MESES_NOMBRES)}

TIPO_ACCION_COLORS = {
    "OM Kawak": "#2563EB",
    "Reto Plan Anual": "#D97706",
    "Proyecto Institucional": "#0EA5A4",
    "Otro": "#6B7280",
    "Sin acción": "#94A3B8",
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


def _id_str(v: Any) -> str:
    """Normaliza identificadores tipo '440.0' / ' 440 ' -> '440'."""
    s = str(v).strip()
    if not s:
        return ""
    try:
        f = float(s)
        if f.is_integer():
            return str(int(f))
        return str(f)
    except (TypeError, ValueError):
        return s


def _extraer_digitos(v: str) -> str:
    """Extrae el primer grupo de digitos, ej. 'OM 440'/'OM440' -> '440'."""
    import re

    match = re.search(r"\d+", v)
    return match.group(0) if match else ""


def _buscar_avance(avances_om: dict[str, float], numero_om: str) -> float | None:
    """Matching robusto de numero_om -> avance: exacto, normalizado, por digitos, sin mayus/minus."""
    if not numero_om:
        return None
    candidatos = [str(numero_om).strip()]
    normalizado = _id_str(numero_om)
    if normalizado:
        candidatos.append(normalizado)
    digitos = _extraer_digitos(str(numero_om))
    if digitos:
        candidatos.append(digitos)

    avances_lower = {k.lower(): v for k, v in avances_om.items()}
    for cand in candidatos:
        if cand in avances_om:
            return avances_om[cand]
        if cand.lower() in avances_lower:
            return avances_lower[cand.lower()]
    return None


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
                id_om_col = next(
                    (c for c in cols if c.startswith("Id ") and "Oportunidad" in c), None
                )
            id_accion_col = next(
                (c for c in cols if str(c).strip().lower() in {"id acción", "id accion"}), None
            )
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


def load_plan_accion_para_om(excel, numero_om: str) -> list[dict[str, Any]]:
    """Carga las actividades del plan de acción asociadas a un numero_om/identificador.

    Paridad con streamlit_app/pages/gestion_om.py::_cargar_plan_accion_para_om +
    _normalizar_campos_plan_accion. Retorna una lista de dicts con las columnas
    Id Acción, Acción, Responsable de ejecución, Avance (%), Estado (Plan de Acción)
    y Estado (Oportunidad de mejora).
    """
    if not numero_om:
        return []
    base = excel.data_root / _PLAN_ACCION_DIR
    if not base.exists():
        return []

    candidatos = [str(numero_om).strip()]
    normalizado = _id_str(numero_om)
    if normalizado and normalizado not in candidatos:
        candidatos.append(normalizado)
    digitos = _extraer_digitos(str(numero_om))
    if digitos and digitos not in candidatos:
        candidatos.append(digitos)

    rows: list[dict[str, Any]] = []
    for f in base.glob("*.xlsx"):
        try:
            df = pd.read_excel(f, dtype=str, na_filter=False)
        except Exception:
            continue
        cols = df.columns.tolist()
        id_col = next((c for c in cols if "Id Oportunidad de mejora" in c), None)
        if not id_col:
            id_col = next((c for c in cols if c.startswith("Id ") and "Oportunidad" in c), None)
        if not id_col or id_col not in df.columns:
            continue

        serie_id = df[id_col].astype(str).str.strip()
        mask = serie_id.isin(candidatos)
        if not mask.any():
            serie_norm = serie_id.apply(_id_str)
            mask = serie_norm.isin(candidatos)
        subset = df.loc[mask, :]
        if subset.empty:
            continue

        for _, row in subset.iterrows():
            id_accion = (
                str(row.get("Id Acción", "")).strip() or str(row.get("Id Accion", "")).strip()
            )
            accion = str(row.get("Acción", "")).strip() or str(row.get("Accion", "")).strip()
            if not accion:
                accion = (
                    str(row.get("Descripción", "")).strip()
                    or str(row.get("Descripcion", "")).strip()
                )
            resp = (
                str(row.get("Responsable de ejecución", ""))
                or str(row.get("Responsable", ""))
                or str(row.get("Fuente de Identificación", ""))
            )
            avance = row.get("Avance (%)", row.get("Avance", ""))
            if avance is None or (isinstance(avance, float) and pd.isna(avance)):
                avance = ""
            estado_plan = str(row.get("Estado (Plan de Acción)", "")) or str(
                row.get("Estado (Plan Acción)", "")
            )
            estado_om = str(row.get("Estado (Oportunidad de mejora)", "")) or str(
                row.get("Estado de Oportunidad", "")
            )
            rows.append(
                {
                    "id_accion": id_accion,
                    "accion": accion,
                    "responsable": resp.strip(),
                    "avance": _formatear_avance_plan(avance),
                    "estado_plan": estado_plan.strip(),
                    "estado_om": estado_om.strip(),
                }
            )

    if not rows:
        return []

    # Deduplicar por Id Acción (o por Acción si no hay id)
    vistos: set[str] = set()
    dedupe: list[dict[str, Any]] = []
    for r in rows:
        key = r["id_accion"] or r["accion"]
        if not key or key in vistos:
            continue
        vistos.add(key)
        dedupe.append(r)
    return dedupe


def _formatear_avance_plan(avance: Any) -> str:
    n = pd.to_numeric(avance, errors="coerce")
    if pd.isna(n):
        return "-"
    n = float(n)
    if n <= 1.5:
        n *= 100
    return f"{n:.1f}%"


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
        out["Mes_num"] = out["Mes"].apply(
            lambda x: MES_A_NUM.get(_mes_a_nombre(x), pd.to_numeric(x, errors="coerce"))
        )
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


def _cumplimiento_pct(row: Any) -> float | None:
    """Cumplimiento en %: usa `Cumplimiento_pct` si existe; si no, `Cumplimiento_norm` (fracción 0–1)."""
    for col, factor in (("Cumplimiento_pct", 1.0), ("cumplimiento_pct", 1.0), ("Cumplimiento_norm", 100.0)):
        if col in row.index:
            x = pd.to_numeric(row[col], errors="coerce")
            if pd.notna(x):
                return round(float(x) * factor, 1)
    return None


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
        cumpl_pct = _cumplimiento_pct(row)

        cat = str(row.get("Categoria", row.get("Nivel de cumplimiento", "Sin dato")))
        tipo_accion = om.get("tipo_accion") or "Sin acción"
        numero_om = om.get("numero_om") or ""
        comentario = om.get("comentario") or ""
        tiene_om = int(om.get("tiene_om", 0) or 0)
        avance_om = _buscar_avance(avances_om, numero_om)
        if avance_om is None and tiene_om:
            avance_om = _buscar_avance(avances_om, rid)

        rows.append(
            {
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
                "tipo_accion_color": TIPO_ACCION_COLORS.get(
                    tipo_accion, TIPO_ACCION_COLORS["Sin acción"]
                ),
                "tiene_om": tiene_om,
                "numero_om": str(numero_om) if numero_om else "",
                "comentario": str(comentario) if comentario else "",
                "om_id": om.get("id"),
                "avance_om": avance_om,
                "row_bg": "#FFF5F5"
                if cat == "Peligro"
                else ("#FFFBEB" if cat == "Alerta" else "#FFFFFF"),
            }
        )
    return pd.DataFrame(rows)


def _cortes_con_dato(df: pd.DataFrame) -> dict[int, list[str]]:
    """Meses (nombre) con al menos un indicador evaluado, por año. «Sin dato» no cuenta."""
    if df.empty or "Anio" not in df.columns or "Mes" not in df.columns:
        return {}
    d = pd.DataFrame(
        {
            "anio": pd.to_numeric(df["Anio"], errors="coerce"),
            "mes": df["Mes"].apply(lambda x: MES_A_NUM.get(_mes_a_nombre(x))),
        }
    )
    cat_col = "Categoria" if "Categoria" in df.columns else "Nivel de cumplimiento"
    if cat_col in df.columns:
        d = d[df[cat_col].astype(str).str.strip().ne("Sin dato").to_numpy()]
    d = d.dropna()
    out: dict[int, list[str]] = {}
    for anio, g in d.groupby("anio"):
        out[int(anio)] = [MESES_NOMBRES[int(m) - 1] for m in sorted(g["mes"].unique())]
    return out


def build_filtros(df: pd.DataFrame) -> dict[str, Any]:
    cortes = _cortes_con_dato(df)
    anios = sorted(cortes) or [2025]
    anio_default = anios[-1]
    procesos = (
        sorted(df["Proceso"].dropna().astype(str).unique().tolist())
        if "Proceso" in df.columns
        else []
    )
    if not procesos and "Proceso_padre" in df.columns:
        procesos = sorted(df["Proceso_padre"].dropna().astype(str).unique().tolist())
    subprocesos = (
        sorted(df["Subproceso"].dropna().astype(str).unique().tolist())
        if "Subproceso" in df.columns
        else []
    )
    if not subprocesos and "Subproceso_final" in df.columns:
        subprocesos = sorted(df["Subproceso_final"].dropna().astype(str).unique().tolist())
    return {
        "anios": [str(y) for y in anios],
        "anio_default": str(anio_default),
        "meses": MESES_NOMBRES,
        "meses_por_anio": {str(y): m for y, m in cortes.items()},
        "mes_default": (cortes.get(anio_default) or ["Diciembre"])[-1],
        "procesos": procesos,
        "subprocesos": subprocesos,
    }


def build_kpis_matriz(df_tabla: pd.DataFrame) -> dict[str, Any]:
    if df_tabla.empty:
        return {"peligro": 0, "alerta": 0, "con_om": 0, "total": 0, "avance_om_promedio": None}
    total = len(df_tabla)
    peligro = (
        int((df_tabla["categoria"] == "Peligro").sum()) if "categoria" in df_tabla.columns else 0
    )
    alerta = (
        int((df_tabla["categoria"] == "Alerta").sum()) if "categoria" in df_tabla.columns else 0
    )
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


def build_por_proceso(df_tabla: pd.DataFrame) -> list[dict[str, Any]]:
    """Indicadores en riesgo por proceso, con y sin OM (más pendientes primero)."""
    if df_tabla.empty or "proceso" not in df_tabla.columns:
        return []
    out: list[dict[str, Any]] = []
    for proceso, g in df_tabla.groupby(df_tabla["proceso"].replace("", "Sin proceso")):
        con_om = int((g["tiene_om"] == 1).sum())
        out.append(
            {
                "proceso": str(proceso),
                "total": int(len(g)),
                "con_om": con_om,
                "sin_om": int(len(g)) - con_om,
            }
        )
    return sorted(out, key=lambda r: (-r["sin_om"], -r["total"], r["proceso"]))


def build_historial(
    df_historico: pd.DataFrame, ids: list[str], *, anio: int, mes: str, n: int = 6
) -> dict[str, list[dict[str, Any]]]:
    """Últimos `n` periodos (hasta el corte) de cada indicador, para el contexto del registro."""
    mes_num = MES_A_NUM.get(mes)
    if df_historico.empty or not ids or not mes_num or "Id" not in df_historico.columns:
        return {}
    df = df_historico.copy()
    df["_id"] = df["Id"].apply(id_a_str)
    df = df[df["_id"].isin(set(ids))]
    if df.empty or "Anio" not in df.columns or "Mes" not in df.columns:
        return {}
    df["_anio"] = pd.to_numeric(df["Anio"], errors="coerce")
    df["_mes"] = df["Mes"].apply(
        lambda x: MES_A_NUM.get(_mes_a_nombre(x), pd.to_numeric(x, errors="coerce"))
    )
    df["_mes"] = pd.to_numeric(df["_mes"], errors="coerce")
    df = df.dropna(subset=["_anio", "_mes"])
    df = df[(df["_anio"] * 100 + df["_mes"]) <= anio * 100 + mes_num]
    cat_col = "Categoria" if "Categoria" in df.columns else "Nivel de cumplimiento"

    def _num(v: Any) -> float | None:
        x = pd.to_numeric(v, errors="coerce")
        return None if pd.isna(x) else float(x)

    out: dict[str, list[dict[str, Any]]] = {}
    for rid, g in df.groupby("_id"):
        g = g.sort_values(["_anio", "_mes"]).drop_duplicates(["_anio", "_mes"], keep="last").tail(n)
        out[str(rid)] = [
            {
                "periodo": f"{MESES_NOMBRES[int(r['_mes']) - 1][:3]} {int(r['_anio'])}",
                "cumplimiento_pct": _cumplimiento_pct(r),
                "ejecucion": _num(r.get("Ejecucion")),
                "meta": _num(r.get("Meta")),
                "categoria": str(r.get(cat_col, "")) if cat_col in g.columns else "",
            }
            for _, r in g.iterrows()
        ]
    return out


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
            elif isinstance(val, int | float):
                rec[col] = float(val) if isinstance(val, float) else int(val)
            else:
                rec[col] = str(val)
        records.append(rec)
    return records
