"""Constructores Informe por Procesos — auditoría, propuestas, resumen ejecutivo."""

from __future__ import annotations

import unicodedata
from typing import Any

import pandas as pd

_PROPUESTAS_PATH = "raw/Propuesta Indicadores/Indicadores Propuestos.xlsx"
_AUDITORIA_PATH = "raw/Auditoria/auditoria_resultado.xlsx"

SOURCE_STYLES = {
    "Retos": {"bg": "#e8f5e9", "border": "#66bb6a", "title": "#1b5e20"},
    "Proyectos": {"bg": "#e3f2fd", "border": "#42a5f5", "title": "#0d47a1"},
    "Plan de mejoramiento": {"bg": "#fff3e0", "border": "#ffb74d", "title": "#e65100"},
    "Calidad": {"bg": "#f3e5f5", "border": "#ba68c8", "title": "#4a148c"},
}

_CAT_STYLE = {
    "fortalezas": ("Fortalezas", "#d1f5e0", "#0a5c36", "#1aaa6b", "✅"),
    "oportunidades_mejora": ("Oportunidades de Mejora", "#fff3cd", "#7a5000", "#e6a800", "🔄"),
    "hallazgos": ("Hallazgos", "#dbeeff", "#003d8f", "#1a6fdb", "🔍"),
    "no_conformidades": ("No Conformidades", "#fde0e0", "#7a0000", "#e63535", "⚠️"),
    "recomendacion_desempeno": ("Recomendación Desempeño", "#ede0ff", "#3d0080", "#7c3aed", "💡"),
}


