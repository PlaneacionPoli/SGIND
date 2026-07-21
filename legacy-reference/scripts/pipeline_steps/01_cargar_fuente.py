#!/usr/bin/env python3
"""
=============================================================
PASO 01 — CARGAR FUENTE CONSOLIDADA
=============================================================
QUÉ HACE:
  Lee Consolidado_API_Kawak.xlsx (generado por consolidar_api.py),
  normaliza columnas (strip, tipos) y reporta estadísticas básicas.
  Detecta columnas faltantes sin bloquear (eso lo hace el Paso 02).

ENTRADA:
  data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx

SALIDA:
  .pipeline_state/df_api.csv  (DataFrame normalizado)

DEPENDENCIAS:
  Ninguna. Es el primer paso.
  PRERREQUISITO: haber ejecutado scripts/consolidar_api.py

EJECUTAR:
  python scripts/pipeline_steps/01_cargar_fuente.py
  python scripts/pipeline_steps/01_cargar_fuente.py --dry-run
=============================================================
"""

import argparse
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

from _state import save_state, save_df  # noqa: E402
from etl.fuentes import cargar_fuente_consolidada  # noqa: E402
from etl.config import CONSOLIDADO_API_KW  # noqa: E402


COLUMNAS_ESPERADAS = ["Id", "fecha", "resultado", "meta", "variables", "series", "analisis"]


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
    parser = argparse.ArgumentParser(description="Paso 01 — Cargar Fuente Consolidada")
    parser.add_argument("--dry-run", action="store_true", help="Simular sin escribir estado")
    args = parser.parse_args()

    log("INFO", "Iniciando Paso 01 — Cargar Fuente Consolidada")
    t0 = time.time()

    if not CONSOLIDADO_API_KW.exists():
        msg = f"Archivo fuente no encontrado: {CONSOLIDADO_API_KW}"
        log("ERROR", msg)
        log("INFO", "Ejecuta primero: python scripts/consolidar_api.py")
        save_state("01", "Cargar Fuente", "error", {"error": msg})
        sys.exit(1)

    try:
        log("INFO", f"Leyendo {CONSOLIDADO_API_KW.name}...")
        df = cargar_fuente_consolidada()

        # Detectar columnas faltantes (sin bloquear)
        cols_lower = [c.lower() for c in df.columns]
        faltantes = [c for c in COLUMNAS_ESPERADAS if c.lower() not in cols_lower]

        # Estadísticas
        ids_unicos = df["Id"].nunique() if "Id" in df.columns else "?"
        fecha_col = None
        for fc in ["fecha", "Fecha", "FECHA"]:
            if fc in df.columns:
                fecha_col = fc
                break

        import pandas as pd
        fecha_min = fecha_max = "?"
        if fecha_col:
            fechas = pd.to_datetime(df[fecha_col], errors="coerce").dropna()
            if not fechas.empty:
                fecha_min = str(fechas.min().date())
                fecha_max = str(fechas.max().date())

        elapsed = round(time.time() - t0, 2)
        resultado = {
            "filas_cargadas": f"{len(df):,}",
            "columnas_encontradas": list(df.columns[:10]),
            "fechas_rango": f"{fecha_min} → {fecha_max}",
            "ids_unicos": ids_unicos,
            "columnas_faltantes": faltantes if faltantes else [],
        }

        log("OK", f"Paso 01 completado en {elapsed}s", resultado)

        if faltantes:
            log("WARN", f"Columnas no encontradas (el Paso 02 validará): {faltantes}")

        if not args.dry_run:
            save_df("df_api", df)
            log("INFO", f"Estado guardado: .pipeline_state/df_api.csv")
        else:
            log("INFO", "Modo --dry-run: no se guardó estado")

        save_state("01", "Cargar Fuente", "ok", resultado)
        sys.exit(0)

    except Exception as e:
        elapsed = round(time.time() - t0, 2)
        log("ERROR", f"Fallo en Paso 01: {e}")
        save_state("01", "Cargar Fuente", "error", {"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
