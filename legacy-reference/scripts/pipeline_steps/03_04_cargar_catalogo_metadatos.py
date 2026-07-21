#!/usr/bin/env python3
"""
=============================================================
PASOS 03+04 — CATÁLOGO + METADATOS (AGRUPADOS)
=============================================================
QUÉ HACE:
  PASO 03 — Catálogo: Lee la hoja "Catalogo Indicadores" del workbook
  y construye los mapas de extracción, tipo de cálculo, tipo de
  indicador y campos de variables.

  PASO 04 — Metadatos: Carga y cruza los catálogos auxiliares:
  Indicadores Kawak, mapeo CMI, ficha técnica y reporte LMI.
  También precalcula api_kawak_lookup y config_patrones.

ENTRADA:
  data/output/Resultados Consolidados.xlsx  (o fuente)
  data/raw/Fuentes Consolidadas/Indicadores Kawak.xlsx
  data/raw/Indicadores por CMI.xlsx
  config/settings.toml

SALIDA:
  .pipeline_state/cat_data.json     (mapas del catálogo)
  .pipeline_state/kawak_validos.json
  .pipeline_state/mapa_procesos.json

DEPENDENCIAS:
  Ninguna (lee directamente de archivos fuente).

EJECUTAR:
  python scripts/pipeline_steps/03_04_cargar_catalogo_metadatos.py
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

from _state import save_state, save_json  # noqa: E402
from etl.catalogo import cargar_catalogo_completo, cargar_config_patrones  # noqa: E402
from etl.fuentes import (  # noqa: E402
    cargar_kawak_validos,
    cargar_metadatos_kawak,
    cargar_metadatos_cmi,
    cargar_mapa_procesos,
    cargar_lmi_reporte,
    cargar_consolidado_api_kawak_lookup,
)


def log(nivel, mensaje, datos=None):
    ts = datetime.now().strftime("%H:%M:%S")
    iconos = {"INFO": "ℹ️ ", "OK": "✅", "ERROR": "❌", "WARN": "⚠️ ", "DATA": "📊"}
    icono = iconos.get(nivel, "•")
    print(f"[{ts}] {icono} {nivel:<5} | {mensaje}")
    if datos:
        for k, v in datos.items():
            print(f"           {'':5}   {k}: {v}")
    sys.stdout.flush()


def _safe_len(obj):
    try:
        return len(obj)
    except Exception:
        return "?"


def main():
    parser = argparse.ArgumentParser(description="Pasos 03+04 — Catálogo + Metadatos")
    parser.parse_args()

    log("INFO", "Iniciando Pasos 03+04 — Catálogo + Metadatos")
    t0 = time.time()

    try:
        # ── PASO 03: Catálogo ────────────────────────────────────────
        log("INFO", "[PASO 03] Cargando catálogo de indicadores...")
        cat_data = cargar_catalogo_completo()

        extraccion_map      = cat_data.get("extraccion_map", {})
        tipo_calculo_map    = cat_data.get("tipo_calculo_map", {})
        tipo_indicador_map  = cat_data.get("tipo_indicador_map", {})
        variables_campo_map = cat_data.get("variables_campo_map", {})

        tipo_calculo_dist = {}
        for v in tipo_calculo_map.values():
            tipo_calculo_dist[str(v)] = tipo_calculo_dist.get(str(v), 0) + 1

        log("DATA", "[PASO 03] Resultados catálogo", {
            "indicadores_en_catalogo": _safe_len(extraccion_map),
            "con_tipo_extraccion": _safe_len(extraccion_map),
            "tipo_calculo_dist": tipo_calculo_dist,
            "variables_mapeadas": _safe_len(variables_campo_map),
        })

        # ── PASO 04: Metadatos ───────────────────────────────────────
        log("INFO", "[PASO 04] Cargando metadatos y catálogos auxiliares...")

        kawak_validos   = cargar_kawak_validos()
        metadatos_kawak = cargar_metadatos_kawak()
        metadatos_cmi   = cargar_metadatos_cmi()
        mapa_procesos   = cargar_mapa_procesos()
        ids_metrica     = cargar_lmi_reporte()

        log("INFO", "[PASO 04] Calculando api_kawak_lookup...")
        api_kawak_lookup = cargar_consolidado_api_kawak_lookup(extraccion_map)

        log("INFO", "[PASO 04] Cargando config_patrones...")
        config_patrones = cargar_config_patrones()

        # Metadatos kawak stats
        n_kawak = _safe_len(metadatos_kawak) if hasattr(metadatos_kawak, "__len__") else "?"
        n_cmi   = _safe_len(metadatos_cmi) if hasattr(metadatos_cmi, "__len__") else "?"
        n_proc  = _safe_len(mapa_procesos) if hasattr(mapa_procesos, "__len__") else "?"

        ids_metrica_list = list(ids_metrica) if hasattr(ids_metrica, "__iter__") else []

        sin_metadato = []
        if hasattr(metadatos_kawak, "__len__") and hasattr(extraccion_map, "keys"):
            ids_cat = set(str(k) for k in extraccion_map.keys())
            if hasattr(metadatos_kawak, "index"):
                ids_meta = set(str(i) for i in metadatos_kawak.index)
                sin_metadato = list(ids_cat - ids_meta)[:10]

        log("DATA", "[PASO 04] Resultados metadatos", {
            "indicadores_kawak": n_kawak,
            "procesos_mapeados": n_proc,
            "indicadores_cmi": n_cmi,
            "indicadores_lmi": _safe_len(ids_metrica_list),
            "api_kawak_lookup_entradas": _safe_len(api_kawak_lookup),
            "config_patrones": _safe_len(config_patrones),
            "indicadores_sin_metadato": len(sin_metadato),
        })

        if sin_metadato:
            log("WARN", f"IDs sin metadato: {sin_metadato[:5]}...")

        # ── Serializar a estado ──────────────────────────────────────
        log("INFO", "Guardando estado en .pipeline_state/...")

        # cat_data: los mapas son dict[str, str|int] → JSON-serializable
        save_json("cat_data", {
            "extraccion_map": {str(k): str(v) for k, v in extraccion_map.items()},
            "tipo_calculo_map": {str(k): str(v) for k, v in tipo_calculo_map.items()},
            "tipo_indicador_map": {str(k): str(v) for k, v in tipo_indicador_map.items()},
            "variables_campo_map": {str(k): str(v) for k, v in variables_campo_map.items()},
        })

        kawak_validos_list = list(str(x) for x in kawak_validos) if hasattr(kawak_validos, "__iter__") else []
        save_json("kawak_validos", kawak_validos_list)

        mapa_proc_serializable = {}
        if hasattr(mapa_procesos, "items"):
            mapa_proc_serializable = {str(k): str(v) for k, v in mapa_procesos.items()}
        save_json("mapa_procesos", mapa_proc_serializable)

        elapsed = round(time.time() - t0, 2)
        resultado = {
            "paso_03_indicadores_catalogo": _safe_len(extraccion_map),
            "paso_03_tipo_calculo_dist": tipo_calculo_dist,
            "paso_04_kawak_validos": _safe_len(kawak_validos_list),
            "paso_04_procesos_mapeados": n_proc,
            "paso_04_api_lookup_entradas": _safe_len(api_kawak_lookup),
            "paso_04_sin_metadato": len(sin_metadato),
        }

        log("OK", f"Pasos 03+04 completados en {elapsed}s", resultado)
        save_state("03_04", "Catálogo + Metadatos", "ok", resultado)
        sys.exit(0)

    except Exception as e:
        log("ERROR", f"Fallo en Pasos 03+04: {e}")
        import traceback
        traceback.print_exc()
        save_state("03_04", "Catálogo + Metadatos", "error", {"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
