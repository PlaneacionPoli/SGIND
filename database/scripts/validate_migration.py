#!/usr/bin/env python3
"""
Validación de integridad post-migración — SGIND v2 Fase 8

Compara datos en PostgreSQL vs fuentes Excel para detectar discrepancias.

Uso:
    # Validar solo contra Excel (sin PG):
    python sgind-v2/database/scripts/validate_migration.py --no-pg

    # Validar contra PG:
    python sgind-v2/database/scripts/validate_migration.py \\
        --postgres "postgresql://sgind:sgind_dev_password@localhost:5433/sgind"

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
    import numpy as np
except ImportError:
    print("ERROR: pip install pandas openpyxl numpy", file=sys.stderr)
    sys.exit(1)

try:
    import psycopg2
except ImportError:
    psycopg2 = None  # type: ignore

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"

RESULTADOS_EXCEL = DATA_DIR / "output" / "Resultados Consolidados.xlsx"
ACCIONES_EXCEL = DATA_DIR / "raw" / "acciones_mejora.xlsx"
SQLITE_DB = DATA_DIR / "db" / "registros_om.db"


# ─── Validaciones de la fuente Excel ─────────────────────────────────────────

def validate_resultados_excel() -> dict:
    """Estadísticas de Resultados Consolidados.xlsx para baseline de KPIs."""
    if not RESULTADOS_EXCEL.exists():
        return {"error": f"No encontrado: {RESULTADOS_EXCEL}"}

    df = pd.read_excel(RESULTADOS_EXCEL)
    df.columns = [str(c).strip() for c in df.columns]

    total_rows = len(df)
    anios = sorted(df["Año"].dropna().unique().tolist()) if "Año" in df.columns else []
    procesos = df["Proceso"].nunique() if "Proceso" in df.columns else 0
    indicadores = df["Id"].nunique() if "Id" in df.columns else 0

    # KPI baseline para verificar paridad
    cumplimiento_col = next((c for c in df.columns if "cumplimiento" in c.lower() and "real" not in c.lower()), None)
    kpi_baseline = {}
    if cumplimiento_col and "Año" in df.columns:
        for anio in anios[-2:]:  # Últimos 2 años
            sub = df[df["Año"] == anio][cumplimiento_col].dropna()
            if len(sub) > 0:
                kpi_baseline[str(int(anio))] = {
                    "n": int(len(sub)),
                    "promedio": round(float(sub.mean()), 2),
                    "mediana": round(float(sub.median()), 2),
                    "min": round(float(sub.min()), 2),
                    "max": round(float(sub.max()), 2),
                }

    return {
        "source": str(RESULTADOS_EXCEL),
        "total_rows": total_rows,
        "anios_disponibles": [int(a) for a in anios],
        "n_procesos": int(procesos),
        "n_indicadores_unicos": int(indicadores),
        "columnas": list(df.columns),
        "kpi_baseline": kpi_baseline,
    }


def validate_acciones_excel() -> dict:
    """Estadísticas de acciones_mejora.xlsx."""
    if not ACCIONES_EXCEL.exists():
        return {"error": f"No encontrado: {ACCIONES_EXCEL}"}

    df = pd.read_excel(ACCIONES_EXCEL)
    estados = df["ESTADO"].value_counts().to_dict() if "ESTADO" in df.columns else {}
    tipos = df["TIPO_ACCION"].value_counts().to_dict() if "TIPO_ACCION" in df.columns else {}

    return {
        "source": str(ACCIONES_EXCEL),
        "total_rows": len(df),
        "estados": {str(k): int(v) for k, v in estados.items()},
        "tipos_accion": {str(k): int(v) for k, v in tipos.items()},
        "columnas": list(df.columns),
    }


def validate_sqlite() -> dict:
    """Estadísticas del SQLite legacy."""
    import sqlite3

    if not SQLITE_DB.exists():
        return {"error": f"No encontrado: {SQLITE_DB}"}

    conn = sqlite3.connect(SQLITE_DB)
    cur = conn.cursor()
    result = {}

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall() if not r[0].startswith("sqlite_")]

    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        result[table] = {"rows": cur.fetchone()[0]}

    conn.close()
    return {"source": str(SQLITE_DB), "tables": result}


# ─── Validaciones contra PostgreSQL ──────────────────────────────────────────

def validate_pg(pg_conn) -> dict:
    """Estadísticas de las tablas en PostgreSQL."""
    cur = pg_conn.cursor()
    result = {}

    tables = ["registros_om", "acciones", "users", "roles", "audit_log"]
    for table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            result[table] = {"rows": cur.fetchone()[0]}
        except Exception as e:
            result[table] = {"error": str(e)}

    # Estado de acciones en PG
    try:
        cur.execute("SELECT estado, COUNT(*) FROM acciones GROUP BY estado ORDER BY COUNT(*) DESC")
        result["acciones"]["estados"] = {row[0]: row[1] for row in cur.fetchall()}
    except Exception:
        pass

    cur.close()
    return result


def compare_acciones(pg_conn, df_excel: pd.DataFrame) -> dict:
    """Compara acciones entre Excel y PostgreSQL."""
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM acciones WHERE marker_col = 'ID'")
    pg_count = cur.fetchone()[0]
    cur.close()

    excel_count = len(df_excel.dropna(subset=["ID"])) if "ID" in df_excel.columns else len(df_excel)
    paridad_pct = round(pg_count / excel_count * 100, 1) if excel_count > 0 else 0

    return {
        "excel_count": excel_count,
        "pg_count": pg_count,
        "paridad_pct": paridad_pct,
        "ok": paridad_pct >= 95.0,
        "mensaje": "OK" if paridad_pct >= 95.0 else f"Diferencia: {excel_count - pg_count} filas faltantes",
    }


# ─── Punto de entrada ────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Validación de integridad post-migración")
    parser.add_argument("--postgres", type=str, default=None)
    parser.add_argument("--no-pg", action="store_true", help="Solo validar fuentes Excel/SQLite")
    args = parser.parse_args()

    if not args.no_pg and not args.postgres:
        print("ERROR: use --postgres <url> o --no-pg para omitir la BD", file=sys.stderr)
        return 1

    report: dict = {
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": {},
        "comparisons": {},
        "status": "ok",
        "issues": [],
    }

    # ── Validar fuentes ─────────────────────────────────────────────────────
    print("Validando Resultados Consolidados.xlsx...")
    report["checks"]["resultados_excel"] = validate_resultados_excel()

    print("Validando acciones_mejora.xlsx...")
    report["checks"]["acciones_excel"] = validate_acciones_excel()

    print("Validando SQLite...")
    report["checks"]["sqlite"] = validate_sqlite()

    if not args.no_pg:
        if psycopg2 is None:
            print("ERROR: pip install psycopg2-binary", file=sys.stderr)
            return 1

        dsn = args.postgres.replace("postgresql+asyncpg://", "postgresql://")
        print("Conectando a PostgreSQL...")
        try:
            pg_conn = psycopg2.connect(dsn)
        except Exception as e:
            print(f"ERROR PostgreSQL: {e}", file=sys.stderr)
            return 1

        try:
            print("Validando tablas PostgreSQL...")
            report["checks"]["postgres"] = validate_pg(pg_conn)

            print("Comparando acciones Excel vs PostgreSQL...")
            df_acc = pd.read_excel(ACCIONES_EXCEL) if ACCIONES_EXCEL.exists() else pd.DataFrame()
            report["comparisons"]["acciones"] = compare_acciones(pg_conn, df_acc)

            if not report["comparisons"]["acciones"]["ok"]:
                report["status"] = "warning"
                report["issues"].append({
                    "type": "paridad_baja",
                    "description": report["comparisons"]["acciones"]["mensaje"],
                    "severity": "warning",
                })
        finally:
            pg_conn.close()

    _print_summary(report)
    _save_report(report)
    return 0 if report["status"] == "ok" else 2


def _print_summary(report: dict) -> None:
    print("\n" + "=" * 60)
    print("REPORTE DE VALIDACIÓN — SGIND v2 Fase 8")
    print("=" * 60)

    res = report["checks"].get("resultados_excel", {})
    if "error" not in res:
        print(f"\n[KPI] Resultados Consolidados.xlsx")
        print(f"   Filas:         {res.get('total_rows', '?')}")
        print(f"   Indicadores:   {res.get('n_indicadores_unicos', '?')}")
        print(f"   Procesos:      {res.get('n_procesos', '?')}")
        print(f"   Años:          {res.get('anios_disponibles', [])}")

    acc = report["checks"].get("acciones_excel", {})
    if "error" not in acc:
        print(f"\n[ACC] acciones_mejora.xlsx")
        print(f"   Total:   {acc.get('total_rows', '?')}")
        print(f"   Estados: {acc.get('estados', {})}")

    sqlite = report["checks"].get("sqlite", {})
    if "error" not in sqlite:
        tables = sqlite.get("tables", {})
        print(f"\n[DB] SQLite legacy")
        for t, info in tables.items():
            print(f"   {t}: {info.get('rows', '?')} filas")

    pg = report["checks"].get("postgres", {})
    if pg:
        print(f"\n[PG] PostgreSQL")
        for t, info in pg.items():
            if isinstance(info, dict) and "rows" in info:
                print(f"   {t}: {info['rows']} filas")

    comp = report["comparisons"].get("acciones", {})
    if comp:
        icon = "[OK]" if comp.get("ok") else "[WARN]"
        print(f"\n{icon} Paridad acciones: {comp.get('paridad_pct', 0)}%  ({comp.get('pg_count', 0)}/{comp.get('excel_count', 0)})")

    issues = report.get("issues", [])
    if issues:
        print(f"\nIssues ({len(issues)}):")
        for issue in issues:
            print(f"   [{issue['severity'].upper()}] {issue['description']}")
    else:
        print("\nSin issues detectados")

    print(f"\nEstado general: {report['status'].upper()}")
    print("=" * 60)


def _save_report(report: dict) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    out = REPORTS_DIR / f"validation_{ts}.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"Reporte guardado: {out}")


if __name__ == "__main__":
    raise SystemExit(main())
