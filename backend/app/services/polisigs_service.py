"""Indicadores asociados a la Política POLISIGS.

- Catálogo y asociación a los 6 objetivos (columnas "Obj. N" con "Sí"):
  data/raw/POLISIGS/Indicadores Polisigs.xlsx, hoja "Indicadores POLISIGS"
- Meta / Ejecución / Cumplimiento: Resultados Consolidados (mismo tracking que el
  CMI), año y corte elegidos (por defecto junio 2026), último periodo reportado de cada indicador.

El consolidado de un objetivo (y de la política) es el promedio simple del
cumplimiento de los indicadores con dato, topado en 100 % por indicador, igual que `avg_cumplimiento` del CMI.
"""

from __future__ import annotations

import json
import logging
import math
import re
from pathlib import Path
from threading import Lock
from typing import Any

import pandas as pd

from app.domain.categorization import categorizar_cumplimiento
from app.domain.plan_mejoramiento_builders import load_plan_indicadores
from app.domain.procesos_builders import mes_nombre, mes_to_num
from app.domain.resumen_builders import ensure_nivel_cumplimiento
from app.domain.strategic_processors import StrategicProcessors
from app.services.excel_reader import ExcelReaderService
from app.services.tracking_cache import get_tracking_dataframe

ANIO = 2026
# Corte de la data: junio 2026 (cierres semestrales: junio y diciembre).
MES_CORTE = 6
CORTES = (6, 12)
# Solo aplica 2026 (la política V6 empieza a medirse ese año).
ANIOS = (2026,)
_TECHO = 100.0
_ARCHIVO = Path("raw") / "POLISIGS" / "Indicadores Polisigs.xlsx"
_HOJA = "Indicadores POLISIGS"
_PENDIENTE = "Pendiente de reporte"
_OBJETIVOS_JSON = Path(__file__).resolve().parent.parent / "data" / "polisigs_objetivos.json"

logger = logging.getLogger(__name__)
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
            _catalogo_cache["df"] = pd.read_excel(path, sheet_name=_HOJA)
            _catalogo_cache["mtime"] = mtime
        return _catalogo_cache["df"]


def _ultimo(excel: ExcelReaderService, anio: int, mes: int) -> dict[str, dict[str, Any]]:
    """Registro de cada Id en el mes de corte exacto; sin medición en ese corte = sin información."""
    tracking = get_tracking_dataframe(excel, historico=False)
    if tracking.empty or "Anio" not in tracking.columns:
        return {}
    df = tracking[pd.to_numeric(tracking["Anio"], errors="coerce") == anio].copy()
    if df.empty:
        return {}
    df = df[df["Mes"].map(mes_to_num).eq(mes)]
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


def _plan_mejoramiento(excel: ExcelReaderService, anio: int, mes: int) -> dict[str, dict[str, str]]:
    """Id de indicador -> Factor / Característica del Plan de mejoramiento (CNA)."""
    out: dict[str, dict[str, str]] = {}

    def _agregar(df: pd.DataFrame, col_id: str) -> None:
        if df.empty or not {col_id, "Factor", "Caracteristica"}.issubset(df.columns):
            return
        for r in df[[col_id, "Factor", "Caracteristica"]].dropna().to_dict("records"):
            out.setdefault(
                _id(r[col_id]),
                {
                    "factor": str(r["Factor"]).strip(),
                    "caracteristica": str(r["Caracteristica"]).strip(),
                },
            )

    try:
        _agregar(StrategicProcessors(excel).preparar_cna_con_cierre(anio, mes), "Id")
        _agregar(load_plan_indicadores(excel), "Id_Kawak")
    except Exception:  # noqa: BLE001 - el plan es información complementaria; no debe tumbar el tablero
        logger.warning("No se pudo cargar el Plan de mejoramiento para POLISIGS", exc_info=True)
    return out


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


def _parse_ods(texto: str | None) -> list[dict[str, Any]]:
    """'ODS 4 – Educación de calidad; ODS 8 – Trabajo…' -> [{numero, nombre}, ...]."""
    out: list[dict[str, Any]] = []
    for parte in (texto or "").split(";"):
        m = re.match(r"^\s*ODS\s*(\d+)\s*[–-]\s*(.+?)\s*$", parte)
        if m:
            out.append({"numero": int(m.group(1)), "nombre": m.group(2)})
    return out


