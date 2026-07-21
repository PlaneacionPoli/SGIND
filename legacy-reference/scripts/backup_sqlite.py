"""
scripts/backup_sqlite.py
------------------------
Script de backup diario para data/db/registros_om.db

USO:
    python scripts/backup_sqlite.py              # backup manual inmediato
    python scripts/backup_sqlite.py --retention 30  # mantener 30 días (default: 14)

AUTOMATIZACIÓN (Windows Task Scheduler):
    Acción → Programa: python
    Argumentos: C:\ruta\scripts\backup_sqlite.py
    Iniciar en: C:\ruta\

AUTOMATIZACIÓN (cron Linux/Mac):
    0 2 * * * cd /ruta && python scripts/backup_sqlite.py

El backup se guarda en data/db/backups/registros_om_YYYYMMDD_HHMMSS.db
Los backups más antiguos que --retention días se eliminan automáticamente.
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "data" / "db" / "registros_om.db"
BACKUP_DIR = ROOT / "data" / "db" / "backups"
DEFAULT_RETENTION_DAYS = 14


def _backup_sqlite_online(src: Path, dst: Path) -> None:
    """Usa la API de backup de SQLite3 (safe con WAL y escrituras concurrentes)."""
    con_src = sqlite3.connect(src)
    con_dst = sqlite3.connect(dst)
    try:
        con_src.backup(con_dst)
    finally:
        con_dst.close()
        con_src.close()


def run_backup(db_path: Path = DB_PATH, retention_days: int = DEFAULT_RETENTION_DAYS) -> Path:
    """
    Realiza un backup de db_path en BACKUP_DIR y elimina backups antiguos.

    Returns:
        Path al archivo de backup creado.

    Raises:
        FileNotFoundError: Si db_path no existe.
    """
    if not db_path.exists():
        raise FileNotFoundError(
            f"Base de datos no encontrada: {db_path}\n"
            "Asegúrate de que la aplicación haya inicializado la BD al menos una vez."
        )

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"registros_om_{timestamp}.db"

    print(f"[backup_sqlite] Origen  : {db_path}")
    print(f"[backup_sqlite] Destino : {backup_path}")

    _backup_sqlite_online(db_path, backup_path)

    size_kb = backup_path.stat().st_size / 1024
    print(f"[backup_sqlite] Tamaño  : {size_kb:.1f} KB  ✓")

    # Verificación de integridad básica
    con = sqlite3.connect(backup_path)
    try:
        result = con.execute("PRAGMA integrity_check").fetchone()
        if result and result[0] == "ok":
            print("[backup_sqlite] Integridad: OK ✓")
        else:
            print(f"[backup_sqlite] ADVERTENCIA integridad: {result}")
    finally:
        con.close()

    # Purgar backups más antiguos que retention_days
    cutoff = datetime.now() - timedelta(days=retention_days)
    removed = 0
    for old in sorted(BACKUP_DIR.glob("registros_om_*.db")):
        if old == backup_path:
            continue
        mtime = datetime.fromtimestamp(old.stat().st_mtime)
        if mtime < cutoff:
            old.unlink()
            removed += 1

    if removed:
        print(f"[backup_sqlite] Purgados: {removed} backup(s) con más de {retention_days} días")

    # Listar backups existentes
    existing = sorted(BACKUP_DIR.glob("registros_om_*.db"))
    print(f"[backup_sqlite] Backups disponibles: {len(existing)}")

    return backup_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backup diario de registros_om.db con retención automática"
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DB_PATH,
        help=f"Ruta a la BD SQLite (default: {DB_PATH})",
    )
    parser.add_argument(
        "--retention",
        type=int,
        default=DEFAULT_RETENTION_DAYS,
        help=f"Días de retención de backups (default: {DEFAULT_RETENTION_DAYS})",
    )
    args = parser.parse_args()

    try:
        backup_path = run_backup(db_path=args.db, retention_days=args.retention)
        print(f"[backup_sqlite] COMPLETADO → {backup_path.name}")
    except FileNotFoundError as exc:
        print(f"[backup_sqlite] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"[backup_sqlite] ERROR inesperado: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
