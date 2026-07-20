#!/usr/bin/env python3
"""
Migración Excel → PostgreSQL — SGIND v2 Fase 8

Migra las siguientes fuentes Excel a PostgreSQL:
  1. acciones_mejora.xlsx  → tabla `acciones`
  2. OM.xlsx (Kawak)       → solo lectura / análisis (no mapea a registros_om)

Uso:
    # Solo validar (dry-run, sin BD requerida):
    python sgind-v2/database/scripts/migrate_excel_to_postgres.py --dry-run

    # Migración real:
    python sgind-v2/database/scripts/migrate_excel_to_postgres.py \\
        --postgres "postgresql://sgind:sgind_dev_password@localhost:5433/sgind"

    # Solo acciones (omitir OM Kawak):
    python ... --only acciones

Genera reporte JSON en sgind-v2/database/reports/
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("ERROR: instale pandas y openpyxl: pip install pandas openpyxl", file=sys.stderr)
    sys.exit(1)

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None  # type: ignore

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"

DEFAULT_ACCIONES_EXCEL = DATA_DIR / "raw" / "acciones_mejora.xlsx"


# ─── Lectura de fuentes ──────────────────────────────────────────────────────

def read_acciones_excel(path: Path) -> pd.DataFrame:
    """Lee acciones_mejora.xlsx y normaliza columnas."""
    df = pd.read_excel(path)
    df.columns = [c.strip() for c in df.columns]
    return df


def map_accion_row(row: dict) -> dict:
    """Convierte una fila de acciones_mejora.xlsx al esquema de la tabla `acciones`."""
    # Los campos conocidos van a columnas directas; el resto va al JSONB `payload`
    known_fields = {
        "ID", "ESTADO", "TIPO_ACCION", "PROCESOS", "AVANCE", "CREADOR",
        "RESPONSABLE_CIERRE", "FECHA_CREACION", "FECHA_ESTIMADA_CIERRE",
        "FECHA_CIERRE", "MESES_SIN_AVANCE", "DESCRIPCION",
    }
    payload = {}
    for k, v in row.items():
        if k not in known_fields and pd.notna(v) and v != "":
            try:
                payload[k] = float(v) if isinstance(v, float) else str(v)
            except (ValueError, TypeError):
                payload[k] = str(v) if v is not None else None

    return {
        "accion": _safe_str(row.get("DESCRIPCION")),
        "responsable": _safe_str(row.get("RESPONSABLE_CIERRE") or row.get("CREADOR")),
        "estado": _safe_str(row.get("ESTADO")),
        "marker_col": "ID",
        "marker_value": str(int(row["ID"])) if pd.notna(row.get("ID")) else None,
        "payload": payload,
    }


def _safe_str(v) -> str | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return str(v).strip() or None


# ─── Validación / análisis dry-run ───────────────────────────────────────────

def analyze_acciones(df: pd.DataFrame) -> dict:
    """Estadísticas sobre las acciones (usadas en dry-run y validación post-migración)."""
    estados = df["ESTADO"].value_counts().to_dict() if "ESTADO" in df.columns else {}
    tipos = df["TIPO_ACCION"].value_counts().to_dict() if "TIPO_ACCION" in df.columns else {}
    nulls = {col: int(df[col].isna().sum()) for col in df.columns}
    return {
        "total_rows": len(df),
        "estados": {str(k): int(v) for k, v in estados.items()},
        "tipos_accion": {str(k): int(v) for k, v in tipos.items()},
        "nulls_por_columna": nulls,
        "columnas": list(df.columns),
    }


def analyze_issues(df: pd.DataFrame) -> list[dict]:
    """Detecta problemas de calidad de datos."""
    issues = []

    if "ID" in df.columns and df["ID"].isna().any():
        issues.append({
            "type": "missing_id",
            "count": int(df["ID"].isna().sum()),
            "description": "Filas sin ID — serán omitidas",
            "severity": "warning",
        })

    if "ESTADO" in df.columns:
        unknown_estados = df[~df["ESTADO"].isin(["Cerrada", "Ejecución", "Ejecución", "Cancelada", "Abierta"])]["ESTADO"].dropna().unique()
        if len(unknown_estados) > 0:
            issues.append({
                "type": "unknown_estado",
                "values": [str(e) for e in unknown_estados],
                "description": "Estados no reconocidos — se migrarán como están",
                "severity": "info",
            })

    if "FECHA_ESTIMADA_CIERRE" in df.columns:
        try:
            vencidas = df[
                pd.to_datetime(df["FECHA_ESTIMADA_CIERRE"], errors="coerce") < pd.Timestamp.now()
            ]
            abiertas_vencidas = vencidas[
                df["ESTADO"].isin(["Ejecución", "Ejecución"])
            ] if "ESTADO" in df.columns else vencidas
            if len(abiertas_vencidas) > 0:
                issues.append({
                    "type": "acciones_vencidas",
                    "count": int(len(abiertas_vencidas)),
                    "description": "Acciones en ejecución con fecha estimada de cierre vencida",
                    "severity": "warning",
                })
        except Exception:
            pass

    return issues


# ─── Migración a PostgreSQL ───────────────────────────────────────────────────

def migrate_acciones_to_pg(pg_conn, df: pd.DataFrame) -> dict:
    """Inserta filas de acciones_mejora.xlsx en la tabla `acciones`."""
    cur = pg_conn.cursor()

    # Limpiar datos previos de esta fuente (marker_col='ID') para re-migración idempotente
    cur.execute("DELETE FROM acciones WHERE marker_col = 'ID'")
    deleted = cur.rowcount

    sql = """
        INSERT INTO acciones (accion, responsable, estado, marker_col, marker_value, payload)
        VALUES (%(accion)s, %(responsable)s, %(estado)s, %(marker_col)s, %(marker_value)s, %(payload)s)
    """
    inserted = 0
    skipped = 0
    for _, row in df.iterrows():
        data = map_accion_row(row.to_dict())
        if not data.get("marker_value"):
            skipped += 1
            continue
        cur.execute(sql, {**data, "payload": json.dumps(data["payload"], ensure_ascii=False, default=str)})
        inserted += 1

    pg_conn.commit()
    cur.close()
    return {"inserted": inserted, "skipped": skipped, "deleted_prev": deleted}


def validate_pg_acciones(pg_conn) -> dict:
    """Valida la integridad de los datos migrados en PostgreSQL."""
    cur = pg_conn.cursor()

    cur.execute("SELECT COUNT(*) FROM acciones")
    total = cur.fetchone()[0]

    cur.execute("SELECT estado, COUNT(*) FROM acciones GROUP BY estado ORDER BY COUNT(*) DESC")
    estados = {row[0]: row[1] for row in cur.fetchall()}

    cur.execute("SELECT COUNT(*) FROM acciones WHERE accion IS NULL OR accion = ''")
    sin_descripcion = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM acciones WHERE marker_col = 'ID'")
    from_excel = cur.fetchone()[0]

    cur.close()
    return {
        "total_acciones": total,
        "estados": estados,
        "sin_descripcion": sin_descripcion,
        "migradas_desde_excel": from_excel,
    }


# ─── Punto de entrada ────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrar Excel (acciones_mejora) a PostgreSQL — SGIND v2 Fase 8"
    )
    parser.add_argument("--acciones", type=Path, default=DEFAULT_ACCIONES_EXCEL,
                        help="Ruta a acciones_mejora.xlsx")
    parser.add_argument("--postgres", type=str, default=None,
                        help="DATABASE_URL psycopg2 (postgresql://user:pass@host:port/db)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Solo analizar sin escribir en BD")
    parser.add_argument("--only", choices=["acciones", "all"], default="all")
    args = parser.parse_args()

    if not args.acciones.exists():
        print(f"ERROR: No se encontró {args.acciones}", file=sys.stderr)
        print("  Asegúrate de estar en la raíz del proyecto.", file=sys.stderr)
        return 1

    if psycopg2 is None and not args.dry_run:
        print("ERROR: instale psycopg2-binary: pip install psycopg2-binary", file=sys.stderr)
        return 1

    if not args.postgres and not args.dry_run:
        print("ERROR: especifique --postgres o use --dry-run", file=sys.stderr)
        return 1

    report: dict = {
        "timestamp": datetime.now(UTC).isoformat(),
        "dry_run": args.dry_run,
        "fuentes": {},
        "analisis": {},
        "issues": [],
        "migrated": {},
        "validation": {},
        "status": "ok",
    }

    # ── Leer Excel ──────────────────────────────────────────────────────────
    print(f"Leyendo {args.acciones.name}...")
    df_acciones = read_acciones_excel(args.acciones)
    report["fuentes"]["acciones_excel"] = str(args.acciones)
    report["analisis"]["acciones"] = analyze_acciones(df_acciones)
    issues = analyze_issues(df_acciones)
    report["issues"] = issues

    if args.dry_run:
        report["migrated"] = {
            "acciones": {"planned": len(df_acciones), "estimated_skip": int(df_acciones["ID"].isna().sum())}
        }
        _print_dry_run_summary(report)
        _save_report(report, "dry_run")
        return 0

    # ── Migrar a PostgreSQL ─────────────────────────────────────────────────
    dsn = args.postgres.replace("postgresql+asyncpg://", "postgresql://")
    print(f"Conectando a PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(dsn)
    except Exception as e:
        print(f"ERROR: No se pudo conectar a PostgreSQL: {e}", file=sys.stderr)
        return 1

    try:
        print("Migrando acciones...")
        result = migrate_acciones_to_pg(pg_conn, df_acciones)
        report["migrated"]["acciones"] = result

        print("Validando integridad post-migración...")
        validation = validate_pg_acciones(pg_conn)
        report["validation"]["acciones"] = validation

        # Verificar paridad
        excel_total = len(df_acciones) - int(df_acciones.get("ID", pd.Series()).isna().sum())
        pg_total = validation["migradas_desde_excel"]
        if pg_total < excel_total * 0.95:
            report["status"] = "warning"
            report["issues"].append({
                "type": "paridad_baja",
                "description": f"PG tiene {pg_total} de {excel_total} acciones esperadas",
                "severity": "error",
            })

    finally:
        pg_conn.close()

    _print_migration_summary(report)
    _save_report(report, "migration")
    return 0 if report["status"] == "ok" else 2


def _print_dry_run_summary(report: dict) -> None:
    print("\n" + "=" * 60)
    print("DRY-RUN — Análisis sin escritura en BD")
    print("=" * 60)
    acc = report["analisis"].get("acciones", {})
    print(f"  Acciones a migrar: {acc.get('total_rows', 0)}")
    print(f"  Estados: {acc.get('estados', {})}")
    print(f"  Tipos: {acc.get('tipos_accion', {})}")
    issues = report.get("issues", [])
    if issues:
        print(f"\n  Problemas detectados ({len(issues)}):")
        for issue in issues:
            print(f"    [{issue['severity'].upper()}] {issue['description']}")
    else:
        print("  Sin problemas de calidad detectados.")
    print("=" * 60)


def _print_migration_summary(report: dict) -> None:
    print("\n" + "=" * 60)
    print("MIGRACIÓN COMPLETADA")
    print("=" * 60)
    mig = report.get("migrated", {}).get("acciones", {})
    val = report.get("validation", {}).get("acciones", {})
    print(f"  Insertadas: {mig.get('inserted', 0)}")
    print(f"  Omitidas:   {mig.get('skipped', 0)}")
    print(f"  Total en PG: {val.get('total_acciones', 0)}")
    print(f"  Estados en PG: {val.get('estados', {})}")
    print(f"  Estado: {report['status'].upper()}")
    print("=" * 60)


def _save_report(report: dict, prefix: str) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    out = REPORTS_DIR / f"{prefix}_excel_{ts}.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"Reporte guardado: {out}")


if __name__ == "__main__":
    raise SystemExit(main())