def _norm_text(value: object) -> str:
    text = str(value or "").strip().upper()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def build_resumen_ejecutivo(
    indicadores: list[dict[str, Any]],
    base_indicadores: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not indicadores:
        return {
            "score": 0, "avg": 0, "label": "En riesgo",
            "total_indicadores": 0, "cumple": 0, "alerta": 0, "peligro": 0, "sin_dato": 0, "delta": None,
        }
    pcts = [i.get("cumplimiento_pct") for i in indicadores if i.get("cumplimiento_pct") is not None]
    avg = sum(pcts) / len(pcts) if pcts else 0.0
    score = min(100.0, avg)
    cumple = sum(1 for p in pcts if p >= 100)
    alerta = sum(1 for p in pcts if 80 <= p < 100)
    peligro = sum(1 for p in pcts if p < 80)
    sin_dato = len(indicadores) - len(pcts)
    delta = None
    if base_indicadores:
        base_pcts = [i.get("cumplimiento_pct") for i in base_indicadores if i.get("cumplimiento_pct") is not None]
        if base_pcts:
            delta = round(avg - sum(base_pcts) / len(base_pcts), 1)
    return {
        "score": round(score, 1),
        "avg": round(avg, 1),
        "label": "Saludable" if score >= 95 else ("Estable" if score >= 80 else "En riesgo"),
        "total_indicadores": len(indicadores),
        "cumple": cumple,
        "alerta": alerta,
        "peligro": peligro,
        "sin_dato": sin_dato,
        "delta": delta,
    }


def build_comparativa_anual(historico: list[dict[str, Any]], mes: int, limit: int = 4) -> list[dict[str, Any]]:
    """Usa vista_global.comparativa_anual del dashboard si está disponible."""
    if not historico:
        return []
    by_year: dict[int, list[float]] = {}
    for h in historico:
        anio = h.get("anio")
        cumpl = h.get("cumplimiento")
        if anio is not None and cumpl is not None:
            by_year.setdefault(int(anio), []).append(float(cumpl))
    years = sorted(by_year.keys())[-limit:]
    return [
        {"anio": y, "cumplimiento": round(sum(by_year[y]) / len(by_year[y]), 1)}
        for y in years
    ]


def build_criticos(indicadores: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    crit = [i for i in indicadores if (i.get("cumplimiento_pct") or 100) < 80]
    crit.sort(key=lambda x: x.get("cumplimiento_pct") or 0)
    return crit[:limit]


def build_analisis_ia(indicadores: list[dict[str, Any]]) -> dict[str, Any]:
    peligro = [i for i in indicadores if (i.get("cumplimiento_pct") or 100) < 80]
    alerta = [i for i in indicadores if 80 <= (i.get("cumplimiento_pct") or 0) < 100]
    saludables = [i for i in indicadores if (i.get("cumplimiento_pct") or 0) >= 100]
    def _pick(lst, n=20):
        out = []
        for i in lst[:n]:
            out.append({
                "indicador": i.get("indicador") or i.get("nombre"),
                "proceso": i.get("proceso"),
                "subproceso": i.get("subproceso"),
                "cumplimiento_pct": i.get("cumplimiento_pct"),
            })
        return out
    return {
        "conteos": {"peligro": len(peligro), "alerta": len(alerta), "saludables": len(saludables)},
        "top_peligro": _pick(sorted(peligro, key=lambda x: x.get("cumplimiento_pct") or 0)),
        "top_alerta": _pick(sorted(alerta, key=lambda x: x.get("cumplimiento_pct") or 0)),
    }


def load_propuestas(excel, proceso: str = "Todos", subproceso: str = "Todos") -> tuple[list[dict[str, Any]], str | None]:
    path = excel.data_root / _PROPUESTAS_PATH
    if not path.exists():
        return [], f"No existe el archivo: {_PROPUESTAS_PATH}"
    try:
        retos = excel.read_excel(_PROPUESTAS_PATH, sheet_name="Retos")
        retos_f = retos[retos["Aplica Desempeño"].astype(str).str.upper() == "SI"][
            ["Proceso", "Subproceso", "Indicador Propuesto"]
        ].dropna(subset=["Indicador Propuesto"])
        retos_f = retos_f.copy()
        retos_f["Fuente"] = "Retos"

        proyectos = excel.read_excel(_PROPUESTAS_PATH, sheet_name="Proyectos")
        proyectos_f = proyectos[proyectos["Propuesta"].astype(str).str.upper() == "SI"][
            ["Proceso", "Subproceso", "Nombre del Indicador Propuesto"]
        ].rename(columns={"Nombre del Indicador Propuesto": "Indicador Propuesto"})
        proyectos_f = proyectos_f.dropna(subset=["Indicador Propuesto"]).copy()
        proyectos_f["Fuente"] = "Proyectos"

        plan = pd.read_excel(path, sheet_name="Plan de mejoramiento", header=1, engine="openpyxl")
        plan_f = plan[plan["Propuesta Indicador"].astype(str).str.upper() == "SI"][
            ["Proceso", "Subproceso", "INDICADOR DE RESULTADO O IMPACTO"]
        ].rename(columns={"INDICADOR DE RESULTADO O IMPACTO": "Indicador Propuesto"})
        plan_f = plan_f.dropna(subset=["Indicador Propuesto"]).copy()
        plan_f["Fuente"] = "Plan de mejoramiento"

        calidad = excel.read_excel(_PROPUESTAS_PATH, sheet_name="Calidad")
        calidad_f = calidad[["Proceso", "Subroceso", "Propuesta SGC (Indicadores)"]].rename(
            columns={"Subroceso": "Subproceso", "Propuesta SGC (Indicadores)": "Indicador Propuesto"}
        ).dropna(subset=["Indicador Propuesto"])
        calidad_f["Fuente"] = "Calidad"

        df_final = pd.concat([retos_f, proyectos_f, plan_f, calidad_f], ignore_index=True)
        df_final = df_final.drop_duplicates(subset=["Proceso", "Subproceso", "Indicador Propuesto", "Fuente"])

        if proceso != "Todos":
            pn = _norm_text(proceso)
            df_final = df_final[df_final["Proceso"].astype(str).map(_norm_text) == pn]
        if subproceso != "Todos":
            sn = _norm_text(subproceso)
            df_final = df_final[df_final["Subproceso"].astype(str).map(_norm_text) == sn]

        records = []
        for _, row in df_final.iterrows():
            fuente = str(row["Fuente"])
            records.append({
                "proceso": str(row["Proceso"]),
                "subproceso": str(row["Subproceso"]),
                "indicador": str(row["Indicador Propuesto"]),
                "fuente": fuente,
                "style": SOURCE_STYLES.get(fuente, {}),
            })
        return records, None
    except Exception as exc:
        return [], f"Error procesando propuestas: {exc}"


def load_auditoria(excel, proceso: str = "Todos") -> tuple[list[dict[str, Any]], str | None]:
    path = excel.data_root / _AUDITORIA_PATH
    if not path.exists():
        return [], f"No existe el archivo: {_AUDITORIA_PATH}"
    try:
        df = excel.read_excel(_AUDITORIA_PATH)
    except Exception as exc:
        return [], f"No se pudo leer auditoría: {exc}"
    if df.empty:
        return [], "La hoja de auditoría está vacía."

    df.columns = [str(c).strip().lower() for c in df.columns]
    if proceso and proceso.upper() != "TODOS" and "proceso" in df.columns:
        mask = df["proceso"].astype(str).str.upper().str.contains(proceso.upper(), na=False)
        df = df[mask]

    secciones = []
    for tipo in ("interna", "externa"):
        titulo = "Auditoría Interna" if tipo == "interna" else "Auditoría Externa – Icontec 2025"
        fichas = []
        for _, row in df.iterrows():
            proceso_nombre = str(row.get("proceso", "")).strip()
            categorias = []
            for campo, estilo in _CAT_STYLE.items():
                col_name = f"{campo}_{tipo}"
                valor = str(row.get(col_name, "")).strip()
                if valor:
                    label, pill_bg, pill_text, dot_color, emoji = estilo
                    categorias.append({
                        "campo": campo,
                        "label": label,
                        "valor": valor,
                        "pill_bg": pill_bg,
                        "pill_text": pill_text,
                        "dot_color": dot_color,
                        "emoji": emoji,
                    })
            if categorias:
                fichas.append({"proceso": proceso_nombre, "categorias": categorias})
        secciones.append({"tipo": tipo, "titulo": titulo, "fichas": fichas})
    return secciones, None
