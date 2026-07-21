#!/usr/bin/env python3
"""
=============================================================
PASO 11 — DEDUPLICAR Y REESCRIBIR FÓRMULAS
=============================================================
QUÉ HACE:
  Para cada hoja (Histórico, Semestral, Cierres):
  1. Ordena por Id y Fecha (usando limpiar_ordenar_hoja).
  2. Elimina filas duplicadas (misma LLAVE), conservando la mejor.
  3. Reescribe todas las fórmulas con el número de fila correcto:
     Año, Mes, Semestre, LLAVE, Cumplimiento.

ENTRADA:
  data/output/Resultados Consolidados.xlsx

SALIDA:
  data/output/Resultados Consolidados.xlsx  (modificado)

DEPENDENCIAS:
  Paso 09_10 ejecutado (filas ya escritas).

EJECUTAR:
  python scripts/pipeline_steps/11_deduplicar_formulas.py
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

import openpyxl  # noqa: E402

from _state import save_state  # noqa: E402
from etl.config import OUTPUT_FILE  # noqa: E402
from etl.escritura import limpiar_ordenar_hoja  # noqa: E402


def log(nivel, mensaje, datos=None):
    ts = datetime.now().strftime("%H:%M:%S")
    iconos = {"INFO": "ℹ️ ", "OK": "✅", "ERROR": "❌", "WARN": "⚠️ ", "DATA": "📊"}
    icono = iconos.get(nivel, "•")
    print(f"[{ts}] {icono} {nivel:<5} | {mensaje}")
    if datos:
        for k, v in datos.items():
            print(f"           {'':5}   {k}: {v}")
    sys.stdout.flush()


def contar_filas_datos(ws):
    """Cuenta filas con datos (excluyendo cabecera)."""
    count = 0
    for row in ws.iter_rows(min_row=2):
        if any(c.value is not None for c in row):
            count += 1
    return count


def main():
    log("INFO", "Iniciando Paso 11 — Deduplicar y Reescribir Fórmulas")
    t0 = time.time()

    if not OUTPUT_FILE.exists():
        msg = f"Workbook no encontrado: {OUTPUT_FILE}"
        log("ERROR", msg)
        save_state("11", "Deduplicar + Fórmulas", "error", {"error": msg})
        sys.exit(1)

    try:
        log("INFO", f"Abriendo {OUTPUT_FILE.name}...")
        wb = openpyxl.load_workbook(OUTPUT_FILE)

        ws_hist    = wb["Consolidado Historico"]
        ws_sem     = wb["Consolidado Semestral"]
        ws_cierres = wb["Consolidado Cierres"]

        filas_antes = {
            "hist":    contar_filas_datos(ws_hist),
            "sem":     contar_filas_datos(ws_sem),
            "cierres": contar_filas_datos(ws_cierres),
        }

        log("INFO", "Ordenando y limpiando Histórico...")
        limpiar_ordenar_hoja(ws_hist, "Historico", ordenar_por=["Id", "Fecha"])

        log("INFO", "Ordenando y limpiando Semestral...")
        limpiar_ordenar_hoja(ws_sem, "Semestral", ordenar_por=["Id", "Fecha"])

        log("INFO", "Ordenando y limpiando Cierres...")
        limpiar_ordenar_hoja(ws_cierres, "Cierres", ordenar_por=["Id", "Fecha"])

        filas_despues = {
            "hist":    contar_filas_datos(ws_hist),
            "sem":     contar_filas_datos(ws_sem),
            "cierres": contar_filas_datos(ws_cierres),
        }

        log("INFO", f"Guardando {OUTPUT_FILE.name}...")
        wb.save(OUTPUT_FILE)
        if hasattr(wb, "close"):
            wb.close()

        elapsed = round(time.time() - t0, 2)
        resultado = {
            "filas_historico": filas_despues["hist"],
            "filas_semestral": filas_despues["sem"],
            "filas_cierres": filas_despues["cierres"],
            "duplicados_eliminados_hist": filas_antes["hist"] - filas_despues["hist"],
            "duplicados_eliminados_sem": filas_antes["sem"] - filas_despues["sem"],
            "duplicados_eliminados_cierres": filas_antes["cierres"] - filas_despues["cierres"],
        }

        log("OK", f"Paso 11 completado en {elapsed}s", resultado)
        save_state("11", "Deduplicar + Fórmulas", "ok", resultado)
        sys.exit(0)

    except Exception as e:
        log("ERROR", f"Fallo en Paso 11: {e}")
        import traceback
        traceback.print_exc()
        save_state("11", "Deduplicar + Fórmulas", "error", {"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
