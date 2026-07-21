"""Detecta indicadores nuevos en las fuentes Kawak/API que aún no están en
el directorio maestro ('Catalogo Indicadores' de
data/raw/Catalogo de Indicadores.xlsx) y agrega filas skeleton con lo
inferible, dejando en blanco lo que requiere clasificación humana.

Pensado para correr DESPUÉS de scripts/consolidar_api.py (que regenera
Indicadores Kawak.xlsx y Consolidado_API_Kawak.xlsx) y ANTES de
scripts/actualizar_consolidado.py.

Uso: python scripts/sincronizar_directorio_indicadores.py
"""
from __future__ import annotations

import csv
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from etl.config import CATALOGO_MAESTRO_FILE, KAWAK_CAT_FILE, CONSOLIDADO_API_KW  # noqa: E402
from etl.normalizacion import _id_str, limpiar_html  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
logger = logging.getLogger(__name__)

REPORTES_DIR = ROOT / "data" / "output" / "reportes"


def _leer_ids_kawak() -> dict[str, dict]:
    """Ids + metadata inferible de Indicadores Kawak.xlsx (Año, Id, Indicador, ...)."""
    out: dict[str, dict] = {}
    if not KAWAK_CAT_FILE.exists():
        return out
    df = pd.read_excel(KAWAK_CAT_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    for _, row in df.iterrows():
        id_s = _id_str(row.get("Id", ""))
        if not id_s:
            continue
        out[id_s] = {
            "Indicador": limpiar_html(str(row.get("Indicador", "") or "")),
            "Clasificacion": str(row.get("Clasificacion", "") or ""),
            "Proceso": str(row.get("Proceso", "") or ""),
            "Periodicidad": str(row.get("Periodicidad", "") or ""),
            "Sentido": str(row.get("Sentido", "") or ""),
        }
    return out


def _leer_ids_api() -> dict[str, dict]:
    """Ids + metadata inferible de Consolidado_API_Kawak.xlsx (última fila por Id)."""
    out: dict[str, dict] = {}
    if not CONSOLIDADO_API_KW.exists():
        return out
    df = pd.read_excel(CONSOLIDADO_API_KW)
    df.columns = [str(c).strip() for c in df.columns]
    col_id = next((c for c in df.columns if c.upper() == "ID"), None)
    if not col_id:
        return out
    df["_id"] = df[col_id].map(lambda v: _id_str(v) if pd.notna(v) else None)
    df_last = df.dropna(subset=["_id"]).sort_values("fecha").groupby("_id").last()
    for id_s, row in df_last.iterrows():
        out[id_s] = {
            "Indicador": limpiar_html(str(row.get("nombre", "") or "")),
            "Clasificacion": str(row.get("clasificacion", "") or ""),
            "Proceso": str(row.get("proceso", "") or ""),
            "Periodicidad": "",
            "Sentido": str(row.get("sentido", "") or ""),
            "Tipo_API": str(row.get("Tipo", "") or ""),
            "Estado": str(row.get("estado", "") or ""),
        }
    return out


def main() -> None:
    if not CATALOGO_MAESTRO_FILE.exists():
        logger.error("No existe %s — nada que sincronizar.", CATALOGO_MAESTRO_FILE)
        return

    ids_kawak = _leer_ids_kawak()
    ids_api = _leer_ids_api()
    universo_fuente = {**ids_api, **ids_kawak}  # Kawak gana si hay choque

    df_cat = pd.read_excel(CATALOGO_MAESTRO_FILE, sheet_name="Catalogo Indicadores")
    ids_catalogo = {_id_str(v) for v in df_cat["Id"].dropna()}

    ids_nuevos = sorted(set(universo_fuente) - ids_catalogo)
    logger.info(
        "Universo fuente (Kawak+API): %d Ids | Directorio actual: %d Ids | Nuevos: %d",
        len(universo_fuente), len(ids_catalogo), len(ids_nuevos),
    )

    if not ids_nuevos:
        logger.info("Nada que agregar — el directorio ya cubre todos los Ids de Kawak/API.")
        return

    bak = CATALOGO_MAESTRO_FILE.with_name(CATALOGO_MAESTRO_FILE.stem + ".bak_pre_sync" + CATALOGO_MAESTRO_FILE.suffix)
    if not bak.exists():
        shutil.copy2(CATALOGO_MAESTRO_FILE, bak)
        logger.info("backup -> %s", bak.name)

    wb = openpyxl.load_workbook(CATALOGO_MAESTRO_FILE)
    ws = wb["Catalogo Indicadores"]
    header = {cell.value: cell.column for cell in ws[1]}

    filas_reporte = []
    for id_s in ids_nuevos:
        datos = universo_fuente.get(id_s, {})
        fila = [None] * len(header)
        campos = {
            "Id": id_s,
            "Indicador": datos.get("Indicador", ""),
            "Clasificacion": datos.get("Clasificacion", ""),
            "Proceso": datos.get("Proceso", ""),
            "Periodicidad": datos.get("Periodicidad", ""),
            "Sentido": datos.get("Sentido", ""),
            "Tipo_API": datos.get("Tipo_API", ""),
            "Estado": datos.get("Estado", ""),
            "Fuente": "API-nuevo (pendiente clasificar)",
        }
        for col_name, val in campos.items():
            if col_name in header:
                fila[header[col_name] - 1] = val
        ws.append(fila)
        filas_reporte.append({"Id": id_s, "Indicador": campos["Indicador"], "Proceso": campos["Proceso"]})

    wb.save(CATALOGO_MAESTRO_FILE)
    logger.info("Agregadas %d filas skeleton a 'Catalogo Indicadores'.", len(ids_nuevos))

    REPORTES_DIR.mkdir(parents=True, exist_ok=True)
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    reporte_path = REPORTES_DIR / f"indicadores_pendientes_clasificar_{fecha}.csv"
    with open(reporte_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["Id", "Indicador", "Proceso"])
        writer.writeheader()
        writer.writerows(filas_reporte)

    logger.error(
        "%d indicadores nuevos requieren clasificación manual "
        "(Subproceso/Linea_Estrategica/Objetivo_Estrategico/Ficha técnica) "
        "en 'Catalogo Indicadores'. Reporte: %s",
        len(ids_nuevos), reporte_path,
    )


if __name__ == "__main__":
    main()
