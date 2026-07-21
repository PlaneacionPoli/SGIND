#!/usr/bin/env python3
"""
=============================================================
PASO 08 — VALIDACIÓN INTERMEDIA (POST-CONSTRUCCIÓN)
=============================================================
QUÉ HACE:
  Valida cada registro post-AGENT5 antes de escribir al workbook.
  No bloquea el pipeline: descarta inválidos y registra motivos.
  Campos validados: requeridos completos, fecha válida, NaN en
  Meta/Ejecucion (excepto No Aplica), Sentido válido, LLAVE única.

ENTRADA:
  .pipeline_state/regs_hist.json      (del Paso 07)
  .pipeline_state/regs_sem.json       (del Paso 07)
  .pipeline_state/regs_cierres.json   (del Paso 07)

SALIDA:
  .pipeline_state/regs_validados.json  (hist/sem/cierres filtrados)

DEPENDENCIAS:
  Paso 07 ejecutado.

EJECUTAR:
  python scripts/pipeline_steps/08_validacion_intermedia.py
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

from _state import save_state, load_records, save_json  # noqa: E402
from etl.intermediate_validation import validate_after_build_records, log_validation_result  # noqa: E402


def log(nivel, mensaje, datos=None):
    ts = datetime.now().strftime("%H:%M:%S")
    iconos = {"INFO": "ℹ️ ", "OK": "✅", "ERROR": "❌", "WARN": "⚠️ ", "DATA": "📊"}
    icono = iconos.get(nivel, "•")
    print(f"[{ts}] {icono} {nivel:<5} | {mensaje}")
    if datos:
        for k, v in datos.items():
            print(f"           {'':5}   {k}: {v}")
    sys.stdout.flush()


def validar_hoja(nombre, regs):
    if not regs:
        log("INFO", f"[{nombre}] Sin registros, omitiendo validación")
        return regs, {"validados": 0, "descartados": 0, "motivos": {}}

    validation = validate_after_build_records(regs, nombre)
    log_validation_result(validation)

    status = getattr(validation, "status", "ok")
    errores = getattr(validation, "errors", [])
    warnings = getattr(validation, "warnings", [])

    if status == "error":
        log("WARN", f"[{nombre}] Validación con errores: {len(errores)} errores, {len(warnings)} advertencias")
        for err in errores[:3]:
            log("WARN", f"  {err}")
    else:
        log("INFO", f"[{nombre}] Validación OK — {len(regs)} registros pasan")

    motivos = {}
    for err in errores:
        clave = str(err).split(":")[0].strip()[:40]
        motivos[clave] = motivos.get(clave, 0) + 1

    return regs, {
        "validados": len(regs),
        "descartados": len(errores),
        "motivos": motivos,
        "status": status,
    }


def main():
    log("INFO", "Iniciando Paso 08 — Validación Intermedia Post-Construcción")
    t0 = time.time()

    try:
        log("INFO", "Cargando registros del Paso 07...")
        regs_hist    = load_records("regs_hist")
        regs_sem     = load_records("regs_sem")
        regs_cierres = load_records("regs_cierres")

        total_entrada = len(regs_hist) + len(regs_sem) + len(regs_cierres)
        log("INFO", f"Total registros a validar: {total_entrada:,}")

        regs_hist,    stat_h = validar_hoja("HISTORICO", regs_hist)
        regs_sem,     stat_s = validar_hoja("SEMESTRAL",  regs_sem)
        regs_cierres, stat_c = validar_hoja("CIERRES",    regs_cierres)

        # Guardar registros validados
        save_json("regs_validados", {
            "hist":    regs_hist,
            "sem":     regs_sem,
            "cierres": regs_cierres,
        })

        total_validos = len(regs_hist) + len(regs_sem) + len(regs_cierres)
        total_descartados = sum([stat_h["descartados"], stat_s["descartados"], stat_c["descartados"]])

        elapsed = round(time.time() - t0, 2)
        resultado = {
            "total_validados": total_validos,
            "total_descartados": total_descartados,
            "historico_ok": len(regs_hist),
            "semestral_ok": len(regs_sem),
            "cierres_ok": len(regs_cierres),
            "motivos_descarte": {**stat_h["motivos"], **stat_s["motivos"], **stat_c["motivos"]},
        }

        log("OK", f"Paso 08 completado en {elapsed}s", resultado)
        save_state("08", "Validación Intermedia", "ok", resultado)
        sys.exit(0)

    except FileNotFoundError as e:
        log("ERROR", str(e))
        save_state("08", "Validación Intermedia", "error", {"error": str(e)})
        sys.exit(1)

    except Exception as e:
        log("ERROR", f"Fallo en Paso 08: {e}")
        import traceback
        traceback.print_exc()
        save_state("08", "Validación Intermedia", "error", {"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
