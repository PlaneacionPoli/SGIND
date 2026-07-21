#!/usr/bin/env python3
"""
=============================================================
PIPELINE COMPLETO — EJECUTAR TODOS LOS PASOS EN SECUENCIA
=============================================================
Ejecuta los 13 scripts del pipeline ETL en orden.
Si un paso falla (exit code != 0), detiene la cadena y reporta.

EJECUTAR:
  python scripts/pipeline_steps/00_run_all.py
  python scripts/pipeline_steps/00_run_all.py --desde 06
=============================================================
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

_STEPS_DIR = Path(__file__).parent
_SCRIPTS_DIR = _STEPS_DIR.parent
_ROOT = _SCRIPTS_DIR.parent

# (step_id, nombre, ruta_absoluta_al_script)
PASOS = [
    ("00_api", "Consolidar API Kawak",    _SCRIPTS_DIR / "consolidar_api.py"),
    ("01",     "Cargar Fuente",           _STEPS_DIR   / "01_cargar_fuente.py"),
    ("02",     "Validar Contrato",        _STEPS_DIR   / "02_validar_contrato.py"),
    ("03_04",  "Catálogo + Metadatos",    _STEPS_DIR   / "03_04_cargar_catalogo_metadatos.py"),
    ("05",     "Abrir Workbook",          _STEPS_DIR   / "05_abrir_workbook.py"),
    ("06",     "Construir Registros",     _STEPS_DIR   / "06_construir_registros.py"),
    ("07",     "AGENT5 Correcciones",     _STEPS_DIR   / "07_aplicar_correcciones.py"),
    ("08",     "Validación Intermedia",   _STEPS_DIR   / "08_validacion_intermedia.py"),
    ("09_10",  "Escribir + Reparar",      _STEPS_DIR   / "09_10_escribir_reparar.py"),
    ("11",     "Deduplicar + Fórmulas",   _STEPS_DIR   / "11_deduplicar_formulas.py"),
    ("12",     "Actualizar Catálogo",     _STEPS_DIR   / "12_actualizar_catalogo.py"),
    ("13",     "Guardar",                 _STEPS_DIR   / "13_guardar.py"),
    ("14_15",  "Auditoría + Respaldo",    _STEPS_DIR   / "14_15_auditoria_respaldo.py"),
]


def ts():
    return datetime.now().strftime("%H:%M:%S")


def main():
    parser = argparse.ArgumentParser(description="Pipeline ETL completo")
    parser.add_argument("--desde", metavar="PASO_ID", default=None,
                        help="Iniciar desde este step_id (ej: --desde 06)")
    args = parser.parse_args()

    print()
    print(f"  [{ts()}] PIPELINE ETL — Resultados Consolidados")
    print(f"  {'─' * 58}")
    print()

    pasos_a_ejecutar = PASOS
    if args.desde:
        idx = next((i for i, (pid, _, _) in enumerate(PASOS) if pid == args.desde), None)
        if idx is None:
            ids_validos = [p[0] for p in PASOS]
            print(f"  ❌ Paso '{args.desde}' no encontrado.")
            print(f"     IDs válidos: {ids_validos}")
            sys.exit(1)
        pasos_a_ejecutar = PASOS[idx:]
        print(f"  ▶ Iniciando desde paso {args.desde}\n")

    resultados = []
    t_total = time.time()
    abortado = False

    for step_id, nombre, script_path in pasos_a_ejecutar:
        if not script_path.exists():
            print(f"  [{ts()}] ⚠️  {step_id:<7} Script no encontrado: {script_path}")
            resultados.append((step_id, nombre, False, 0.0))
            break

        print(f"  [{ts()}] ▶ {step_id:<7} {nombre}")

        t0 = time.time()
        ok = False
        try:
            # CREATE_NEW_PROCESS_GROUP: aísla al hijo de las señales CTRL+C/CTRL+BREAK
            # que llegan a la consola del padre, evitando interrupciones espurias.
            popen_kwargs = {}
            if sys.platform == "win32":
                popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

            proc = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(_ROOT),
                **popen_kwargs,
            )
            try:
                proc.wait()
            except KeyboardInterrupt:
                # Verificar si el hijo ya terminó antes del SIGINT
                # (falso positivo por propagación de señal en Windows)
                if proc.poll() is not None:
                    pass  # el hijo ya terminó bien — ignorar la señal
                else:
                    # Interrumpido mientras el hijo corría — detener
                    proc.wait()
                    elapsed = round(time.time() - t0, 2)
                    print(f"\n  [{ts()}] ⏹  Interrumpido por el usuario")
                    resultados.append((step_id, nombre, False, elapsed))
                    abortado = True
                    break

            elapsed = round(time.time() - t0, 2)
            ok = proc.returncode == 0
        except Exception as e:
            elapsed = round(time.time() - t0, 2)
            print(f"         ❌ Error al lanzar script: {e}")

        resultados.append((step_id, nombre, ok, elapsed))

        if not ok:
            print()
            print(f"  [{ts()}] ❌ PIPELINE DETENIDO en paso {step_id} — {nombre}")
            print()
            break

        print()

    # ── Resumen final ────────────────────────────────────────────────
    duracion_total = round(time.time() - t_total, 1)
    n_ok = sum(1 for _, _, ok, _ in resultados if ok)
    ancho = 58

    print(f"  ╔{'═' * ancho}╗")
    print(f"  ║{'PIPELINE COMPLETO — RESUMEN FINAL':^{ancho}}║")
    print(f"  ╠{'═' * ancho}╣")

    ids_ejecutados = {r[0] for r in resultados}
    for step_id, nombre, ok, elapsed in resultados:
        icono = "✅" if ok else ("⏹ " if abortado and step_id == resultados[-1][0] else "❌")
        print(f"  ║  {icono} {step_id:<7} {nombre:<38} {elapsed:>6}s  ║")

    for step_id, nombre, script_path in PASOS:
        if step_id not in ids_ejecutados:
            print(f"  ║  ⏭  {step_id:<7} {nombre:<38} {'—':>7}   ║")

    print(f"  ╠{'═' * ancho}╣")
    resumen = f"TOTAL: {duracion_total}s  |  {n_ok}/{len(resultados)} pasos OK"
    if abortado:
        resumen += "  |  INTERRUMPIDO"
    print(f"  ║  {resumen:<{ancho - 2}}  ║")
    print(f"  ╚{'═' * ancho}╝")
    print()

    sys.exit(0 if n_ok == len(pasos_a_ejecutar) else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n  [{datetime.now().strftime('%H:%M:%S')}] ⏹  Interrumpido")
        sys.exit(1)
