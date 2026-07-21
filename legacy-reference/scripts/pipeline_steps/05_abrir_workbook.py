#!/usr/bin/env python3
"""
=============================================================
PASO 05 — ABRIR WORKBOOK Y LEER ESTADO EXISTENTE
=============================================================
QUÉ HACE:
  Abre Resultados Consolidados.xlsx, extrae las LLAVEs existentes
  en cada hoja (Histórico, Semestral, Cierres), preserva signos
  Meta_Signo/Ejecucion_Signo ya ingresados, purga filas inválidas,
  crea versión de seguridad (backup pre-consolidación) y guarda
  el estado en .pipeline_state/workbook_meta.json.

ENTRADA:
  data/output/Resultados Consolidados.xlsx  (o fuente)
  data/raw/Resultados_Consolidados_Fuente.xlsx  (fallback)

SALIDA:
  .pipeline_state/workbook_meta.json  (llaves, signos, escalas)

DEPENDENCIAS:
  Ninguna (lee directamente del workbook).

EJECUTAR:
  python scripts/pipeline_steps/05_abrir_workbook.py
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
import openpyxl  # noqa: E402

from _state import save_state, save_json  # noqa: E402
from etl.config import OUTPUT_FILE, INPUT_FILE  # noqa: E402
from etl.versioning import VersionManager  # noqa: E402
from etl.audit import AuditTrail  # noqa: E402
from etl.signos import obtener_signos  # noqa: E402
from etl.purga import purgar_filas_invalidas, limpiar_cierres_existentes  # noqa: E402
from etl.escritura import llaves_de_df  # noqa: E402
from etl.formulas_excel import _ensure_tipo_registro_header  # noqa: E402
from etl.fuentes import cargar_kawak_validos  # noqa: E402
from etl.normalizacion import _id_str  # noqa: E402
from etl.workbook_io import workbook_local_copy  # noqa: E402


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
    log("INFO", "Iniciando Paso 05 — Abrir Workbook y Leer Estado Existente")
    t0 = time.time()

    # Determinar archivo fuente
    if OUTPUT_FILE.exists():
        fuente = OUTPUT_FILE
        log("INFO", f"Usando output existente: {OUTPUT_FILE.name}")
    elif INPUT_FILE.exists():
        fuente = INPUT_FILE
        log("WARN", f"Output no existe, usando fuente: {INPUT_FILE.name}")
    else:
        msg = f"No se encontró workbook: ni {OUTPUT_FILE} ni {INPUT_FILE}"
        log("ERROR", msg)
        save_state("05", "Abrir Workbook", "error", {"error": msg})
        sys.exit(1)

    try:
        # ── Crear versión de seguridad ───────────────────────────────
        log("INFO", "Creando versión de seguridad pre-consolidación...")
        vm = VersionManager(OUTPUT_FILE, max_versions=5)
        trail = AuditTrail()
        version_creada = False
        try:
            if OUTPUT_FILE.exists():
                vm.crear_version(tag="pre_consolidacion")
                version_creada = True
                log("INFO", "Versión de seguridad creada.")
        except Exception as e:
            log("WARN", f"No se pudo crear versión de seguridad: {e}")

        # ── Abrir workbook ───────────────────────────────────────────
        log("INFO", f"Abriendo workbook {fuente.name}...")

        kawak_validos = cargar_kawak_validos()

        with workbook_local_copy(fuente) as (local_file, source_wb):
            wb = openpyxl.load_workbook(local_file)

            hojas_disponibles = wb.sheetnames
            log("INFO", f"Hojas disponibles: {hojas_disponibles}")

            ws_hist    = wb["Consolidado Historico"]
            ws_sem     = wb["Consolidado Semestral"]
            ws_cierres = wb["Consolidado Cierres"]

            # ── Purgar filas inválidas ───────────────────────────────
            log("INFO", "Purgando filas inválidas...")
            for ws, nom in [(ws_hist, "Historico"), (ws_sem, "Semestral"), (ws_cierres, "Cierres")]:
                _ensure_tipo_registro_header(ws)
                purgar_filas_invalidas(ws, nom, kawak_validos)
            limpiar_cierres_existentes(ws_cierres)

            # ── Leer hojas existentes ────────────────────────────────
            log("INFO", "Leyendo datos existentes para llaves y signos...")
            with pd.ExcelFile(local_file) as xls:
                df_hist_ex    = pd.read_excel(xls, sheet_name="Consolidado Historico")
                df_sem_ex     = pd.read_excel(xls, sheet_name="Consolidado Semestral")
                df_cierres_ex = pd.read_excel(xls, sheet_name="Consolidado Cierres")

        # ── Calcular signos ──────────────────────────────────────────
        log("INFO", "Calculando signos por indicador...")
        signos = obtener_signos(df_hist_ex, df_sem_ex, df_cierres_ex)

        # ── Extraer LLAVEs ───────────────────────────────────────────
        llaves_hist    = list(llaves_de_df(df_hist_ex))
        llaves_sem     = list(llaves_de_df(df_sem_ex))
        llaves_cierres = list(llaves_de_df(df_cierres_ex))

        # ── Extraer hist_escalas ─────────────────────────────────────
        hist_escalas = {}
        if not df_hist_ex.empty and "Id" in df_hist_ex.columns:
            df_tmp = (
                df_hist_ex
                .assign(_id=df_hist_ex["Id"].map(_id_str))
                .loc[lambda d: d["_id"].astype(str).str.len() > 0, ["_id", "Meta", "Ejecucion"]]
                .drop_duplicates(subset=["_id"], keep="first")
                .set_index("_id")
            )
            for idx, row in df_tmp.iterrows():
                meta = row.get("Meta")
                ejec = row.get("Ejecucion")
                hist_escalas[str(idx)] = {
                    "Meta": None if (meta != meta) else meta,
                    "Ejecucion": None if (ejec != ejec) else ejec,
                }

        # ── Preservar signos existentes ──────────────────────────────
        signos_preservados = 0
        for col in ["Meta_Signo", "Ejecucion_Signo"]:
            if col in df_hist_ex.columns:
                signos_preservados += df_hist_ex[col].notna().sum()

        # Rango de fechas existente
        fecha_min = fecha_max = "?"
        if "Fecha" in df_hist_ex.columns:
            fechas = pd.to_datetime(df_hist_ex["Fecha"], errors="coerce").dropna()
            if not fechas.empty:
                fecha_min = str(fechas.min().date())
                fecha_max = str(fechas.max().date())

        # ── Guardar estado ───────────────────────────────────────────
        meta = {
            "fuente_usada": str(fuente),
            "llaves_hist": llaves_hist,
            "llaves_sem": llaves_sem,
            "llaves_cierres": llaves_cierres,
            "signos": {str(k): {sk: str(sv) for sk, sv in v.items()} for k, v in signos.items()},
            "hist_escalas": hist_escalas,
            "version_creada": version_creada,
        }
        save_json("workbook_meta", meta)

        elapsed = round(time.time() - t0, 2)
        resultado = {
            "fuente_usada": fuente.name,
            "llaves_historico": f"{len(llaves_hist):,}",
            "llaves_semestral": f"{len(llaves_sem):,}",
            "llaves_cierres": f"{len(llaves_cierres):,}",
            "signos_preservados": signos_preservados,
            "rango_fechas_existente": f"{fecha_min} → {fecha_max}",
            "indicadores_con_signo": len(signos),
            "version_seguridad": "creada" if version_creada else "omitida",
        }

        log("OK", f"Paso 05 completado en {elapsed}s", resultado)
        save_state("05", "Abrir Workbook", "ok", resultado)
        sys.exit(0)

    except Exception as e:
        log("ERROR", f"Fallo en Paso 05: {e}")
        import traceback
        traceback.print_exc()
        save_state("05", "Abrir Workbook", "error", {"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
