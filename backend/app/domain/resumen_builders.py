"""Constructores de Resumen General — portado desde resumen_general.py."""

from __future__ import annotations

import math
import re
import unicodedata
from typing import Any

import pandas as pd

from app.domain.categorization import categorizar_cumplimiento
from app.domain.linea_order import linea_sort_key


def _safe_pct(value: Any, *, default: float | None = None) -> float | None:
    """Convierte a porcentaje finito; evita NaN/Inf en respuestas JSON."""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(num) or math.isinf(num):
        return default
    return round(num, 1)


STRATEGIC_LINE_DEFS = [
    {"key": "expansion", "alt": [], "label": "Expansion", "icon": "rocket", "color": "#FBAF17"},
    {"key": "transformacion organizacional", "alt": ["transformacion organizacional"], "label": "Transformacion organizacional", "icon": "chart", "color": "#42F2F2"},
    {"key": "calidad", "alt": [], "label": "Calidad", "icon": "medal", "color": "#EC0677"},
    {"key": "experiencia", "alt": [], "label": "Experiencia", "icon": "bulb", "color": "#1FB2DE"},
    {"key": "sostenibilidad", "alt": ["sustentabilidad"], "label": "Sostenibilidad", "icon": "leaf", "color": "#A6CE38"},
    {"key": "educacion para toda la vida", "alt": ["educacion para toda la vida"], "label": "Educacion para toda la vida", "icon": "graduation", "color": "#0F385A"},
]

LINEA_COLORS_BADGE = {
    "expansion": "#FBAF17",
    "transformacion organizacional": "#0891b2",
    "calidad": "#EC0677",
    "experiencia": "#1FB2DE",
    "sostenibilidad": "#A6CE38",
    "educacion para toda la vida": "#0F385A",
}

SUNBURST_LINE_COLORS = {
    "expansion": "#FBAF17",
    "transformacion organizacional": "#42F2F2",
    "calidad": "#EC0677",
    "experiencia": "#1FB2DE",
    "sostenibilidad": "#A6CE38",
    "educacion para toda la vida": "#0F385A",
}

LABEL_WRAP_OVERRIDES = {
    "educacion para toda la vida": "Educación para\ntoda la vida",
}


