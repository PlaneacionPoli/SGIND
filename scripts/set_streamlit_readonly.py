#!/usr/bin/env python3
"""
Script de mantenimiento — pone el Streamlit legacy en modo read-only (mantenimiento).

Funciona escribiendo/borrando el archivo .maintenance_mode en el directorio raíz
del proyecto. El app.py de Streamlit detecta ese archivo al iniciar y muestra
un mensaje de mantenimiento en lugar del dashboard.

Uso:
    # Activar modo mantenimiento:
    python sgind-v2/scripts/set_streamlit_readonly.py --enable

    # Activar con URL de v2 (se muestra al usuario):
    python sgind-v2/scripts/set_streamlit_readonly.py --enable --v2-url https://sgind-v2.poli.edu.co

    # Desactivar (volver al funcionamiento normal):
    python sgind-v2/scripts/set_streamlit_readonly.py --disable

    # Estado actual:
    python sgind-v2/scripts/set_streamlit_readonly.py --status

    # Archivar código Streamlit (T+30 días, solo si ya no se necesita):
    python sgind-v2/scripts/set_streamlit_readonly.py --archive

Requisitos Streamlit Cloud:
    Si el Streamlit está deployado en Streamlit Cloud, el archivo .maintenance_mode
    debe estar commiteado en el repo Y el branch producción pusheado.
    Alternativamente, usar la variable de entorno SGIND_MAINTENANCE_MODE=1
    en Settings → Secrets de la app en Streamlit Cloud.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ─── Rutas ───────────────────────────────────────────────────────────────────

SCRIPT_DIR   = Path(__file__).resolve().parent          # sgind-v2/scripts/
SGIND_V2_DIR = SCRIPT_DIR.parent                         # sgind-v2/
REPO_ROOT    = SGIND_V2_DIR.parent                       # raíz del repo

FLAG_FILE    = REPO_ROOT / ".maintenance_mode"
APP_PY       = REPO_ROOT / "app.py"

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _ok(msg: str)   -> None: print(f"  \033[92m✓\033[0m {msg}")
def _fail(msg: str) -> None: print(f"  \033[91m✗\033[0m {msg}", file=sys.stderr)
def _info(msg: str) -> None: print(f"  \033[94m→\033[0m {msg}")


# ─── Acciones ─────────────────────────────────────────────────────────────────

def enable_maintenance(v2_url: str = "") -> int:
    if FLAG_FILE.exists():
        _info(f"Modo mantenimiento ya estaba activo ({FLAG_FILE})")
    else:
        content = f"SGIND_V2_URL={v2_url}\n" if v2_url else ""
        FLAG_FILE.write_text(content, encoding="utf-8")
        _ok(f"Archivo creado: {FLAG_FILE}")

    if v2_url:
        _info(f"URL v2 configurada: {v2_url}")

    print()
    print("  \033[1mPróximos pasos:\033[0m")
    print("  1. Commitear el archivo .maintenance_mode al repo:")
    print("     git add .maintenance_mode && git commit -m 'chore: activar modo mantenimiento'")
    print("  2. Pushear al branch de producción:")
    print("     git push origin main")
    print("  3. Streamlit Cloud auto-redeploy mostrará el mensaje de mantenimiento.")
    print()
    print("  Alternativa (sin commit) — en Streamlit Cloud > Settings > Secrets:")
    print("     SGIND_MAINTENANCE_MODE = 1")
    if v2_url:
        print(f"     SGIND_V2_URL = {v2_url}")
    return 0


def disable_maintenance() -> int:
    if not FLAG_FILE.exists():
        _info("Modo mantenimiento ya estaba desactivado (archivo no existe)")
        return 0

    FLAG_FILE.unlink()
    _ok(f"Archivo eliminado: {FLAG_FILE}")

    print()
    print("  \033[1mPróximos pasos:\033[0m")
    print("  1. Commitear la eliminación:")
    print("     git add .maintenance_mode && git commit -m 'chore: desactivar modo mantenimiento'")
    print("  2. Pushear al branch de producción:")
    print("     git push origin main")
    return 0


def status() -> int:
    print(f"\n  Flag file: {FLAG_FILE}")
    if FLAG_FILE.exists():
        content = FLAG_FILE.read_text(encoding="utf-8").strip()
        print(f"  \033[91m● MANTENIMIENTO ACTIVO\033[0m")
        if content:
            _info(f"Contenido: {content}")
    else:
        print(f"  \033[92m● Sistema operativo (sin modo mantenimiento)\033[0m")

    print(f"\n  app.py verificado: {'✓ existe' if APP_PY.exists() else '✗ no encontrado'}")
    return 0


def archive_streamlit() -> int:
    """Mueve el código legacy a una carpeta archivada. Solo usar T+30 días."""
    ARCHIVE_DIR = REPO_ROOT / "streamlit_legacy_archived"

    dirs_to_move = [
        REPO_ROOT / "streamlit_app",
    ]
    files_to_move = [
        REPO_ROOT / "app.py",
    ]

    print("  \033[93m⚠ Esta acción MUEVE el código Streamlit a streamlit_legacy_archived/\033[0m")
    print("  Solo ejecutar cuando v2 lleve 30+ días estable en producción.")
    confirm = input("  ¿Confirmar? (escribe 'ARCHIVAR' para continuar): ")
    if confirm.strip() != "ARCHIVAR":
        _info("Operación cancelada.")
        return 0

    ARCHIVE_DIR.mkdir(exist_ok=True)

    import shutil

    for d in dirs_to_move:
        if d.exists():
            dest = ARCHIVE_DIR / d.name
            shutil.move(str(d), str(dest))
            _ok(f"Movido: {d.name} → streamlit_legacy_archived/{d.name}")
        else:
            _info(f"No encontrado (ya archivado?): {d}")

    for f in files_to_move:
        if f.exists():
            dest = ARCHIVE_DIR / f.name
            shutil.move(str(f), str(dest))
            _ok(f"Movido: {f.name} → streamlit_legacy_archived/{f.name}")
        else:
            _info(f"No encontrado (ya archivado?): {f}")

    # Eliminar flag de mantenimiento si existe
    if FLAG_FILE.exists():
        FLAG_FILE.unlink()
        _ok("Archivo .maintenance_mode eliminado")

    print()
    print("  \033[1mListo. Streamlit legacy archivado.\033[0m")
    print("  Próximos pasos:")
    print("  1. git add -A && git commit -m 'chore: archivar código Streamlit legacy'")
    print("  2. git push origin main")
    print("  3. Actualizar README.md del repo raíz")
    return 0


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Activar/desactivar modo mantenimiento en Streamlit legacy"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--enable",  action="store_true", help="Activar modo mantenimiento")
    group.add_argument("--disable", action="store_true", help="Desactivar modo mantenimiento")
    group.add_argument("--status",  action="store_true", help="Ver estado actual")
    group.add_argument("--archive", action="store_true", help="Archivar código Streamlit (T+30 días)")
    parser.add_argument("--v2-url", default="", help="URL de SGIND v2 (mostrada al usuario en mantenimiento)")
    args = parser.parse_args()

    print(f"\n\033[1mSGIND — Control de modo mantenimiento\033[0m")
    print(f"  Repo: {REPO_ROOT}\n")

    if args.enable:
        return enable_maintenance(v2_url=args.v2_url)
    if args.disable:
        return disable_maintenance()
    if args.status:
        return status()
    if args.archive:
        return archive_streamlit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
