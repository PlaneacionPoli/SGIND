#!/usr/bin/env python3
"""
=============================================================
PASOS 09+10 — ESCRIBIR FILAS + REPARAR VALORES (AGRUPADOS)
=============================================================
QUÉ HACE:
  PASO 09 — Escritura: Inserta los registros válidos (del Paso 08)
  en las hojas Consolidado Histórico, Semestral y Cierres del
  workbook. Solo inserta LLAVEs que no existan aún (verificación
  final antes de escribir).

  PASO 10 — Reparación: Para filas con Meta==NULL intenta
  completarla desde el catálogo. Para indicadores multi-serie
  recalcula la agregación. Para semestrales recalcula agregados.

ENTRADA:
  .pipeline_state/regs_validados.json  (del Paso 08)
  .pipeline_state/workbook_meta.json   (del Paso 05)
  data/output/Resultados Consolidados.xlsx

SALIDA:
  data/output/Resultados Consolidados.xlsx  (modificado)

DEPENDENCIAS:
  Pasos 05, 08 ejecutados. Workbook debe existir.

EJECUTAR:
  python scripts/pipeline_steps/09_10_escribir_reparar.py
  python scripts/pipeline_steps/09_10_escribir_reparar.py --dry-run
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

import pandas as pd  # noqa: E402
import openpyxl  # noqa: E402

from _state import save_state, load_json  # noqa: E402
from etl.config import OUTPUT_FILE, INPUT_FILE  # noqa: E402
from etl.escritura import escribir_filas, llaves_de_df  # noqa: E402
from etl.purga import (  # noqa: E402
    reparar_meta_vacia, reparar_multiserie, reparar_semestral_agregados,
    reparar_desglose_variables, reparar_metas_fijas,
)
from etl.catalogo import cargar_catalogo_completo  # noqa: E402
from etl.fuentes import cargar_consolidado_api_kawak_lookup, cargar_lmi_reporte  # noqa: E402


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
    parser = argparse.ArgumentParser(description="Pasos 09+10 — Escribir + Reparar")
    parser.add_argument("--dry-run", action="store_true", help="Simular sin modificar el workbook")
    args = parser.parse_args()

    log("INFO", "Iniciando Pasos 09+10 — Escribir Filas + Reparar Valores")
    t0 = time.time()

    # Determinar archivo de trabajo
    wb_path = OUTPUT_FILE if OUTPUT_FILE.exists() else INPUT_FILE
    if not wb_path.exists():
        msg = f"Workbook no encontrado: {wb_path}"
        log("ERROR", msg)
        save_state("09_10", "Escribir + Reparar", "error", {"error": msg})
        sys.exit(1)

    try:
        # ── Cargar estado previo ─────────────────────────────────────
        log("INFO", "Cargando registros validados del Paso 08...")
        validados = load_json("regs_validados")
        regs_hist    = validados.get("hist", [])
        regs_sem     = validados.get("sem", [])
        regs_cierres = validados.get("cierres", [])

        log("INFO", "Cargando signos del Paso 05...")
        meta = load_json("workbook_meta")
        signos_raw = meta.get("signos", {})
        signos = {}
        for k, v in signos_raw.items():
            signos[k] = {sk: None if sv in ("None", "nan", "") else sv for sk, sv in v.items()}

        log("INFO", "Cargando catálogo y lookup...")
        cat_data            = cargar_catalogo_completo()
        extraccion_map      = cat_data["extraccion_map"]
        tipo_calculo_map    = cat_data["tipo_calculo_map"]
        variables_campo_map = cat_data["variables_campo_map"]
        tipo_indicador_map  = cat_data["tipo_indicador_map"]
        api_kawak_lookup = cargar_consolidado_api_kawak_lookup(extraccion_map)
        ids_metrica      = cargar_lmi_reporte()

        # ── Abrir workbook ───────────────────────────────────────────
        log("INFO", f"Abriendo {wb_path.name}...")
        wb = openpyxl.load_workbook(wb_path)
        ws_hist    = wb["Consolidado Historico"]
        ws_sem     = wb["Consolidado Semestral"]
        ws_cierres = wb["Consolidado Cierres"]

        # ── PASO 09: Escribir filas ──────────────────────────────────
        log("INFO", "[PASO 09] Escribiendo filas nuevas...")

        duplicados_bloqueados = 0
        llaves_act_h = llaves_de_df(pd.read_excel(wb_path, sheet_name="Consolidado Historico"))
        llaves_act_s = llaves_de_df(pd.read_excel(wb_path, sheet_name="Consolidado Semestral"))

        regs_hist_ok    = [r for r in regs_hist    if str(r.get("LLAVE", "")) not in llaves_act_h]
        regs_sem_ok     = [r for r in regs_sem     if str(r.get("LLAVE", "")) not in llaves_act_s]
        regs_cierres_ok = regs_cierres  # cierres se limpian antes

        duplicados_bloqueados = (len(regs_hist) - len(regs_hist_ok)) + (len(regs_sem) - len(regs_sem_ok))

        if not args.dry_run:
            if regs_hist_ok:
                escribir_filas(ws_hist, regs_hist_ok, signos, ids_metrica=ids_metrica)
            if regs_sem_ok:
                escribir_filas(ws_sem, regs_sem_ok, signos, ids_metrica=ids_metrica)
            if regs_cierres_ok:
                escribir_filas(ws_cierres, regs_cierres_ok, signos, ids_metrica=ids_metrica)
        else:
            log("INFO", "Modo --dry-run: filas NO escritas")

        log("DATA", "[PASO 09]", {
            "filas_insertadas_historico": len(regs_hist_ok),
            "filas_insertadas_semestral": len(regs_sem_ok),
            "filas_insertadas_cierres": len(regs_cierres_ok),
            "duplicados_bloqueados_en_escritura": duplicados_bloqueados,
        })

        # ── PASO 10: Reparar valores ─────────────────────────────────
        log("INFO", "[PASO 10] Reparando metas vacías y multi-series...")

        if not args.dry_run:
            for ws, nom in [(ws_hist, "Historico"), (ws_sem, "Semestral"), (ws_cierres, "Cierres")]:
                reparar_meta_vacia(ws, api_kawak_lookup, nom)
                reparar_multiserie(
                    ws, api_kawak_lookup, tipo_calculo_map, nom,
                    extraccion_map, tipo_indicador_map,
                )

            df_api_state = None
            try:
                from _state import load_df
                df_api_state = load_df("df_api")
                df_api_state["fecha"] = pd.to_datetime(df_api_state["fecha"], errors="coerce")
            except Exception as e:
                log("WARN", f"No se pudo cargar df_api para reparaciones de agregados: {e}")

            if tipo_calculo_map and df_api_state is not None:
                try:
                    reparar_semestral_agregados(
                        ws_sem, df_api_state, extraccion_map, tipo_calculo_map, "Semestral",
                        variables_campo_map, tipo_indicador_map,
                    )
                    reparar_semestral_agregados(
                        ws_cierres, df_api_state, extraccion_map, tipo_calculo_map, "Cierres",
                        variables_campo_map, tipo_indicador_map,
                    )
                except Exception as e:
                    log("WARN", f"No se pudo reparar agregados semestrales: {e}")

            if df_api_state is not None:
                try:
                    reparar_desglose_variables(
                        ws_hist, df_api_state, extraccion_map, variables_campo_map,
                        tipo_indicador_map, "Historico",
                    )
                    reparar_desglose_variables(
                        ws_sem, df_api_state, extraccion_map, variables_campo_map,
                        tipo_indicador_map, "Semestral", tipo_calculo_map=tipo_calculo_map,
                    )
                    reparar_desglose_variables(
                        ws_cierres, df_api_state, extraccion_map, variables_campo_map,
                        tipo_indicador_map, "Cierres", tipo_calculo_map=tipo_calculo_map,
                    )
                except Exception as e:
                    log("WARN", f"No se pudo reparar Desglose Variables: {e}")

            for ws, nom in [(ws_hist, "Historico"), (ws_sem, "Semestral"), (ws_cierres, "Cierres")]:
                reparar_metas_fijas(ws, nom)
        else:
            log("INFO", "Modo --dry-run: reparaciones NO aplicadas")

        # ── Guardar workbook ─────────────────────────────────────────
        if not args.dry_run:
            log("INFO", f"Guardando {wb_path.name}...")
            wb.save(wb_path)
            log("INFO", "Workbook guardado.")
        if hasattr(wb, "close"):
            wb.close()

        elapsed = round(time.time() - t0, 2)
        resultado = {
            "paso_09_hist_insertados": len(regs_hist_ok),
            "paso_09_sem_insertados": len(regs_sem_ok),
            "paso_09_cierres_insertados": len(regs_cierres_ok),
            "paso_09_duplicados_bloqueados": duplicados_bloqueados,
            "dry_run": args.dry_run,
        }

        log("OK", f"Pasos 09+10 completados en {elapsed}s", resultado)
        save_state("09_10", "Escribir + Reparar", "ok", resultado)
        sys.exit(0)

    except FileNotFoundError as e:
        log("ERROR", str(e))
        save_state("09_10", "Escribir + Reparar", "error", {"error": str(e)})
        sys.exit(1)

    except Exception as e:
        log("ERROR", f"Fallo en Pasos 09+10: {e}")
        import traceback
        traceback.print_exc()
        save_state("09_10", "Escribir + Reparar", "error", {"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
