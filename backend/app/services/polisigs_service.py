"""Indicadores asociados a la Política POLISIGS.

- Catálogo (objetivo, componente, clasificación, responsable…):
  data/raw/POLISIGS/Indicadores Polisigs.xlsx
- Meta / Ejecución / Cumplimiento: Resultados Consolidados (mismo tracking que el
  CMI), año 2026, último periodo reportado de cada indicador.

El consolidado de un objetivo (y de la política) es el promedio simple del
cumplimiento de los indicadores con dato, igual que `avg_cumplimiento` del CMI.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from threading import Lock
from typing import Any

import pandas as pd

from app.domain.categorization import categorizar_cumplimiento
from app.domain.resumen_builders import ensure_nivel_cumplimiento
from app.services.excel_reader import ExcelReaderService
from app.services.tracking_cache import get_tracking_dataframe

ANIO = 2026
_ARCHIVO = Path("raw") / "POLISIGS" / "Indicadores Polisigs.xlsx"
_PENDIENTE = "Pendiente de reporte"
_OBJETIVOS_JSON = Path(__file__).resolve().parent.parent / "data" / "polisigs_objetivos.json"

_catalogo_cache: dict[str, Any] = {"mtime": None, "df": None}
_lock = Lock()


def _num(v: Any) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def _txt(v: Any) -> str | None:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    s = str(v).strip()
    return s or None


def _id(v: Any) -> str:
    return re.sub(r"\.0$", "", str(v).strip())


def _load_catalogo(excel: ExcelReaderService) -> pd.DataFrame:
    path = excel.data_root.resolve() / _ARCHIVO
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}")
    mtime = path.stat().st_mtime
    with _lock:
        if _catalogo_cache["mtime"] != mtime:
            _catalogo_cache["df"] = pd.read_excel(path)
            _catalogo_cache["mtime"] = mtime
        return _catalogo_cache["df"]


def _ultimo_2026(excel: ExcelReaderService) -> dict[str, dict[str, Any]]:
    """Último registro 2026 por Id (preferimos el último con ejecución reportada)."""
    tracking = get_tracking_dataframe(excel, historico=False)
    if tracking.empty or "Anio" not in tracking.columns:
        return {}
    df = tracking[pd.to_numeric(tracking["Anio"], errors="coerce") == ANIO].copy()
    if df.empty:
        return {}
    # Cumplimiento_norm (fracción) lo calcula el ETL con las reglas del CMI.
    df["cumplimiento_pct"] = pd.to_numeric(df.get("Cumplimiento_norm"), errors="coerce") * 100
    df = ensure_nivel_cumplimiento(df)
    df["_id"] = df["Id"].map(_id)
    df["_rep"] = pd.to_numeric(df["Ejecucion"], errors="coerce").notna()
    sort_cols = ["_rep"] + (["Fecha"] if "Fecha" in df.columns else [])
    df = df.sort_values(sort_cols).drop_duplicates("_id", keep="last")
    return {r["_id"]: r for r in df.to_dict("records")}


def _nivel_consolidado(pct: float | None) -> str:
    return _PENDIENTE if pct is None else categorizar_cumplimiento(pct / 100.0)


def _consolidar(inds: list[dict[str, Any]]) -> dict[str, Any]:
    vals = [i["cumplimiento_pct"] for i in inds if i["cumplimiento_pct"] is not None]
    avg = round(sum(vals) / len(vals), 1) if vals else None
    niveles = [i["Nivel de cumplimiento"] for i in inds]
    return {
        "cumplimiento": avg,
        "nivel": _nivel_consolidado(avg),
        "total": len(inds),
        "con_dato": len(vals),
        "sobrecumple": niveles.count("Sobrecumplimiento"),
        "cumple": niveles.count("Cumplimiento"),
        "alerta": niveles.count("Alerta"),
        "peligro": niveles.count("Peligro"),
        "sin_dato": len(inds) - len(vals),
    }


def _load_objetivos() -> dict[str, Any]:
    return json.loads(_OBJETIVOS_JSON.read_text(encoding="utf-8"))


def _compromiso(label: str) -> str:
    """'1. Alta calidad académica' -> 'Alta calidad académica' (compromiso de la política)."""
    return re.sub(r"^\s*\d+\.\s*", "", label).strip()


def _objetivos_de(cfg: dict[str, Any], ind_id: str, componente: str | None) -> list[int]:
    """Objetivos V6 de un indicador: regla por ID y, si no hay, la del componente."""
    por_id = cfg.get("por_id", {})
    if ind_id in por_id:
        return list(por_id[ind_id])
    return list(cfg.get("por_componente", {}).get(componente or "", []))


def get_polisigs(excel: ExcelReaderService) -> dict[str, Any]:
    cfg = _load_objetivos()
    catalogo = _load_catalogo(excel)
    datos = _ultimo_2026(excel)

    indicadores: list[dict[str, Any]] = []
    for r in catalogo.to_dict("records"):
        ind_id = _id(r["ID"])
        d = datos.get(ind_id, {})
        componente = _txt(r.get("Componente del objetivo"))
        pct = _num(d.get("cumplimiento_pct"))
        indicadores.append(
            {
                "Id": ind_id,
                "Indicador": _txt(d.get("Indicador")) or _txt(r.get("Indicador")) or "",
                "objetivos": _objetivos_de(cfg, ind_id, componente),
                "compromiso": _compromiso(str(r["Objetivo de la política"])),
                "componente": componente,
                "proceso": _txt(d.get("Proceso")) or _txt(r.get("Proceso")),
                "responsable": _txt(r.get("Responsable")),
                "tipo_medicion": _txt(r.get("Tipo de medición")),
                "frecuencia": _txt(d.get("Periodicidad")) or _txt(r.get("Frecuencia")),
                "sentido": _txt(d.get("Sentido")) or _txt(r.get("Sentido")),
                "clasificacion": _txt(r.get("Clasificación")),
                "objetivo_secundario": _txt(r.get("Objetivo secundario")),
                "justificacion": _txt(r.get("Justificación")),
                # Mismos nombres de campo que el listado del CMI (fmtMeta/fmtEjecucion).
                "Meta": _num(d.get("Meta")),
                "Ejecucion": _num(d.get("Ejecucion")),
                "Meta_Signo": _txt(d.get("Meta_Signo")),
                "Decimales_Meta": _num(d.get("Decimales_Meta")),
                "periodo": _txt(d.get("Periodo")),
                "cumplimiento_pct": None if pct is None else round(pct, 1),
                "Nivel de cumplimiento": d.get("Nivel de cumplimiento") or _PENDIENTE,
            }
        )

    objetivos: list[dict[str, Any]] = []
    for o in cfg["objetivos"]:
        # Un indicador puede repetirse en varios objetivos.
        items = [i for i in indicadores if o["numero"] in i["objetivos"]]
        comps: dict[str, list[dict[str, Any]]] = {}
        for i in items:
            comps.setdefault(i["componente"] or "Sin componente", []).append(i)
        objetivos.append(
            {
                "numero": o["numero"],
                "nombre": o["nombre"],
                "corto": o["corto"],
                **_consolidar(items),
                "componentes": [{"nombre": n, **_consolidar(v)} for n, v in comps.items()],
            }
        )

    return {
        "anio": ANIO,
        "version_objetivos": cfg["version"],
        "politica": {"nombre": "Política POLISIGS V6", **_consolidar(indicadores)},
        "objetivos": objetivos,
        "indicadores": indicadores,
    }