def _sunburst_norm_key(value: str | None) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^0-9a-z]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _clean_sunburst_label(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().replace("_", " ")
    text = unicodedata.normalize("NFC", text)
    return re.sub(r"\s+", " ", text)


def _wrap_sunburst_label(label: str, width: int = 18) -> str:
    raw = str(label or "").strip()
    if not raw:
        return ""
    separators = [",", " / ", " - ", " y ", ";"]
    segments = [raw]
    for sep in separators:
        if any(sep in seg for seg in segments):
            new_segs = []
            for seg in segments:
                if sep in seg:
                    new_segs.extend(p.strip() for p in seg.split(sep) if p.strip())
                else:
                    new_segs.append(seg)
            segments = new_segs
    wrapped_lines = []
    for seg in segments:
        words = seg.split()
        cur: list[str] = []
        for word in words:
            if sum(len(x) for x in cur) + len(cur) + len(word) <= width:
                cur.append(word)
            else:
                if cur:
                    wrapped_lines.append(" ".join(cur))
                cur = [word]
        if cur:
            wrapped_lines.append(" ".join(cur))
    return "\n".join(re.sub(r"\s+", " ", ln).strip() for ln in wrapped_lines)


def _objective_display_label(label: str, parent: str) -> str:
    full = str(label or "").strip()
    if not full:
        return ""
    parent_key = _sunburst_norm_key(parent)
    label_key = _sunburst_norm_key(full)
    if parent_key == "sostenibilidad" and "inclusion" in label_key and "medio ambiente" in label_key:
        return "Inclusión, proyección social y medio ambiente"
    return full


def norm_key(value: str | None) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return _sunburst_norm_key(str(value))


def ensure_nivel_cumplimiento(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "Cumplimiento" in out.columns and "cumplimiento_pct" not in out.columns:
        out = out.rename(columns={"Cumplimiento": "cumplimiento_pct"})
    if "cumplimiento_pct" not in out.columns and "cumplimiento_dec" in out.columns:
        out["cumplimiento_pct"] = pd.to_numeric(out["cumplimiento_dec"], errors="coerce") * 100
    if "cumplimiento_pct" in out.columns:

        def _map_level(row):
            if pd.isna(row["cumplimiento_pct"]):
                return "Pendiente de reporte"
            try:
                pct = float(row["cumplimiento_pct"])
            except (TypeError, ValueError):
                return "Pendiente de reporte"
            if math.isnan(pct):
                return "Pendiente de reporte"
            return categorizar_cumplimiento(pct / 100.0, id_indicador=row.get("Id"))

        out["Nivel de cumplimiento"] = out.apply(_map_level, axis=1)
        return out
    if "Nivel de cumplimiento" not in out.columns:
        out["Nivel de cumplimiento"] = "Pendiente de reporte"
    return out


def build_linea_summary(
    df: pd.DataFrame,
    *,
    unique_count_col: str = "Id",
    count_col_name: str = "N_Indicadores",
) -> pd.DataFrame:
    cols = ["Linea", "Cumpl_Promedio", "Sobrecumplimiento", "Cumplimiento", "Alerta", "Peligro", count_col_name]
    if df.empty or "Linea" not in df.columns:
        return pd.DataFrame(columns=cols)

    work = ensure_nivel_cumplimiento(df.copy())
    if unique_count_col in work.columns:
        sort_cols = [unique_count_col, "Linea"]
        if "Fecha" in work.columns:
            sort_cols.append("Fecha")
        work = work.sort_values(sort_cols, na_position="last").drop_duplicates(
            subset=[unique_count_col, "Linea"], keep="last"
        )

    def _count_unique(s):
        return s.dropna().astype(str).str.strip().replace("", pd.NA).dropna().nunique()

    summary = (
        work.groupby("Linea", dropna=False)
        .agg(
            **{
                count_col_name: (unique_count_col, _count_unique) if unique_count_col in work.columns else ("Indicador", "count"),
                "Cumpl_Promedio": ("cumplimiento_pct", lambda x: x[x > 0].mean() if (x > 0).any() else pd.NA),
                "Sobrecumplimiento": ("Nivel de cumplimiento", lambda s: (s == "Sobrecumplimiento").sum()),
                "Cumplimiento": ("Nivel de cumplimiento", lambda s: (s == "Cumplimiento").sum()),
                "Alerta": ("Nivel de cumplimiento", lambda s: (s == "Alerta").sum()),
                "Peligro": ("Nivel de cumplimiento", lambda s: (s == "Peligro").sum()),
            }
        )
        .reset_index()
    )
    return summary


def get_chip_config_indicadores(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return _empty_chips_indicadores()
    unique = df.drop_duplicates(subset=["Id"], keep="last") if "Id" in df.columns else df
    total = len(unique)
    nivel = unique["Nivel de cumplimiento"] if "Nivel de cumplimiento" in unique.columns else pd.Series(dtype=str)
    counts = {
        "Sobrecumplimiento": int((nivel == "Sobrecumplimiento").sum()),
        "Cumplimiento": int((nivel == "Cumplimiento").sum()),
        "Alerta": int((nivel == "Alerta").sum()),
        "Peligro": int((nivel == "Peligro").sum()),
    }
    return [
        {"value": total, "label": "Total", "color": "#0B5FFF"},
        {"value": counts["Sobrecumplimiento"], "label": "Sobrecumplimiento", "color": "#173D66"},
        {"value": counts["Cumplimiento"], "label": "Cumplimiento", "color": "#16A34A"},
        {"value": counts["Alerta"], "label": "Alerta", "color": "#F59E0B"},
        {"value": counts["Peligro"], "label": "Peligro", "color": "#D32F2F"},
    ]


def _empty_chips_indicadores() -> list[dict]:
    return [
        {"value": 0, "label": "Total", "color": "#0B5FFF"},
        {"value": 0, "label": "Sobrecumplimiento", "color": "#173D66"},
        {"value": 0, "label": "Cumplimiento", "color": "#16A34A"},
        {"value": 0, "label": "Alerta", "color": "#F59E0B"},
        {"value": 0, "label": "Peligro", "color": "#D32F2F"},
    ]


def get_chip_config_proyectos(df: pd.DataFrame) -> list[dict]:
    if df.empty or "Id" not in df.columns:
        return [
            {"value": 0, "label": "Total Proyectos", "color": "#0B5FFF"},
            {"value": 0, "label": "Cerrados (100%)", "color": "#16A34A"},
            {"value": 0, "label": "En Ejecución", "color": "#F59E0B"},
            {"value": 0, "label": "Planeación", "color": "#6B7280"},
        ]
    unique = df.drop_duplicates(subset=["Id"], keep="last")
    cerrados = en_ejecucion = en_planeacion = 0
    for _, row in unique.iterrows():
        cumpl = row.get("cumplimiento_pct")
        if pd.isna(cumpl) or cumpl == 0:
            en_planeacion += 1
        elif cumpl >= 100:
            cerrados += 1
        else:
            en_ejecucion += 1
    return [
        {"value": len(unique), "label": "Total Proyectos", "color": "#0B5FFF"},
        {"value": cerrados, "label": "Cerrados (100%)", "color": "#16A34A"},
        {"value": en_ejecucion, "label": "En Ejecución", "color": "#F59E0B"},
        {"value": en_planeacion, "label": "Planeación", "color": "#6B7280"},
    ]


def build_strategy_cards(
    linea_summary: pd.DataFrame,
    historico_df: pd.DataFrame | None,
    *,
    vista: str = "indicadores",
) -> list[dict]:
    norm_to_row: dict[str, dict] = {}
    if not linea_summary.empty and "Linea" in linea_summary.columns:
        for _, row in linea_summary.iterrows():
            norm_to_row[norm_key(str(row["Linea"]))] = row.to_dict()

    unit_label = "proyectos" if vista == "proyectos" else "indicadores"
    count_col = "N_Proyectos" if vista == "proyectos" else "N_Indicadores"
    if vista == "retos":
        unit_label = "retos"
        count_col = "N_Indicadores"
    elif vista == "consolidado":
        unit_label = "planes"
        count_col = "N_Total"
    cards = []
    for line_def in STRATEGIC_LINE_DEFS:
        row = norm_to_row.get(line_def["key"])
        if row is None:
            for alt in [line_def["key"]] + line_def.get("alt", []):
                matches = [k for k in norm_to_row if alt in k]
                if matches:
                    row = norm_to_row[matches[0]]
                    break
        if row:
            count = int(float(row.get(count_col, row.get("N_Indicadores", 0)) or 0))
            cumpl = _safe_pct(row.get("Cumpl_Promedio", 0), default=0.0) or 0.0
            linea_nombre = str(row.get("Linea", line_def["label"]))
            n_indicadores = int(float(row.get("N_Indicadores", 0) or 0))
            n_proyectos = int(float(row.get("N_Proyectos", 0) or 0))
            n_retos = int(float(row.get("N_Retos", 0) or 0))
        else:
            count = 0
            cumpl = 0.0
            linea_nombre = line_def["label"]
            n_indicadores = 0
            n_proyectos = 0
            n_retos = 0

        historico: list[dict] = []
        if row and historico_df is not None and not historico_df.empty and "Linea" in historico_df.columns:
            df_hist = historico_df[historico_df["Linea"] == linea_nombre]
            if not df_hist.empty and "Anio" in df_hist.columns and "cumplimiento_pct" in df_hist.columns:
                serie = (
                    df_hist.groupby("Anio", dropna=False)["cumplimiento_pct"]
                    .mean()
                    .reset_index()
                    .sort_values("Anio")
                )
                historico = []
                for _, r in serie.iterrows():
                    if pd.isna(r["Anio"]):
                        continue
                    pct = _safe_pct(r["cumplimiento_pct"])
                    if pct is None:
                        continue
                    historico.append({"anio": int(r["Anio"]), "cumplimiento": pct})

        card: dict[str, Any] = {
            "linea": line_def["label"],
            "icon": line_def["icon"],
            "color": line_def["color"],
            "count": count,
            "cumplimiento": cumpl,
            "unit_label": unit_label,
            "historico": historico,
        }
        if vista == "consolidado":
            card["n_indicadores"] = n_indicadores
            card["n_proyectos"] = n_proyectos
            card["n_retos"] = n_retos
        cards.append(card)
    return cards


def build_sunburst_plotly(objetivo_df: pd.DataFrame) -> dict[str, Any]:
    empty = {
        "ids": ["sin_datos"],
        "labels": ["Sin datos"],
        "parents": [""],
        "values": [1],
        "colors": ["#6B728E"],
        "text": ["Sin datos<br>0%"],
        "customdata": [[0]],
    }
    if objetivo_df.empty or "Linea" not in objetivo_df.columns:
        return empty

    df = ensure_nivel_cumplimiento(objetivo_df.copy())
    if "Objetivo" not in df.columns:
        df["Objetivo"] = df["Linea"]
    if "cumplimiento_pct" in df.columns:
        df["cumplimiento_pct"] = pd.to_numeric(df["cumplimiento_pct"], errors="coerce")
        df["cumplimiento_pct"] = df["cumplimiento_pct"].replace([math.inf, -math.inf], pd.NA)

    for col in ["Linea", "Objetivo"]:
        if col in df.columns:
            df = df[df[col].notna() & (df[col].astype(str).str.strip() != "")]

    if "cumplimiento_pct" in df.columns:
        df = df[df["cumplimiento_pct"].notna()]

    if df.empty:
        return empty

    df["Linea"] = df["Linea"].apply(_clean_sunburst_label)
    df["Objetivo"] = df["Objetivo"].apply(_clean_sunburst_label)
    df = df[df["Objetivo"].astype(str).str.strip() != ""]
    if df.empty:
        return empty

    lines = df.groupby("Linea", dropna=False).agg(cumplimiento_pct=("cumplimiento_pct", "mean")).reset_index()
    grouped = (
        df.groupby(["Linea", "Objetivo"], dropna=False)
        .agg(cumplimiento_pct=("cumplimiento_pct", "mean"))
        .reset_index()
    )
    obj_counts = df.groupby(["Linea", "Objetivo"]).size().to_dict()
    objetivos_por_linea = grouped.groupby("Linea", dropna=False).size().to_dict()
    color_map = {_sunburst_norm_key(k): v for k, v in SUNBURST_LINE_COLORS.items()}

    labels: list[str] = []
    ids: list[str] = []
    parents: list[str] = []
    values: list[float] = []
    customdata: list[list[float]] = []
    colors: list[str] = []
    used_ids: set[str] = set()
    line_min_weight = 2.0

    def _unique_id(candidate: str) -> str:
        candidate = str(candidate or "").strip() or "node"
        if candidate not in used_ids:
            used_ids.add(candidate)
            return candidate
        idx = 1
        while True:
            alt = f"{candidate}_{idx}"
            if alt not in used_ids:
                used_ids.add(alt)
                return alt
            idx += 1

    line_id_by_name: dict[str, str] = {}
    for _, line in lines.iterrows():
        linea_name = str(line["Linea"]).strip()
        line_id = _unique_id(f"line::{_sunburst_norm_key(linea_name)}")
        line_id_by_name[linea_name] = line_id
        labels.append(linea_name)
        ids.append(line_id)
        parents.append("")
        values.append(0.0)
        pct = float(line["cumplimiento_pct"]) if pd.notna(line["cumplimiento_pct"]) else 0.0
        customdata.append([pct])
        colors.append(color_map.get(_sunburst_norm_key(linea_name), "#6B728E"))

    for _, row in grouped.iterrows():
        obj_name = str(row["Objetivo"]).strip()
        parent_name = str(row["Linea"]).strip()
        if not obj_name or not parent_name:
            continue
        count = obj_counts.get((row["Linea"], row["Objetivo"]), 0)
        if not count or int(count) <= 0:
            continue
        parent_norm = _sunburst_norm_key(parent_name)
        parent_id = line_id_by_name.get(parent_name) or _unique_id(f"line::{parent_norm}")
        obj_id = _unique_id(f"obj::{parent_norm}::{_sunburst_norm_key(obj_name)}")
        n_obj_linea = int(objetivos_por_linea.get(row["Linea"], 1) or 1)
        obj_weight = max(1.0, line_min_weight / max(1, n_obj_linea))
        labels.append(obj_name)
        ids.append(obj_id)
        parents.append(parent_id)
        values.append(obj_weight)
        pct = float(row["cumplimiento_pct"]) if pd.notna(row["cumplimiento_pct"]) else 0.0
        customdata.append([pct])
        colors.append(color_map.get(parent_norm, "#6B728E"))

    text: list[str] = []
    id_to_label = dict(zip(ids, labels))
    for lab, cd, parent_id in zip(labels, customdata, parents):
        pct = cd[0] if cd else 0.0
        lab_key = _sunburst_norm_key(lab)
        if lab_key in LABEL_WRAP_OVERRIDES:
            wrapped = LABEL_WRAP_OVERRIDES[lab_key]
        elif parent_id == "":
            wrapped = _wrap_sunburst_label(lab, width=12)
        else:
            parent_name = id_to_label.get(parent_id, "")
            wrapped = _wrap_sunburst_label(_objective_display_label(lab, parent_name), width=26)
        html_label = f"<b>{str(wrapped).replace(chr(10), '<br>')}</b>"
        text.append(f"{html_label}<br>{pct:.0f}%")

    return {
        "ids": ids,
        "labels": labels,
        "parents": parents,
        "values": values,
        "colors": colors,
        "text": text,
        "customdata": customdata,
    }


def compute_trends(current: pd.DataFrame, previous: pd.DataFrame) -> tuple[list[dict], list[dict]]:
    if current.empty or previous.empty or "Id" not in current.columns or "Id" not in previous.columns:
        return [], []

    name_col = "Indicador" if "Indicador" in current.columns else "Id"
    cur = (
        current[["Id", name_col, "cumplimiento_pct"] + (["Linea"] if "Linea" in current.columns else [])]
        .dropna(subset=["cumplimiento_pct"])
        .drop_duplicates(subset=["Id"], keep="first")
    )
    prev = (
        previous[["Id", "cumplimiento_pct"]]
        .dropna(subset=["cumplimiento_pct"])
        .drop_duplicates(subset=["Id"], keep="first")
    )
    if cur.empty or prev.empty:
        return [], []

    merged = cur.merge(prev, on="Id", suffixes=("", "_prev"))
    if merged.empty:
        return [], []
    merged["variation"] = merged["cumplimiento_pct"] - merged["cumplimiento_pct_prev"]

    def _row_to_dict(row, positive: bool) -> dict:
        linea = str(row["Linea"]) if "Linea" in row.index else ""
        return {
            "indicador": str(row[name_col]) if name_col in row.index else str(row["Id"]),
            "linea": linea,
            "linea_color": LINEA_COLORS_BADGE.get(norm_key(linea), "#6B728E"),
            "variacion": round(float(row["variation"]), 1),
            "positive": positive,
        }

    best = merged.sort_values("variation", ascending=False).head(5)
    worst = merged.sort_values("variation").head(5)
    return (
        [_row_to_dict(row, True) for _, row in best.iterrows()],
        [_row_to_dict(row, False) for _, row in worst.iterrows()],
    )


def _narrative_estado_por_cumplimiento(
    cumplimiento: float,
    *,
    excelente: float = 100.0,
    bueno: float = 95.0,
    moderado: float = 70.0,
) -> tuple[str, str, str]:
    if cumplimiento >= excelente:
        return "destacado", "#16A34A", "success"
    if cumplimiento >= bueno:
        return "sólido y en línea con las metas", "#2563EB", "chart"
    if cumplimiento >= moderado:
        return "con oportunidades de mejora", "#D97706", "warning"
    return "que requiere atención prioritaria", "#DC2626", "alert"


def generate_narrative_indicadores(
    df: pd.DataFrame,
    linea_summary: pd.DataFrame,
    chips: list[dict],
) -> dict[str, Any]:
    total_chip = next((c["value"] for c in chips if c["label"] == "Total"), 0)
    counts = {c["label"]: c["value"] for c in chips}
    health_rate = round(
        ((counts.get("Sobrecumplimiento", 0) + counts.get("Cumplimiento", 0)) / max(total_chip, 1)) * 100,
        1,
    )
    if health_rate >= 85:
        estado, color, icon = "sobresaliente", "#16A34A", "success"
    elif health_rate >= 70:
        estado, color, icon = "satisfactorio", "#2563EB", "chart"
    elif health_rate >= 50:
        estado, color, icon = "moderado con oportunidades de mejora", "#D97706", "warning"
    else:
        estado, color, icon = "crítico y requiere atención prioritaria", "#DC2626", "alert"

    mejor_linea = ""
    if not df.empty and "Linea" in df.columns and "cumplimiento_pct" in df.columns:
        top = df.groupby("Linea")["cumplimiento_pct"].mean().reset_index().sort_values("cumplimiento_pct", ascending=False)
        if not top.empty:
            ln = top.iloc[0]
            mejor_linea = (
                f'La línea <strong>{ln["Linea"]}</strong> lidera el cumplimiento con un promedio de '
                f'<strong>{ln["cumplimiento_pct"]:.1f}%</strong>. '
            )

    alerta = counts.get("Alerta", 0)
    peligro = counts.get("Peligro", 0)
    alerta_txt = (
        f"Se identifican <strong>{alerta}</strong> indicadores en alerta y <strong>{peligro}</strong> en peligro "
        f"que requieren seguimiento inmediato. "
        if alerta + peligro > 0
        else "No se registran indicadores en estado crítico en este corte. "
    )

    texto = (
        f'La institución presenta un desempeño estratégico <strong style="color:{color};">{estado}</strong>: '
        f"el <strong>{health_rate}%</strong> de los indicadores PDI se encuentran en niveles saludables "
        f"(<strong>{counts.get('Sobrecumplimiento', 0)}</strong> en sobrecumplimiento y "
        f"<strong>{counts.get('Cumplimiento', 0)}</strong> en cumplimiento sobre "
        f"<strong>{total_chip}</strong> totales). {mejor_linea}{alerta_txt}"
    )
    return {"texto": texto, "estado_color": color, "estado_icon": icon, "health_rate": health_rate}


RETOS_UMBRAL_CUMPLIMIENTO = 95.0
RETOS_UMBRAL_ALERTA = 80.0
RETOS_UMBRAL_SOBRECUMPLIMIENTO = 105.0


def _retos_category(pct: float | None) -> str:
    """Categoría Plan de Retos: cumple desde 95% (régimen PA)."""
    if pd.isna(pct):
        return "Sin dato"
    pct = float(pct)
    if pct >= RETOS_UMBRAL_SOBRECUMPLIMIENTO:
        return "Sobrecumplimiento"
    if pct >= RETOS_UMBRAL_CUMPLIMIENTO:
        return "Cumplimiento"
    if pct >= RETOS_UMBRAL_ALERTA:
        return "Alerta"
    return "Peligro"


def build_linea_summary_retos(
    linea_df: pd.DataFrame,
    objetivo_df: pd.DataFrame | None = None,
    planes_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    cols = ["Linea", "N_Indicadores", "Cumpl_Promedio", "Sobrecumplimiento", "Cumplimiento", "Alerta", "Peligro"]
    if linea_df.empty or "Linea" not in linea_df.columns:
        return pd.DataFrame(columns=cols)

    df = linea_df.copy()
    df["Nivel de cumplimiento"] = df["cumplimiento_pct"].apply(_retos_category)

    if objetivo_df is not None and "Linea" in objetivo_df.columns and "Objetivo" in objetivo_df.columns:
        objetivos_count = (
            objetivo_df.groupby("Linea", dropna=False)
            .agg(N_Indicadores=("Objetivo", lambda s: s.dropna().astype(str).str.strip().replace("", pd.NA).dropna().nunique()))
            .reset_index()
        )
    else:
        objetivos_count = df.groupby("Linea", dropna=False).agg(N_Indicadores=("cumplimiento_pct", "size")).reset_index()

    resumen = (
        df.groupby("Linea", dropna=False)
        .agg(
            Cumpl_Promedio=("cumplimiento_pct", "mean"),
            Sobrecumplimiento=("Nivel de cumplimiento", lambda s: (s == "Sobrecumplimiento").sum()),
            Cumplimiento=("Nivel de cumplimiento", lambda s: (s == "Cumplimiento").sum()),
            Alerta=("Nivel de cumplimiento", lambda s: (s == "Alerta").sum()),
            Peligro=("Nivel de cumplimiento", lambda s: (s == "Peligro").sum()),
        )
        .reset_index()
    )
    resumen = resumen.merge(objetivos_count, on="Linea", how="left")

    if planes_df is not None and not planes_df.empty and "Linea" in planes_df.columns and "N_Planes" in planes_df.columns:
        planes = planes_df.copy()
        planes["Linea_norm"] = planes["Linea"].astype(str).apply(norm_key)
        planes_count = planes.groupby("Linea_norm", dropna=False).agg(N_Planes=("N_Planes", "sum")).reset_index()
        resumen["Linea_norm"] = resumen["Linea"].astype(str).apply(norm_key)
        resumen = resumen.merge(planes_count, on="Linea_norm", how="left")
        resumen["N_Indicadores"] = resumen["N_Planes"].fillna(resumen["N_Indicadores"]).astype(int)
        resumen = resumen.drop(columns=["Linea_norm", "N_Planes"], errors="ignore")

    return resumen


def merge_consolidado_summaries(
    s1: pd.DataFrame,
    s2: pd.DataFrame,
    s3: pd.DataFrame,
    o1: pd.DataFrame,
    o2: pd.DataFrame,
    o3: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    def _clean_label(value):
        if pd.isna(value):
            return ""
        text = str(value).strip().replace("_", " ")
        text = re.sub(r"\s+", " ", text)
        return text

    def _normalize_summary(summary: pd.DataFrame) -> pd.DataFrame:
        out = summary.copy()
        if "Linea" in out.columns:
            out["Linea_norm"] = out["Linea"].astype(str).apply(norm_key)
        return out

    s1n, s2n, s3n = _normalize_summary(s1), _normalize_summary(s2), _normalize_summary(s3)
    frames = [df[["Linea_norm"]] for df in [s1n, s2n, s3n] if "Linea_norm" in df.columns]
    if not frames:
        return pd.DataFrame(), pd.concat([o1, o2, o3], ignore_index=True)

    all_lineas = pd.concat(frames).drop_duplicates()
    out = all_lineas.copy().set_index("Linea_norm")
    out["N_Indicadores"] = 0
    out["N_Proyectos"] = 0
    out["N_Retos"] = 0

    if "Linea_norm" in s1n.columns and "N_Indicadores" in s1n.columns:
        out["N_Indicadores"] = pd.to_numeric(s1n.set_index("Linea_norm")["N_Indicadores"], errors="coerce")
    if "Linea_norm" in s2n.columns and "N_Proyectos" in s2n.columns:
        out["N_Proyectos"] = pd.to_numeric(s2n.set_index("Linea_norm")["N_Proyectos"], errors="coerce")
    if "Linea_norm" in s3n.columns and "N_Indicadores" in s3n.columns:
        out["N_Retos"] = pd.to_numeric(s3n.set_index("Linea_norm")["N_Indicadores"], errors="coerce")

    out["N_Indicadores"] = out["N_Indicadores"].fillna(0).astype(int)
    out["N_Proyectos"] = out["N_Proyectos"].fillna(0).astype(int)
    out["N_Retos"] = out["N_Retos"].fillna(0).astype(int)
    out["N_Total"] = out[["N_Indicadores", "N_Proyectos", "N_Retos"]].sum(axis=1).astype(int)

    def _avg_series(summary, name):
        if "Linea_norm" in summary.columns and "Cumpl_Promedio" in summary.columns:
            return pd.to_numeric(summary.set_index("Linea_norm")["Cumpl_Promedio"], errors="coerce").rename(name)
        return pd.Series(name=name, dtype="float64")

    out = out.join(
        [_avg_series(s1n, "Cumpl_Promedio_Indicadores"), _avg_series(s2n, "Cumpl_Promedio_Proyectos"), _avg_series(s3n, "Cumpl_Promedio_Retos")],
        how="left",
    )
    out["Cumpl_Promedio"] = out[
        ["Cumpl_Promedio_Indicadores", "Cumpl_Promedio_Proyectos", "Cumpl_Promedio_Retos"]
    ].mean(axis=1, skipna=True).fillna(0)

    for col in ["Sobrecumplimiento", "Cumplimiento", "Alerta", "Peligro"]:
        vals = []
        for summary in [s1n, s2n, s3n]:
            if col in summary.columns and "Linea_norm" in summary.columns:
                vals.append(summary.set_index("Linea_norm")[col])
        out[col] = pd.to_numeric(pd.concat(vals, axis=1).fillna(0).sum(axis=1), errors="coerce").fillna(0).astype(int) if vals else 0

    labels = {}
    for summary in [s1n, s2n, s3n]:
        if "Linea" in summary.columns and "Linea_norm" in summary.columns:
            for _, row in summary[["Linea", "Linea_norm"]].drop_duplicates().iterrows():
                key = row["Linea_norm"]
                if key and key not in labels:
                    labels[key] = _clean_label(row["Linea"])

    out = out.reset_index()
    out["Linea"] = out["Linea_norm"].map(labels).fillna(out["Linea_norm"])
    objetivo_df = pd.concat([o1, o2, o3], ignore_index=True)
    return out, objetivo_df


def get_chip_config_retos(linea_df: pd.DataFrame, area_count: int) -> list[dict]:
    total_planes = int(linea_df["N_Indicadores"].sum()) if not linea_df.empty and "N_Indicadores" in linea_df.columns else 0
    meta_esperada = 100.0
    ejecucion_real = float(linea_df["Cumpl_Promedio"].mean()) if not linea_df.empty and "Cumpl_Promedio" in linea_df.columns else 0.0
    cumplimiento = round((ejecucion_real / meta_esperada) * 100, 1) if meta_esperada else 0.0
    return [
        {"value": total_planes, "label": "Plan de Retos", "color": "#0B5FFF"},
        {"value": f"{meta_esperada:.0f}%", "label": "% Meta Esperada", "color": "#6B7280"},
        {"value": f"{ejecucion_real:.1f}%", "label": "% Ejecución Real", "color": "#2563EB"},
        {"value": f"{cumplimiento:.1f}%", "label": "Cumplimiento", "color": "#16A34A" if cumplimiento >= 100 else "#F59E0B"},
        {"value": area_count, "label": "Áreas con retos", "color": "#7C3AED"},
    ]


def get_chip_config_consolidado(
    linea_summary: pd.DataFrame,
    ind_count: int,
    proy_count: int,
    retos_count: int,
) -> list[dict]:
    cumpl_pdi = float(linea_summary["Cumpl_Promedio"].mean()) if not linea_summary.empty else 0.0
    return [
        {"value": f"{cumpl_pdi:.1f}%", "label": "Cumplimiento PDI %", "color": "#0B5FFF"},
        {"value": ind_count, "label": "Indicadores", "color": "#173D66"},
        {"value": proy_count, "label": "Proyectos", "color": "#16A34A"},
        {"value": retos_count, "label": "Plan de Retos", "color": "#7C3AED"},
    ]


def generate_narrative_proyectos(proy_df: pd.DataFrame, linea_summary: pd.DataFrame) -> dict[str, Any]:
    count_col = "N_Proyectos" if "N_Proyectos" in linea_summary.columns else "N_Indicadores"
    total_proy = int(linea_summary[count_col].sum()) if not linea_summary.empty and count_col in linea_summary.columns else 0
    cerrados = en_ejecucion = en_planeacion = 0
    cumplimiento_prom = 0.0
    if not proy_df.empty and "cumplimiento_pct" in proy_df.columns:
        unique = proy_df.drop_duplicates("Id", keep="last") if "Id" in proy_df.columns else proy_df
        cumplimiento_prom = float(unique["cumplimiento_pct"].mean())
        for _, row in unique.iterrows():
            cumpl = row.get("cumplimiento_pct")
            if pd.isna(cumpl) or cumpl == 0:
                en_planeacion += 1
            elif cumpl >= 100:
                cerrados += 1
            else:
                en_ejecucion += 1

    if cumplimiento_prom >= 100:
        estado, color, icon = "proyectos completados exitosamente", "#16A34A", "success"
    elif cumplimiento_prom >= 70:
        estado, color, icon = "proyectos en ejecución con buen avance", "#2563EB", "chart"
    elif cumplimiento_prom >= 50:
        estado, color, icon = "proyectos con avances parciales", "#D97706", "warning"
    else:
        estado, color, icon = "proyectos requieren atención prioritaria", "#DC2626", "alert"

    mejor_linea = ""
    if not linea_summary.empty and "Linea" in linea_summary.columns and "Cumpl_Promedio" in linea_summary.columns:
        top = linea_summary.sort_values("Cumpl_Promedio", ascending=False).iloc[0]
        mejor_linea = (
            f'La línea <strong>{top["Linea"]}</strong> concentra el mejor desempeño '
            f'(<strong>{float(top["Cumpl_Promedio"]):.1f}%</strong> de cumplimiento). '
        )

    texto = (
        f'El portafolio de proyectos institucionales presenta un estado <strong style="color:{color};">{estado}</strong>. '
        f"De los <strong>{total_proy}</strong> proyectos PDI registrados, "
        f"<strong>{cerrados}</strong> están cerrados (100%), "
        f"<strong>{en_ejecucion}</strong> en ejecución, y "
        f"<strong>{en_planeacion}</strong> en fase de planeación. "
        f"El cumplimiento promedio del portafolio es de <strong>{cumplimiento_prom:.1f}%</strong>. "
        f"{mejor_linea}"
    )
    return {"texto": texto, "estado_color": color, "estado_icon": icon, "health_rate": round(cumplimiento_prom, 1)}


def generate_narrative_retos(linea_summary: pd.DataFrame) -> dict[str, Any]:
    total_retos = int(linea_summary["N_Indicadores"].sum()) if not linea_summary.empty else 0
    cumplimiento_prom = float(linea_summary["Cumpl_Promedio"].mean()) if not linea_summary.empty else 0.0
    if cumplimiento_prom >= RETOS_UMBRAL_SOBRECUMPLIMIENTO:
        estado, color, icon = "retos con sobrecumplimiento", "#16A34A", "success"
    elif cumplimiento_prom >= RETOS_UMBRAL_CUMPLIMIENTO:
        estado, color, icon = "retos en cumplimiento", "#16A34A", "success"
    elif cumplimiento_prom >= RETOS_UMBRAL_ALERTA:
        estado, color, icon = "retos en buen avance", "#2563EB", "chart"
    elif cumplimiento_prom >= 50:
        estado, color, icon = "retos con avances parciales", "#D97706", "warning"
    else:
        estado, color, icon = "retos requieren atención", "#DC2626", "alert"

    mejor_linea = alerta_lineas = ""
    if not linea_summary.empty and "Linea" in linea_summary.columns and "Cumpl_Promedio" in linea_summary.columns:
        ranked = linea_summary.sort_values("Cumpl_Promedio", ascending=False)
        top = ranked.iloc[0]
        mejor_linea = (
            f'La línea <strong>{top["Linea"]}</strong> lidera con '
            f'<strong>{float(top["Cumpl_Promedio"]):.1f}%</strong> de cumplimiento. '
        )
        bajo_umbral = ranked[ranked["Cumpl_Promedio"] < RETOS_UMBRAL_CUMPLIMIENTO]
        if not bajo_umbral.empty:
            nombres = ", ".join(f'<strong>{row["Linea"]}</strong>' for _, row in bajo_umbral.iterrows())
            alerta_lineas = (
                f"{len(bajo_umbral)} línea(s) están por debajo del umbral de cumplimiento "
                f"({RETOS_UMBRAL_CUMPLIMIENTO:.0f}%): {nombres}. "
            )
        else:
            alerta_lineas = (
                f"Todas las líneas estratégicas superan el umbral de cumplimiento "
                f"({RETOS_UMBRAL_CUMPLIMIENTO:.0f}%). "
            )

    texto = (
        f'El Plan de Retos presenta un estado <strong style="color:{color};">{estado}</strong>. '
        f"Se registran <strong>{total_retos}</strong> retos con un cumplimiento promedio de "
        f"<strong>{cumplimiento_prom:.1f}%</strong> respecto a las metas establecidas "
        f"(umbral de cumplimiento desde <strong>{RETOS_UMBRAL_CUMPLIMIENTO:.0f}%</strong>). "
        f"{mejor_linea}{alerta_lineas}"
    )
    return {"texto": texto, "estado_color": color, "estado_icon": icon, "health_rate": round(cumplimiento_prom, 1)}


def generate_narrative_consolidado(
    linea_summary: pd.DataFrame,
    *,
    ind_count: int,
    proy_count: int,
    retos_count: int,
    anio: int,
) -> dict[str, Any]:
    cumpl_pdi = float(linea_summary["Cumpl_Promedio"].mean()) if not linea_summary.empty else 0.0
    total_elementos = ind_count + proy_count + retos_count
    estado, color, icon = _narrative_estado_por_cumplimiento(cumpl_pdi)

    mejor_linea = brecha_linea = distribucion = ""
    if not linea_summary.empty and "Linea" in linea_summary.columns:
        work = linea_summary.copy()
        if "Cumpl_Promedio" in work.columns:
            ranked = work.sort_values("Cumpl_Promedio", ascending=False)
            best = ranked.iloc[0]
            mejor_linea = (
                f'La línea <strong>{best["Linea"]}</strong> lidera el cumplimiento integrado '
                f'con <strong>{float(best["Cumpl_Promedio"]):.1f}%</strong>. '
            )
            if len(ranked) > 1:
                worst = ranked.iloc[-1]
                brecha = float(best["Cumpl_Promedio"]) - float(worst["Cumpl_Promedio"])
                if brecha >= 3:
                    brecha_linea = (
                        f'La mayor brecha se observa frente a <strong>{worst["Linea"]}</strong> '
                        f'(<strong>{float(worst["Cumpl_Promedio"]):.1f}%</strong>). '
                    )

        if {"N_Indicadores", "N_Proyectos", "N_Retos"}.issubset(work.columns):
            ind_linea = int(work["N_Indicadores"].sum())
            proy_linea = int(work["N_Proyectos"].sum())
            ret_linea = int(work["N_Retos"].sum())
            distribucion = (
                f"Por línea estratégica se monitorean <strong>{ind_linea}</strong> indicadores, "
                f"<strong>{proy_linea}</strong> proyectos y <strong>{ret_linea}</strong> retos. "
            )

    texto = (
        f'La visión consolidada del PDI <strong>{anio}</strong> muestra un desempeño institucional '
        f'<strong style="color:{color};">{estado}</strong>, con un cumplimiento promedio integrado de '
        f'<strong>{cumpl_pdi:.1f}%</strong>. El portafolio reúne '
        f'<strong>{ind_count}</strong> indicadores estratégicos, <strong>{proy_count}</strong> proyectos y '
        f"<strong>{retos_count}</strong> retos "
        f"(<strong>{total_elementos}</strong> elementos en conjunto). "
        f"{mejor_linea}{brecha_linea}{distribucion}"
    )
    return {
        "texto": texto,
        "estado_color": color,
        "estado_icon": icon,
        "health_rate": round(cumpl_pdi, 1),
    }


def build_proyectos_gantt(
    proy_df: pd.DataFrame,
    *,
    anio_min: int = 2022,
    anio_max: int = 2026,
) -> dict[str, Any]:
    """Cronograma de proyectos: vigencia activa por año dentro del horizonte PDI."""
    empty = {"anio_min": anio_min, "anio_max": anio_max, "items": []}
    if proy_df.empty or "Id" not in proy_df.columns:
        return empty

    work = proy_df.copy()
    work["Anio"] = pd.to_numeric(work.get("Anio"), errors="coerce")
    work = work[work["Anio"].between(anio_min, anio_max)]
    if work.empty:
        return empty

    sort_cols = ["Id"]
    if "Fecha" in work.columns:
        sort_cols.append("Fecha")
    elif "Mes" in work.columns:
        sort_cols.append("Mes")
    work = work.sort_values(sort_cols)

    items: list[dict[str, Any]] = []
    for project_id, group in work.groupby("Id", sort=False):
        anios = sorted({int(a) for a in group["Anio"].dropna().unique()})
        if not anios:
            continue

        latest = group.iloc[-1]
        nombre = str(latest.get("Indicador") or project_id).strip()
        linea = str(latest.get("Linea") or "Sin línea").strip()
        cumpl = _safe_pct(latest.get("cumplimiento_pct"), default=0.0) or 0.0
        estado = "Planeación"
        if cumpl > 0:
            estado = "Cerrado" if cumpl >= 100 else "En ejecución"

        linea_key = norm_key(linea)
        linea_color = LINEA_COLORS_BADGE.get(linea_key, "#64748B")
        anio_inicio = min(anios)
        anio_fin = max(anios)

        items.append(
            {
                "id": str(project_id),
                "nombre": nombre,
                "linea": linea,
                "linea_color": linea_color,
                "anio_inicio": anio_inicio,
                "anio_fin": anio_fin,
                "duracion_anios": anio_fin - anio_inicio + 1,
                "anios_activos": anios,
                "cumplimiento": cumpl,
                "estado": estado,
            }
        )

    items.sort(key=lambda x: (linea_sort_key(x["linea"]), x["nombre"].lower()))
    return {"anio_min": anio_min, "anio_max": anio_max, "items": items}


def build_proyectos_tabla(proy_df: pd.DataFrame) -> list[dict]:
    if proy_df.empty:
        return []
    cols = ["Id", "Indicador", "Linea", "cumplimiento_pct", "Nivel de cumplimiento"]
    work = ensure_nivel_cumplimiento(proy_df.copy())
    available = [c for c in cols if c in work.columns]
    if not available:
        return []
    rows = []
    for linea in sorted(work["Linea"].dropna().unique(), key=linea_sort_key) if "Linea" in work.columns else [""]:
        sub = work[work["Linea"] == linea] if linea else work
        for _, row in sub.drop_duplicates("Id", keep="last").iterrows():
            cumpl = row.get("cumplimiento_pct")
            estado = "Planeación"
            if pd.notna(cumpl) and cumpl > 0:
                estado = "Cerrado" if cumpl >= 100 else "En ejecución"
            rows.append(
                {
                    "linea": str(linea or row.get("Linea", "")),
                    "id": str(row.get("Id", "")),
                    "nombre": str(row.get("Indicador", row.get("Id", ""))),
                    "cumplimiento": round(float(cumpl), 1) if pd.notna(cumpl) else 0.0,
                    "estado": estado,
                    "nivel": str(row.get("Nivel de cumplimiento", "")),
                }
            )
    return rows


def build_retos_tabla(linea_df: pd.DataFrame) -> list[dict]:
    if linea_df.empty or "Linea" not in linea_df.columns:
        return []
    return [
        {
            "linea": str(row["Linea"]),
            "cumplimiento": round(float(row.get("cumplimiento_pct", 0) or 0), 1),
            "nivel": _retos_category(row.get("cumplimiento_pct")),
        }
        for _, row in linea_df.iterrows()
    ]
