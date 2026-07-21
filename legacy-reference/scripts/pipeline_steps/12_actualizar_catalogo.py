#!/usr/bin/env python3
"""
=============================================================
PASO 12 — ACTUALIZAR CATÁLOGO DE INDICADORES
=============================================================
QUÉ HACE:
  Regenera completamente la hoja "Catalogo Indicadores" del
  workbook a partir de los metadatos actuales. Primero borra
  el contenido existente y luego reescribe con construir_catalogo().

ENTRADA:
  .pipeline_state/df_api.csv  (del Paso 01)
  data/output/Resultados Consolidados.xlsx

SALIDA:
  data/output/Resultados Consolidados.xlsx  (hoja catálogo regenerada)

DEPENDENCIAS:
  Pasos 01 y 11 ejecutados.

EJECUTAR:
  python scripts/pipeline_steps/12_actualizar_catalogo.py
=============================================================
"""

import sys
import time
from datetime import datetime
from pathlib import Path

_STEPS_DIR = Path(__file__).parent
_SCRIPTS_DIR = _STEPS_DIR.parent
_ROOT = _SCRIPTS_DIR.parent
for _p in (str(_STEPS_DIR), str(_SCRIPTS_DIR), str(_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pandas as pd  # noqa: E402
import openpyxl  # noqa: E402

from _state import save_state, load_df  # noqa: E402
from etl.config import OUTPUT_FILE  # noqa: E402
from etl.catalogo import construir_catalogo  # noqa: E402
from etl.escritura import escribir_hoja_nueva  # noqa: E402
from etl.fuentes import cargar_metadatos_kawak, cargar_metadatos_cmi  # noqa: E402


def log(nivel, mensaje, datos=None):
    ts = datetime.now().strftime("%H:%M:%S")
    iconos = {"INFO": "ℹ️ ", "OK": "✅", "ERROR": "❌", "WARN": "⚠️ ", "DATA": "📊"}
    icono = iconos.get(nivel, "•")
    print(f"[{ts}] {icono} {nivel:<5} | {mensaje}")
    if datos:
        for k, v in datos.items():
            print(f"           {'':5}   {k}: {v}")
    sys.stdout.flush()


def main():
    log("INFO", "Iniciando Paso 12 — Actualizar Catálogo de Indicadores")
    t0 = time.time()

    if not OUTPUT_FILE.exists():
        msg = f"Workbook no encontrado: {OUTPUT_FILE}"
        log("ERROR", msg)
        save_state("12", "Actualizar Catálogo", "error", {"error": msg})
        sys.exit(1)

    try:
        log("INFO", "Cargando df_api del Paso 01...")
        df_api = load_df("df_api")
        df_api["fecha"] = pd.to_datetime(df_api["fecha"], errors="coerce")

        log("INFO", "Cargando histórico existente para construir catálogo...")
        df_hist_ex = pd.read_excel(OUTPUT_FILE, sheet_name="Consolidado Historico")

        log("INFO", "Cargando metadatos Kawak y CMI...")
        metadatos_kawak = cargar_metadatos_kawak()
        metadatos_cmi   = cargar_metadatos_cmi()

        log("INFO", "Construyendo catálogo...")
        df_catalogo = construir_catalogo(df_api, df_hist_ex, metadatos_kawak, metadatos_cmi)

        if df_catalogo.empty:
            log("WARN", "construir_catalogo() retornó DataFrame vacío — no se actualizará la hoja")
            save_state("12", "Actualizar Catálogo", "ok", {"indicadores_en_catalogo": 0})
            sys.exit(0)

        log("INFO", f"Catálogo con {len(df_catalogo)} indicadores y {len(df_catalogo.columns)} campos")

        log("INFO", f"Escribiendo hoja 'Catalogo Indicadores' en {OUTPUT_FILE.name}...")
        wb = openpyxl.load_workbook(OUTPUT_FILE)
        escribir_hoja_nueva(wb, "Catalogo Indicadores", df_catalogo)
        wb.save(OUTPUT_FILE)
        if hasattr(wb, "close"):
            wb.close()

        elapsed = round(time.time() - t0, 2)
        resultado = {
            "indicadores_en_catalogo": len(df_catalogo),
            "campos_escritos": len(df_catalogo.columns),
            "hoja_limpiada_y_regenerada": True,
        }

        log("OK", f"Paso 12 completado en {elapsed}s", resultado)
        save_state("12", "Actualizar Catálogo", "ok", resultado)
        sys.exit(0)

    except FileNotFoundError as e:
        log("ERROR", str(e))
        save_state("12", "Actualizar Catálogo", "error", {"error": str(e)})
        sys.exit(1)

    except Exception as e:
        log("ERROR", f"Fallo en Paso 12: {e}")
        import traceback
        traceback.print_exc()
        save_state("12", "Actualizar Catálogo", "error", {"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
