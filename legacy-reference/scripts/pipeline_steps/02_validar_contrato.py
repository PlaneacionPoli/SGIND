#!/usr/bin/env python3
"""
=============================================================
PASO 02 — VALIDAR CONTRATO DE DATOS (LAYER 1)
=============================================================
QUÉ HACE:
  Valida que el DataFrame cargado en el Paso 01 cumpla el contrato
  definido en config/data_contracts.yaml. Verifica columnas requeridas
  y tipos. Bloquea el pipeline si hay errores críticos.

ENTRADA:
  .pipeline_state/df_api.csv  (del Paso 01)
  config/data_contracts.yaml

SALIDA:
  Estado en current_run.json. No produce archivo nuevo.

DEPENDENCIAS:
  Paso 01 ejecutado.

EJECUTAR:
  python scripts/pipeline_steps/02_validar_contrato.py
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

from _state import save_state, load_df  # noqa: E402
from etl.validation_gate import validar_consolidado_api_entrada  # noqa: E402


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
    parser = argparse.ArgumentParser(description="Paso 02 — Validar Contrato")
    parser.parse_args()

    log("INFO", "Iniciando Paso 02 — Validar Contrato de Datos (LAYER 1)")
    t0 = time.time()

    try:
        log("INFO", "Cargando df_api desde estado...")
        import pandas as pd
        df = load_df("df_api")
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

        log("INFO", "Ejecutando validación LAYER 1...")
        validacion = validar_consolidado_api_entrada(df, verbose=True)

        elapsed = round(time.time() - t0, 2)

        filas_fecha_invalida = int(df["fecha"].isna().sum()) if "fecha" in df.columns else "?"

        resultado = {
            "status_validacion": validacion.status,
            "errores_criticos": len(getattr(validacion, "errors", [])),
            "advertencias": len(getattr(validacion, "warnings", [])),
            "filas_con_fecha_invalida": filas_fecha_invalida,
        }

        if hasattr(validacion, "details") and validacion.details:
            resultado["detalles"] = str(validacion.details)[:200]

        if validacion.status == "error":
            log("ERROR", f"Fallo en Paso 02: ValidationError — Pipeline bloqueado")
            errores = getattr(validacion, "errors", [])
            for err in errores[:5]:
                log("ERROR", f"  {err}")
            log("INFO", "Acción requerida: Re-ejecutar consolidar_api.py y verificar archivo fuente")
            save_state("02", "Validar Contrato", "error", resultado)
            sys.exit(1)

        log("OK", f"Paso 02 completado en {elapsed}s", resultado)
        save_state("02", "Validar Contrato", "ok", resultado)
        sys.exit(0)

    except FileNotFoundError as e:
        log("ERROR", str(e))
        save_state("02", "Validar Contrato", "error", {"error": str(e)})
        sys.exit(1)

    except Exception as e:
        log("ERROR", f"Fallo en Paso 02: {e}")
        save_state("02", "Validar Contrato", "error", {"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
