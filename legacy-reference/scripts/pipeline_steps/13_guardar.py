#!/usr/bin/env python3
"""
=============================================================
PASO 13 — GUARDAR ARCHIVOS DE SALIDA
=============================================================
QUÉ HACE:
  1. Crea backup del archivo previo → Resultados Consolidados.bak.xlsx
  2. El archivo principal ya fue guardado en pasos anteriores.
  3. Genera copia con fórmulas materializadas (solo valores):
     Resultados Consolidados VALORES.xlsx
  Reporta tamaños de archivo y totales de filas.

ENTRADA:
  data/output/Resultados Consolidados.xlsx

SALIDA:
  data/output/Resultados Consolidados.bak.xlsx
  data/output/Resultados Consolidados VALORES.xlsx

DEPENDENCIAS:
  Pasos 09_10, 11, 12 ejecutados.

EJECUTAR:
  python scripts/pipeline_steps/13_guardar.py
  python scripts/pipeline_steps/13_guardar.py --dry-run
=============================================================
"""

import argparse
import shutil
import sys
import tempfile
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
import pandas as pd  # noqa: E402

from _state import save_state  # noqa: E402
from etl.config import OUTPUT_FILE  # noqa: E402
from etl.formulas_excel import _materializar_cumplimiento  # noqa: E402


def log(nivel, mensaje, datos=None):
    ts = datetime.now().strftime("%H:%M:%S")
    iconos = {"INFO": "ℹ️ ", "OK": "✅", "ERROR": "❌", "WARN": "⚠️ ", "DATA": "📊"}
    icono = iconos.get(nivel, "•")
    print(f"[{ts}] {icono} {nivel:<5} | {mensaje}")
    if datos:
        for k, v in datos.items():
            print(f"           {'':5}   {k}: {v}")
    sys.stdout.flush()


def mb(path):
    try:
        return f"{path.stat().st_size / 1_048_576:.1f} MB"
    except Exception:
        return "?"


def contar_filas(path, sheet):
    try:
        df = pd.read_excel(path, sheet_name=sheet, usecols=[0])
        return max(0, len(df))
    except Exception:
        return "?"


def main():
    parser = argparse.ArgumentParser(description="Paso 13 — Guardar Archivos de Salida")
    parser.add_argument("--dry-run", action="store_true", help="Simular sin escribir archivos")
    args = parser.parse_args()

    log("INFO", "Iniciando Paso 13 — Guardar Archivos de Salida")
    t0 = time.time()

    if not OUTPUT_FILE.exists():
        msg = f"Archivo principal no encontrado: {OUTPUT_FILE}"
        log("ERROR", msg)
        save_state("13", "Guardar", "error", {"error": msg})
        sys.exit(1)

    try:
        backup_file  = OUTPUT_FILE.with_suffix(".bak.xlsx")
        valores_file = OUTPUT_FILE.with_name(OUTPUT_FILE.stem + " VALORES.xlsx")

        # ── Backup ───────────────────────────────────────────────────
        log("INFO", f"Creando backup: {backup_file.name}...")
        if not args.dry_run:
            shutil.copy2(OUTPUT_FILE, backup_file)
            log("INFO", f"Backup creado: {mb(backup_file)}")
        else:
            log("INFO", "Modo --dry-run: backup NO creado")

        # ── Generar VALORES ──────────────────────────────────────────
        log("INFO", f"Generando copia solo-valores: {valores_file.name}...")
        if not args.dry_run:
            with tempfile.TemporaryDirectory(prefix="sip_valores_", ignore_cleanup_errors=True) as td:
                tmp = Path(td) / OUTPUT_FILE.name
                shutil.copy2(OUTPUT_FILE, tmp)
                wb_val = openpyxl.load_workbook(tmp)
                for ws in wb_val.worksheets:
                    try:
                        _materializar_cumplimiento(ws)
                    except Exception as e:
                        log("WARN", f"No se pudo materializar hoja {ws.title}: {e}")
                tmp_val = Path(td) / valores_file.name
                wb_val.save(tmp_val)
                if hasattr(wb_val, "close"):
                    wb_val.close()
                shutil.copy2(tmp_val, valores_file)
            log("INFO", f"VALORES creado: {mb(valores_file)}")
        else:
            log("INFO", "Modo --dry-run: VALORES NO generado")

        # ── Estadísticas ─────────────────────────────────────────────
        n_hist    = contar_filas(OUTPUT_FILE, "Consolidado Historico")
        n_sem     = contar_filas(OUTPUT_FILE, "Consolidado Semestral")
        n_cierres = contar_filas(OUTPUT_FILE, "Consolidado Cierres")

        elapsed = round(time.time() - t0, 2)
        resultado = {
            "archivo_principal": f"{OUTPUT_FILE.name} ({mb(OUTPUT_FILE)})",
            "archivo_valores": f"{valores_file.name} ({mb(valores_file) if valores_file.exists() else 'pendiente'})",
            "backup": f"{backup_file.name}" if backup_file.exists() else "no creado",
            "total_filas_historico": n_hist,
            "total_filas_semestral": n_sem,
            "total_filas_cierres": n_cierres,
            "dry_run": args.dry_run,
        }

        log("OK", f"Paso 13 completado en {elapsed}s", resultado)
        save_state("13", "Guardar", "ok", resultado)
        sys.exit(0)

    except Exception as e:
        log("ERROR", f"Fallo en Paso 13: {e}")
        import traceback
        traceback.print_exc()
        save_state("13", "Guardar", "error", {"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
