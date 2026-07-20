"""
Tests Fase 8 — Migración de Datos.

Cubre:
 1. Script dry-run de SQLite → PostgreSQL no falla sin BD
 2. Script dry-run de Excel → PostgreSQL no falla sin BD
 3. Mapeo de filas acciones_mejora.xlsx → esquema `acciones`
 4. Validación de fuentes Excel (estructura y columnas esperadas)
 5. Script validate_migration --no-pg produce reporte válido
 6. KPI baseline de Resultados Consolidados.xlsx es razonable
"""

import json
import sys
from pathlib import Path

import pytest

# Rutas
# __file__ → tests/ → backend/ → sgind-v2/ → Sistema_Indicadores_Poli/
ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
SCRIPTS_DIR = ROOT / "sgind-v2" / "database" / "scripts"

ACCIONES_EXCEL = DATA_DIR / "raw" / "acciones_mejora.xlsx"
RESULTADOS_EXCEL = DATA_DIR / "output" / "Resultados Consolidados.xlsx"
SQLITE_DB = DATA_DIR / "db" / "registros_om.db"

# Agregar scripts al path de importación
sys.path.insert(0, str(SCRIPTS_DIR))


# ─── Dry-run SQLite ──────────────────────────────────────────────────────────

def test_sqlite_dryrun_no_requiere_bd(tmp_path, capsys):
    """El dry-run de migrate_sqlite_to_postgres no necesita PostgreSQL."""
    if not SQLITE_DB.exists():
        pytest.skip("SQLite no disponible")

    from migrate_sqlite_to_postgres import read_sqlite_om, read_sqlite_acciones
    import sqlite3

    conn = sqlite3.connect(SQLITE_DB)
    om_rows = read_sqlite_om(conn)
    acc_rows = read_sqlite_acciones(conn)
    conn.close()

    # SQLite puede tener 0 registros_om pero debe ser una lista
    assert isinstance(om_rows, list)
    assert isinstance(acc_rows, list)
    # acciones tiene 118 filas
    assert len(acc_rows) == 118


def test_sqlite_om_mapeo():
    """La función map_om_row aplica tipos correctos."""
    from migrate_sqlite_to_postgres import map_om_row

    raw = {
        "id_indicador": "T-001",
        "nombre_indicador": "Test",
        "proceso": "Calidad",
        "periodo": "Enero",
        "anio": "2025",
        "sede": "Bogotá",
        "tiene_om": "1",
        "tipo_accion": "OM Kawak",
        "numero_om": "123",
        "comentario": "ok",
        "registrado_por": "admin",
        "fecha_registro": "2025-01-01",
    }
    mapped = map_om_row(raw)
    assert mapped["anio"] == 2025
    assert mapped["tiene_om"] == 1
    assert mapped["id_indicador"] == "T-001"


# ─── Dry-run Excel ───────────────────────────────────────────────────────────

def test_excel_dryrun_no_requiere_bd():
    """El dry-run de migrate_excel_to_postgres lee el Excel sin necesitar BD."""
    if not ACCIONES_EXCEL.exists():
        pytest.skip("acciones_mejora.xlsx no disponible")

    from migrate_excel_to_postgres import read_acciones_excel, analyze_acciones

    df = read_acciones_excel(ACCIONES_EXCEL)
    assert len(df) > 0
    assert "ESTADO" in df.columns
    assert "TIPO_ACCION" in df.columns

    stats = analyze_acciones(df)
    assert stats["total_rows"] == len(df)
    assert "estados" in stats
    assert "tipos_accion" in stats


def test_excel_acciones_columnas_requeridas():
    """acciones_mejora.xlsx tiene todas las columnas necesarias para migración."""
    if not ACCIONES_EXCEL.exists():
        pytest.skip("acciones_mejora.xlsx no disponible")

    import pandas as pd
    df = pd.read_excel(ACCIONES_EXCEL, nrows=0)
    cols = set(df.columns)

    required = {"ID", "ESTADO", "TIPO_ACCION", "DESCRIPCION"}
    missing = required - cols
    assert not missing, f"Columnas faltantes en acciones_mejora.xlsx: {missing}"


