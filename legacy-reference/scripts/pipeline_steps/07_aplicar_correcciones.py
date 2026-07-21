#!/usr/bin/env python3
"""
=============================================================
PASO 07 — AGENT5: APLICAR CORRECCIONES CRÍTICAS
=============================================================
QUÉ HACE:
  Itera sobre los registros construidos en el Paso 06 y aplica
  las correcciones críticas del AGENT 5:
  1. Si Ejecucion > 1.3 → recortar a 1.3 (capping automático)
  2. Si Meta == 0 → marcar como requiere_revision=True
  Guarda lista de alertas en .pipeline_state/alertas_agent5.json.

ENTRADA:
  .pipeline_state/regs_hist.json     (del Paso 06)
  .pipeline_state/regs_sem.json      (del Paso 06)
  .pipeline_state/regs_cierres.json  (del Paso 06)

SALIDA:
  .pipeline_state/regs_hist.json     (sobreescribe con correcciones)
  .pipeline_state/regs_sem.json      (sobreescribe con correcciones)
  .pipeline_state/regs_cierres.json  (sobreescribe con correcciones)
  .pipeline_state/alertas_agent5.json

DEPENDENCIAS:
  Paso 06 ejecutado.

EJECUTAR:
  python scripts/pipeline_steps/07_aplicar_correcciones.py
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

from _state import save_state, load_records, save_records, save_json  # noqa: E402
from etl.agent5_corrections import AGENT5Corrections  # noqa: E402


def log(nivel, mensaje, datos=None):
    ts = datetime.now().strftime("%H:%M:%S")
    iconos = {"INFO": "ℹ️ ", "OK": "✅", "ERROR": "❌", "WARN": "⚠️ ", "DATA": "📊"}
    icono = iconos.get(nivel, "•")
    print(f"[{ts}] {icono} {nivel:<5} | {mensaje}")
    if datos:
        for k, v in datos.items():
            print(f"           {'':5}   {k}: {v}")
    sys.stdout.flush()


def aplicar_correcciones_a(nombre, regs):
    if not regs:
        log("INFO", f"[{nombre}] Sin registros, omitiendo")
        return regs, {}

    df = pd.DataFrame(regs)
    df_corregido, reporte = AGENT5Corrections.apply_all_corrections(df)

    n_capping = reporte.get("ejecucion_capping", 0)
    n_meta0   = reporte.get("meta_zero_count", 0)

    if n_capping > 0:
        log("WARN", f"[{nombre}] {n_capping} registros con ejecución > 1.3 → capeados a 1.3")
    if n_meta0 > 0:
        log("WARN", f"[{nombre}] {n_meta0} registros con Meta=0 detectados (revisar manualmente)")

    return df_corregido.to_dict(orient="records"), reporte


def main():
    log("INFO", "Iniciando Paso 07 — AGENT5: Correcciones Críticas")
    t0 = time.time()

    try:
        log("INFO", "Cargando registros del Paso 06...")
        regs_hist    = load_records("regs_hist")
        regs_sem     = load_records("regs_sem")
        regs_cierres = load_records("regs_cierres")

        log("INFO", f"Registros a procesar: hist={len(regs_hist)}, sem={len(regs_sem)}, cierres={len(regs_cierres)}")

        regs_hist,    rep_h = aplicar_correcciones_a("HISTORICO", regs_hist)
        regs_sem,     rep_s = aplicar_correcciones_a("SEMESTRAL", regs_sem)
        regs_cierres, rep_c = aplicar_correcciones_a("CIERRES",   regs_cierres)

        # Guardar registros corregidos (sobreescribe)
        save_records("regs_hist",    regs_hist)
        save_records("regs_sem",     regs_sem)
        save_records("regs_cierres", regs_cierres)

        # Recopilar IDs con alertas
        ids_con_alerta = []
        for regs in [regs_hist, regs_sem, regs_cierres]:
            for r in regs:
                if r.get("requiere_revision") or r.get("_capped"):
                    ids_con_alerta.append(str(r.get("Id", "")))

        alertas = {
            "ejecuciones_recortadas": rep_h.get("ejecucion_capping", 0) + rep_s.get("ejecucion_capping", 0) + rep_c.get("ejecucion_capping", 0),
            "metas_en_cero": rep_h.get("meta_zero_count", 0) + rep_s.get("meta_zero_count", 0) + rep_c.get("meta_zero_count", 0),
            "por_hoja": {
                "historico": rep_h,
                "semestral": rep_s,
                "cierres":   rep_c,
            },
            "ids_con_alerta": list(set(ids_con_alerta))[:30],
        }
        save_json("alertas_agent5", alertas)

        elapsed = round(time.time() - t0, 2)
        resultado = {
            "ejecuciones_recortadas": alertas["ejecuciones_recortadas"],
            "metas_en_cero": alertas["metas_en_cero"],
            "alertas_generadas": alertas["ejecuciones_recortadas"] + alertas["metas_en_cero"],
            "ids_con_alerta": alertas["ids_con_alerta"][:10],
        }

        log("OK", f"Paso 07 completado en {elapsed}s", resultado)
        save_state("07", "AGENT5 Correcciones", "ok", resultado)
        sys.exit(0)

    except FileNotFoundError as e:
        log("ERROR", str(e))
        save_state("07", "AGENT5 Correcciones", "error", {"error": str(e)})
        sys.exit(1)

    except Exception as e:
        log("ERROR", f"Fallo en Paso 07: {e}")
        import traceback
        traceback.print_exc()
        save_state("07", "AGENT5 Correcciones", "error", {"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
