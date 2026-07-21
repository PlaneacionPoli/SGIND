#!/usr/bin/env python3
"""
=============================================================
PASOS 14+15 — AUDITORÍA JSON + RESPALDO VERSIONADO (AGRUPADOS)
=============================================================
QUÉ HACE:
  PASO 14 — Auditoría: Lee .pipeline_state/current_run.json con
  los resultados de todos los pasos y consolida en un JSON de
  auditoría completo. Guarda en artifacts/audit/[timestamp].json.

  PASO 15 — Respaldo: Copia el archivo principal a .versions/
  con nombre versionado (o usa VersionManager si ya existe versión).

ENTRADA:
  .pipeline_state/current_run.json
  .pipeline_state/alertas_agent5.json
  data/output/Resultados Consolidados.xlsx

SALIDA:
  artifacts/audit/[YYYYMMDD_HHMMSS].json
  data/output/.versiones/Resultados_Consolidados_v[timestamp]_post_consolidacion.xlsx

DEPENDENCIAS:
  Paso 13 ejecutado.

EJECUTAR:
  python scripts/pipeline_steps/14_15_auditoria_respaldo.py
=============================================================
"""

import shutil
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

import json  # noqa: E402

from _state import save_state, load_state, load_json  # noqa: E402
from etl.config import OUTPUT_FILE, OUTPUT_DIR  # noqa: E402
from etl.versioning import VersionManager  # noqa: E402


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
    log("INFO", "Iniciando Pasos 14+15 — Auditoría + Respaldo")
    t0 = time.time()

    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        # ── PASO 14: Auditoría ───────────────────────────────────────
        log("INFO", "[PASO 14] Consolidando auditoría del run...")

        state = load_state()
        alertas_agent5 = {}
        try:
            alertas_agent5 = load_json("alertas_agent5")
        except FileNotFoundError:
            log("WARN", "alertas_agent5.json no encontrado (Paso 07 no ejecutado?)")

        # Extraer totales de los pasos
        def get_resultado(step_key, field, default=0):
            s = state.get(f"step_{step_key}", {})
            return s.get("resultado", {}).get(field, default)

        pasos_ok  = [k.replace("step_", "") for k, v in state.items() if k.startswith("step_") and v.get("status") == "ok"]
        pasos_err = [k.replace("step_", "") for k, v in state.items() if k.startswith("step_") and v.get("status") == "error"]

        audit = {
            "run_id": run_ts,
            "inicio": state.get("_last_updated", datetime.now().isoformat()),
            "fin": datetime.now().isoformat(),
            "pasos_ejecutados": pasos_ok,
            "pasos_con_error": pasos_err,
            "totales": {
                "filas_fuente": get_resultado("01", "filas_cargadas", "?"),
                "registros_nuevos_hist": get_resultado("09_10", "paso_09_hist_insertados", 0),
                "registros_nuevos_sem": get_resultado("09_10", "paso_09_sem_insertados", 0),
                "registros_nuevos_cierres": get_resultado("09_10", "paso_09_cierres_insertados", 0),
                "duplicados_bloqueados": get_resultado("09_10", "paso_09_duplicados_bloqueados", 0),
                "indicadores_en_catalogo": get_resultado("12", "indicadores_en_catalogo", 0),
                "total_filas_historico": get_resultado("13", "total_filas_historico", "?"),
            },
            "alertas_agent5": {
                "ejecuciones_recortadas": alertas_agent5.get("ejecuciones_recortadas", 0),
                "metas_en_cero": alertas_agent5.get("metas_en_cero", 0),
                "ids_con_alerta": alertas_agent5.get("ids_con_alerta", [])[:20],
            },
            "estado_pasos": {
                k: {"status": v.get("status"), "timestamp": v.get("timestamp")}
                for k, v in state.items()
                if k.startswith("step_")
            },
            "errores": [
                {"paso": k.replace("step_", ""), "error": v.get("resultado", {}).get("error", "")}
                for k, v in state.items()
                if k.startswith("step_") and v.get("status") == "error"
            ],
        }

        # Guardar JSON de auditoría
        audit_dir = _ROOT / "artifacts" / "audit"
        audit_dir.mkdir(parents=True, exist_ok=True)
        audit_file = audit_dir / f"{run_ts}.json"
        audit_file.write_text(
            json.dumps(audit, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        log("DATA", "[PASO 14]", {"audit_guardado": str(audit_file.relative_to(_ROOT))})

        # ── PASO 15: Respaldo ────────────────────────────────────────
        log("INFO", "[PASO 15] Creando respaldo versionado...")

        respaldo_path = None
        if OUTPUT_FILE.exists():
            vm = VersionManager(OUTPUT_FILE, max_versions=10)
            try:
                respaldo_path = vm.crear_version(tag="post_consolidacion")
                if respaldo_path:
                    log("DATA", "[PASO 15]", {"respaldo_creado": str(respaldo_path)})
            except Exception as e:
                log("WARN", f"VersionManager falló, usando copia manual: {e}")
                versiones_dir = OUTPUT_DIR / ".versiones"
                versiones_dir.mkdir(exist_ok=True)
                respaldo_manual = versiones_dir / f"Resultados_Consolidados_v{run_ts}_post_consolidacion.xlsx"
                shutil.copy2(OUTPUT_FILE, respaldo_manual)
                respaldo_path = respaldo_manual
                log("DATA", "[PASO 15]", {"respaldo_creado": str(respaldo_manual.relative_to(_ROOT))})
        else:
            log("WARN", f"Archivo principal no encontrado para respaldo: {OUTPUT_FILE}")

        elapsed = round(time.time() - t0, 2)
        resultado = {
            "audit_guardado": str(audit_file.relative_to(_ROOT)),
            "pasos_ok": len(pasos_ok),
            "pasos_con_error": len(pasos_err),
            "respaldo_creado": str(respaldo_path.relative_to(_ROOT)) if respaldo_path else "no creado",
        }

        log("OK", f"Pasos 14+15 completados en {elapsed}s", resultado)
        save_state("14_15", "Auditoría + Respaldo", "ok", resultado)
        sys.exit(0)

    except Exception as e:
        log("ERROR", f"Fallo en Pasos 14+15: {e}")
        import traceback
        traceback.print_exc()
        save_state("14_15", "Auditoría + Respaldo", "error", {"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