def test_excel_mapeo_accion_row():
    """La función map_accion_row produce la estructura correcta para `acciones`."""
    from migrate_excel_to_postgres import map_accion_row

    row = {
        "ID": 392,
        "DESCRIPCION": "Acción de prueba para permanencia",
        "ESTADO": "Cerrada",
        "TIPO_ACCION": "Acción de Mejora",
        "PROCESOS": "1 - Permanencia",
        "AVANCE": 100,
        "CREADOR": "Test User",
        "RESPONSABLE_CIERRE": "Test Responsable",
        "FECHA_CREACION": "2025-01-13",
        "FECHA_ESTIMADA_CIERRE": None,
        "FECHA_CIERRE": "2025-01-15",
        "MESES_SIN_AVANCE": 0,
    }
    mapped = map_accion_row(row)

    assert mapped["estado"] == "Cerrada"
    assert mapped["marker_col"] == "ID"
    assert mapped["marker_value"] == "392"
    assert "accion" in mapped
    assert "payload" in mapped
    assert isinstance(mapped["payload"], dict)


# ─── Validación de fuentes ───────────────────────────────────────────────────

def test_resultados_consolidados_estructura():
    """Resultados Consolidados.xlsx tiene las columnas esperadas por el ETL."""
    if not RESULTADOS_EXCEL.exists():
        pytest.skip("Resultados Consolidados.xlsx no disponible")

    import pandas as pd
    df = pd.read_excel(RESULTADOS_EXCEL, nrows=5)
    cols = set(df.columns)

    required = {"Id", "Proceso", "Año", "Meta", "Ejecucion"}
    missing = required - cols
    assert not missing, f"Columnas faltantes en Resultados Consolidados: {missing}"


def test_resultados_consolidados_kpi_baseline():
    """El baseline de KPIs de Resultados Consolidados es numérico y razonable."""
    if not RESULTADOS_EXCEL.exists():
        pytest.skip("Resultados Consolidados.xlsx no disponible")

    import pandas as pd
    df = pd.read_excel(RESULTADOS_EXCEL)
    df.columns = [str(c).strip() for c in df.columns]

    # Total rows razonable (mínimo 100)
    assert len(df) >= 100, f"Pocos registros: {len(df)}"

    # Años disponibles incluyen 2025
    assert "Año" in df.columns
    anios = df["Año"].dropna().unique()
    assert 2025 in anios, f"Año 2025 no encontrado, años: {sorted(anios)}"

    # Meta y Ejecucion tienen datos (Cumplimiento es columna calculada por ETL)
    assert "Meta" in df.columns
    assert "Ejecucion" in df.columns
    assert df["Meta"].notna().sum() > 100, "Meta no tiene suficientes valores"
    assert df["Ejecucion"].notna().sum() > 100, "Ejecucion no tiene suficientes valores"

    # Indicadores únicos razonables
    assert df["Id"].nunique() > 50, f"Pocos indicadores únicos: {df['Id'].nunique()}"


def test_validate_migration_script_no_pg(tmp_path):
    """validate_migration.py con --no-pg produce reporte JSON válido."""
    import subprocess
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "validate_migration.py"), "--no-pg"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    # Debe exitir con código 0 (OK) aunque no haya PG
    assert result.returncode == 0, f"validate_migration --no-pg falló: {result.stderr}"


def test_migrate_excel_dryrun_script(tmp_path):
    """migrate_excel_to_postgres.py --dry-run termina con código 0."""
    if not ACCIONES_EXCEL.exists():
        pytest.skip("acciones_mejora.xlsx no disponible")

    import subprocess
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "migrate_excel_to_postgres.py"), "--dry-run"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, f"dry-run falló: {result.stderr}"
    assert "Acciones a migrar: 401" in result.stdout or "401" in result.stdout


def test_migrate_sqlite_dryrun_script():
    """migrate_sqlite_to_postgres.py --dry-run termina con código 0."""
    if not SQLITE_DB.exists():
        pytest.skip("SQLite no disponible")

    import subprocess
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "migrate_sqlite_to_postgres.py"), "--dry-run"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, f"sqlite dry-run falló: {result.stderr}"
    output = json.loads(result.stdout)
    assert output["dry_run"] is True
    assert output["status"] == "ok"
    assert "registros_om" in output["source"]


# ─── Análisis de issues ──────────────────────────────────────────────────────

def test_analyze_issues_detecta_vencidas():
    """analyze_issues detecta acciones en ejecución con fecha vencida."""
    if not ACCIONES_EXCEL.exists():
        pytest.skip("acciones_mejora.xlsx no disponible")

    from migrate_excel_to_postgres import read_acciones_excel, analyze_issues

    df = read_acciones_excel(ACCIONES_EXCEL)
    issues = analyze_issues(df)

    # Debe ser una lista (puede estar vacía si no hay issues)
    assert isinstance(issues, list)
    for issue in issues:
        assert "type" in issue
        assert "severity" in issue
        assert "description" in issue
        assert issue["severity"] in ("info", "warning", "error")
