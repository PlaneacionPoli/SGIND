#!/usr/bin/env python3
"""
=============================================================
PASO 06 — CONSTRUIR REGISTROS NUEVOS
=============================================================
QUÉ HACE:
  Ejecuta las tres funciones de construcción de registros:
  1. construir_registros_historico() — aplica regla de último
     día del mes, extracción en 5 niveles, descarta LLAVEs
     ya existentes.
  2. construir_registros_semestral() — rama Cierre (meses 6,12)
     y rama Agregado (Promedio/Acumulado).
  3. construir_registros_cierres() — mes=12, día=31, por año.

ENTRADA:
  .pipeline_state/df_api.csv           (del Paso 01)
  .pipeline_state/workbook_meta.json   (del Paso 05)

SALIDA:
  .pipeline_state/regs_hist.json
  .pipeline_state/regs_sem.json
  .pipeline_state/regs_cierres.json

DEPENDENCIAS:
  Pasos 01 y 05 ejecutados.

EJECUTAR:
  python scripts/pipeline_steps/06_construir_registros.py
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

from _state import save_state, load_df, load_json, save_records  # noqa: E402
from etl.catalogo import cargar_catalogo_completo, cargar_config_patrones  # noqa: E402
from etl.fuentes import (  # noqa: E402
    cargar_kawak_validos,
    cargar_consolidado_api_kawak_lookup,
    cargar_mapa_procesos,
)
from etl.builders import (  # noqa: E402
    construir_registros_historico,
    construir_registros_semestral,
    construir_registros_cierres,
)
from etl.normalizacion import _id_str  # noqa: E402


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
    log("INFO", "Iniciando Paso 06 — Construir Registros Nuevos")
    t0 = time.time()

    try:
        # ── Cargar estado previo ─────────────────────────────────────
        log("INFO", "Cargando df_api desde estado Paso 01...")
        df_api = load_df("df_api")
        df_api["fecha"] = pd.to_datetime(df_api["fecha"], errors="coerce")
        df_api = df_api.dropna(subset=["fecha"]).copy()

        log("INFO", "Cargando metadatos del workbook desde Paso 05...")
        meta = load_json("workbook_meta")
        llaves_hist = set(meta.get("llaves_hist", []))
        llaves_sem  = set(meta.get("llaves_sem", []))
        hist_escalas_raw = meta.get("hist_escalas", {})
        hist_escalas = {}
        for k, v in hist_escalas_raw.items():
            hist_escalas[k] = {
                "Meta": None if v.get("Meta") in (None, "None", "nan") else float(v["Meta"]),
                "Ejecucion": None if v.get("Ejecucion") in (None, "None", "nan") else float(v["Ejecucion"]),
            }

        # ── Cargar catálogo y configuración ─────────────────────────
        log("INFO", "Cargando catálogo y configuración...")
        cat_data            = cargar_catalogo_completo()
        extraccion_map      = cat_data["extraccion_map"]
        tipo_calculo_map    = cat_data["tipo_calculo_map"]
        tipo_indicador_map  = cat_data["tipo_indicador_map"]
        variables_campo_map = cat_data["variables_campo_map"]

        kawak_validos    = cargar_kawak_validos()
        mapa_procesos    = cargar_mapa_procesos()
        config_patrones  = cargar_config_patrones()
        api_kawak_lookup = cargar_consolidado_api_kawak_lookup(extraccion_map)

        # ── Normalizar LLAVE en df_api ───────────────────────────────
        id_series    = df_api["Id"].map(_id_str)
        fecha_series = df_api["fecha"]
        df_api["LLAVE"] = (
            id_series
            + "-"
            + fecha_series.dt.year.astype(int).astype(str)
            + "-"
            + fecha_series.dt.month.astype(int).astype(str).str.zfill(2)
            + "-"
            + fecha_series.dt.day.astype(int).astype(str).str.zfill(2)
        )

        # ── Construir registros Histórico ────────────────────────────
        log("INFO", "[HISTÓRICO] Construyendo registros históricos...")
        regs_hist, skip_h, na_h = construir_registros_historico(
            df_api, llaves_hist, hist_escalas,
            config_patrones=config_patrones,
            mapa_procesos=mapa_procesos,
            kawak_validos=kawak_validos,
            extraccion_map=extraccion_map,
            api_kawak_lookup=api_kawak_lookup,
            variables_campo_map=variables_campo_map,
            tipo_indicador_map=tipo_indicador_map,
        )
        log("DATA", "[HISTÓRICO]", {
            "registros_nuevos": len(regs_hist),
            "descartados_existentes": skip_h,
            "descartados_no_aplica": na_h,
        })

        # ── Construir registros Semestral ────────────────────────────
        log("INFO", "[SEMESTRAL] Construyendo registros semestrales...")
        regs_sem, skip_s, na_s = construir_registros_semestral(
            df_api, llaves_sem, hist_escalas,
            config_patrones=config_patrones,
            mapa_procesos=mapa_procesos,
            kawak_validos=kawak_validos,
            extraccion_map=extraccion_map,
            api_kawak_lookup=api_kawak_lookup,
            tipo_calculo_map=tipo_calculo_map,
            variables_campo_map=variables_campo_map,
            tipo_indicador_map=tipo_indicador_map,
        )
        log("DATA", "[SEMESTRAL]", {
            "registros_nuevos": len(regs_sem),
            "descartados_existentes": skip_s,
            "descartados_no_aplica": na_s,
        })

        # ── Construir registros Cierres ──────────────────────────────
        log("INFO", "[CIERRES] Construyendo registros de cierre...")
        regs_cierres, skip_c, na_c = construir_registros_cierres(
            df_api, hist_escalas,
            config_patrones=config_patrones,
            mapa_procesos=mapa_procesos,
            kawak_validos=kawak_validos,
            extraccion_map=extraccion_map,
            api_kawak_lookup=api_kawak_lookup,
            tipo_calculo_map=tipo_calculo_map,
            variables_campo_map=variables_campo_map,
            tipo_indicador_map=tipo_indicador_map,
        )
        log("DATA", "[CIERRES]", {
            "registros_nuevos": len(regs_cierres),
            "descartados_existentes": skip_c,
            "descartados_no_aplica": na_c,
        })

        # ── Guardar registros ────────────────────────────────────────
        log("INFO", "Guardando registros en .pipeline_state/...")
        save_records("regs_hist", regs_hist)
        save_records("regs_sem", regs_sem)
        save_records("regs_cierres", regs_cierres)

        elapsed = round(time.time() - t0, 2)
        total = len(regs_hist) + len(regs_sem) + len(regs_cierres)
        resultado = {
            "historico_nuevos": len(regs_hist),
            "historico_descartados": skip_h,
            "semestral_nuevos": len(regs_sem),
            "cierres_nuevos": len(regs_cierres),
            "total_nuevos_a_insertar": total,
        }

        log("OK", f"Paso 06 completado en {elapsed}s", resultado)
        save_state("06", "Construir Registros", "ok", resultado)
        sys.exit(0)

    except FileNotFoundError as e:
        log("ERROR", str(e))
        save_state("06", "Construir Registros", "error", {"error": str(e)})
        sys.exit(1)

    except Exception as e:
        log("ERROR", f"Fallo en Paso 06: {e}")
        import traceback
        traceback.print_exc()
        save_state("06", "Construir Registros", "error", {"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