def _objetivos_marcados(row: dict[str, Any]) -> list[int]:
    """Objetivos con 'Sí' en las columnas 'Obj. N ...' del Excel (un indicador puede tener varios)."""
    out: list[int] = []
    for col, val in row.items():
        m = re.match(r"^\s*Obj\.\s*(\d+)", str(col))
        if m and str(val).strip().lower() in {"sí", "si", "x", "1"}:
            out.append(int(m.group(1)))
    return sorted(out)


def get_polisigs(
    excel: ExcelReaderService, anio: int = ANIO, mes: int = MES_CORTE
) -> dict[str, Any]:
    cfg = _load_objetivos()
    catalogo = _load_catalogo(excel)
    datos = _ultimo(excel, anio, mes)
    plan = _plan_mejoramiento(excel, anio, mes)

    indicadores: list[dict[str, Any]] = []
    for r in catalogo.to_dict("records"):
        objetivos_ind = _objetivos_marcados(r)
        if not objetivos_ind:
            continue  # la base lista 350 indicadores; solo los asociados a algún objetivo
        ind_id = _id(r["ID"])
        d = datos.get(ind_id, {})
        real = _num(d.get("cumplimiento_pct"))
        # Techo de 100 % por indicador: el sobrecumplimiento no compensa otros
        # indicadores al promediar el objetivo.
        pct = None if real is None else min(real, _TECHO)
        indicadores.append(
            {
                "Id": ind_id,
                "Indicador": _txt(d.get("Indicador")) or _txt(r.get("Indicador")) or "",
                "objetivos": objetivos_ind,
                "proceso": _txt(d.get("Proceso")) or _txt(r.get("Proceso")),
                "responsable": _txt(r.get("Responsable")),
                "tipo": _txt(r.get("Tipo")),
                "frecuencia": _txt(d.get("Periodicidad")) or _txt(r.get("Frecuencia")),
                "sentido": _txt(d.get("Sentido")),
                "ods": _parse_ods(_txt(r.get("ODS relacionados (análisis ODS)"))),
                "relevancia_ods": _txt(r.get("Relevancia ODS")),
                "observaciones": _txt(r.get("Observaciones")),
                "plan_mejoramiento": plan.get(ind_id),
                # Mismos nombres de campo que el listado del CMI (fmtMeta/fmtEjecucion).
                "Meta": _num(d.get("Meta")),
                "Ejecucion": _num(d.get("Ejecucion")),
                "Meta_Signo": _txt(d.get("Meta_Signo")),
                "Decimales_Meta": _num(d.get("Decimales_Meta")),
                "periodo": _txt(d.get("Periodo")),
                "cumplimiento_pct": None if pct is None else round(pct, 1),
                "cumplimiento_real": None if real is None else round(real, 1),
                "Nivel de cumplimiento": d.get("Nivel de cumplimiento") or _PENDIENTE,
            }
        )

    objetivos: list[dict[str, Any]] = []
    for o in cfg["objetivos"]:
        # Un indicador puede repetirse en varios objetivos.
        items = [i for i in indicadores if o["numero"] in i["objetivos"]]
        comps: dict[str, list[dict[str, Any]]] = {}
        for i in items:
            comps.setdefault(i["proceso"] or "Sin proceso", []).append(i)
        objetivos.append(
            {
                "numero": o["numero"],
                "nombre": o["nombre"],
                "corto": o["corto"],
                **_consolidar(items),
                "procesos": [{"nombre": n, **_consolidar(v)} for n, v in comps.items()],
            }
        )

    return {
        "anio": anio,
        "mes": mes,
        "corte": f"{mes_nombre(mes)} {anio}",
        "filtros": {
            "anios": list(ANIOS),
            "cortes": [{"mes": m, "nombre": mes_nombre(m)} for m in CORTES],
            "corte_defecto": {"anio": ANIO, "mes": MES_CORTE},
        },
        "version_objetivos": cfg["version"],
        "politica": {"nombre": "Política POLISIGS V6", **_consolidar(indicadores)},
        "objetivos": objetivos,
        "indicadores": indicadores,
    }
