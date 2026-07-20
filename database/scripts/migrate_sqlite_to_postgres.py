#!/usr/bin/env python3
"""
Migración SQLite → PostgreSQL — SGIND v2 (Fase 2)

Uso:
    python sgind-v2/database/scripts/migrate_sqlite_to_postgres.py \\
        --sqlite data/db/registros_om.db \\
        --postgres postgresql://sgind:pass@localhost:5432/sgind

    # Solo validar (dry-run):
    python ... --dry-run

Genera reporte JSON en sgind-v2/database/reports/
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None  # type: ignore

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SQLITE = ROOT / "data" / "db" / "registros_om.db"
REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"

OM_COLUMNS = [
    "id_indicador",
    "nombre_indicador",
    "proceso",
    "periodo",
    "anio",
    "sede",
    "tiene_om",
    "tipo_accion",
    "numero_om",
    "comentario",
    "registrado_por",
    "fecha_registro",
]

OM_COLUMN_ALIASES = {
    "tipo_accion": ["tipo_accion", "tipo_accion_om"],
}


def _row_get(row: dict, col: str):
    if col in row and row[col] is not None:
        return row[col]
    for alias in OM_COLUMN_ALIASES.get(col, []):
        if alias in row and row[alias] is not None:
            return row[alias]
    defaults = {"tiene_om": 0, "tipo_accion": "OM Kawak", "registrado_por": ""}
    return defaults.get(col)


def read_sqlite_om(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM registros_om ORDER BY id")
    return [dict(r) for r in cur.fetchall()]


def read_sqlite_acciones(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM acciones ORDER BY id")
    except sqlite3.OperationalError:
        return []
    return [dict(r) for r in cur.fetchall()]


def map_om_row(row: dict) -> dict:
    mapped = {}
    for col in OM_COLUMNS:
        mapped[col] = _row_get(row, col)
    if mapped.get("anio") is not None:
        try:
            mapped["anio"] = int(mapped["anio"])
        except (TypeError, ValueError):
            mapped["anio"] = None
    if mapped.get("tiene_om") is not None:
        try:
            mapped["tiene_om"] = int(mapped["tiene_om"])
        except (TypeError, ValueError):
            mapped["tiene_om"] = 0
    return mapped


def map_accion_row(row: dict) -> dict:
    known = {"id", "ACCION", "RESPONSABLE", "ESTADO", "test_marker"}
    payload = {k: v for k, v in row.items() if k not in known and v is not None}
    marker_col = None
    marker_value = None
    if "test_marker" in row:
        marker_col = "test_marker"
        marker_value = row.get("test_marker")
    return {
        "accion": row.get("ACCION"),
        "responsable": row.get("RESPONSABLE"),
        "estado": row.get("ESTADO"),
        "marker_col": marker_col,
        "marker_value": str(marker_value) if marker_value is not None else None,
        "payload": payload,
    }


def migrate_registros_om(pg_conn, rows: list[dict], dry_run: bool) -> int:
    if dry_run:
        return len(rows)
    cur = pg_conn.cursor()
    sql = """
        INSERT INTO registros_om (
            id_indicador, nombre_indicador, proceso, periodo, anio, sede,
            tiene_om, tipo_accion, numero_om, comentario, registrado_por, fecha_registro
        ) VALUES (
            %(id_indicador)s, %(nombre_indicador)s, %(proceso)s, %(periodo)s, %(anio)s, %(sede)s,
            %(tiene_om)s, %(tipo_accion)s, %(numero_om)s, %(comentario)s,
            %(registrado_por)s, %(fecha_registro)s
        )
        ON CONFLICT ON CONSTRAINT registros_om_unique_key DO UPDATE SET
            nombre_indicador = EXCLUDED.nombre_indicador,
            proceso = EXCLUDED.proceso,
            sede = EXCLUDED.sede,
            tiene_om = EXCLUDED.tiene_om,
            tipo_accion = EXCLUDED.tipo_accion,
            numero_om = EXCLUDED.numero_om,
            comentario = EXCLUDED.comentario,
            registrado_por = EXCLUDED.registrado_por,
            fecha_registro = EXCLUDED.fecha_registro,
            updated_at = NOW()
    """
    count = 0
    for raw in rows:
        data = map_om_row(raw)
        if not data.get("id_indicador"):
            continue
        cur.execute(sql, data)
        count += 1
    pg_conn.commit()
    cur.close()
    return count


def migrate_acciones(pg_conn, rows: list[dict], dry_run: bool) -> int:
    if dry_run:
        return len(rows)
    cur = pg_conn.cursor()
    sql = """
        INSERT INTO acciones (accion, responsable, estado, marker_col, marker_value, payload)
        VALUES (%(accion)s, %(responsable)s, %(estado)s, %(marker_col)s, %(marker_value)s, %(payload)s)
    """
    count = 0
    for raw in rows:
        data = map_accion_row(raw)
        cur.execute(sql, {**data, "payload": json.dumps(data["payload"])})
        count += 1
    pg_conn.commit()
    cur.close()
    return count


def validate_migration(pg_conn) -> dict:
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM registros_om")
    om_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM acciones")
    acc_count = cur.fetchone()[0]
    cur.execute(
        """
        SELECT COUNT(*) FROM (
            SELECT id_indicador, periodo, anio, COUNT(*) c
            FROM registros_om
            GROUP BY id_indicador, periodo, anio
            HAVING COUNT(*) > 1
        ) d
        """
    )
    dupes = cur.fetchone()[0]
    cur.close()
    return {"registros_om": om_count, "acciones": acc_count, "duplicates": dupes}


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrar SQLite legacy a PostgreSQL SGIND v2")
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--postgres", type=str, default=None, help="DATABASE_URL sync (postgresql://)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.sqlite.exists():
        print(f"ERROR: SQLite no encontrado: {args.sqlite}", file=sys.stderr)
        return 1

    if psycopg2 is None and not args.dry_run:
        print("ERROR: instale psycopg2-binary para migración real", file=sys.stderr)
        return 1

    if not args.postgres and not args.dry_run:
        print("ERROR: especifique --postgres o use --dry-run", file=sys.stderr)
        return 1

    sqlite_conn = sqlite3.connect(args.sqlite)
    om_rows = read_sqlite_om(sqlite_conn)
    acc_rows = read_sqlite_acciones(sqlite_conn)
    sqlite_conn.close()

    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "sqlite_path": str(args.sqlite),
        "dry_run": args.dry_run,
        "source": {"registros_om": len(om_rows), "acciones": len(acc_rows)},
        "migrated": {},
        "validation": {},
        "status": "ok",
    }

    if args.dry_run:
        report["migrated"] = {"registros_om": len(om_rows), "acciones": len(acc_rows)}
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    dsn = args.postgres.replace("postgresql+asyncpg://", "postgresql://")
    pg_conn = psycopg2.connect(dsn)
    try:
        report["migrated"]["registros_om"] = migrate_registros_om(pg_conn, om_rows, False)
        report["migrated"]["acciones"] = migrate_acciones(pg_conn, acc_rows, False)
        report["validation"] = validate_migration(pg_conn)
        if report["validation"].get("duplicates", 0) > 0:
            report["status"] = "warning"
    finally:
        pg_conn.close()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / f"migration_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"Reporte guardado: {out}")
    return 0 if report["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
