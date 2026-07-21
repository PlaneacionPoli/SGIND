"""
core/db/operations.py — CRUD operations on registros_om and acciones tables.

Responsibility: Data persistence layer - save, read, delete operations.

This module handles:
  - registros_om CRUD: guardar (upsert), leer, registros_como_dict
  - acciones table: bulk save, read, delete by marker
  - SQLite and PostgreSQL backend abstraction
"""

import sqlite3
import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from .config_provider import DB_PATH
from .data_normalizer import normalizar_periodo_anio as _normalize_om_periodo_anio
from .connection_manager import (
    _connect_postgres,
    _use_pg,
    _notify_streamlit,
    inicializar_db,
)


# ── Registros OM: Save (Upsert) ────────────────────────────────────────────────


def guardar_registro_om(datos: dict) -> bool:
    """
    Upsert operation on registros_om table.

    Inserts or updates a single indicator record. Normalizes periodo/anio before insert.

    Args:
        datos: Dict with keys:
            - id_indicador: Indicator ID
            - nombre_indicador: Indicator name
            - proceso: Process name
            - periodo: Month name or number (e.g., "Enero", "1", "2026-01")
            - anio: Year
            - tiene_om: 0 or 1
            - tipo_accion: Action type (default: "OM Kawak")
            - numero_om: OM reference number
            - comentario: Comments

    Returns:
        True if successful, False on error
    """
    inicializar_db()

    periodo, anio = _normalize_om_periodo_anio(datos.get("periodo", ""), datos.get("anio", 0))
    datos = {
        "id_indicador": str(datos.get("id_indicador", "")),
        "nombre_indicador": str(datos.get("nombre_indicador", "")),
        "proceso": str(datos.get("proceso", "")),
        "periodo": str(periodo),
        "anio": int(anio),
        "tiene_om": int(datos.get("tiene_om", 0)),
        "tipo_accion": str(datos.get("tipo_accion", "OM Kawak")),
        "numero_om": str(datos.get("numero_om", "")),
        "comentario": str(datos.get("comentario", "")),
        "registrado_por": "",
        "fecha_registro": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        if _use_pg():
            return _upsert_postgres(datos)
        else:
            return _upsert_sqlite(datos)
    except Exception as e:
        _notify_streamlit("error", f"Error al guardar: {e}")
        return False


def _upsert_sqlite(d: dict) -> bool:
    """SQLite upsert using ON CONFLICT clause."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO registros_om
            (id_indicador, nombre_indicador, proceso, periodo, anio,
             tiene_om, tipo_accion, numero_om, comentario, registrado_por, fecha_registro)
        VALUES
            (:id_indicador, :nombre_indicador, :proceso, :periodo, :anio,
             :tiene_om, :tipo_accion, :numero_om, :comentario, :registrado_por, :fecha_registro)
        ON CONFLICT(id_indicador, periodo, anio) DO UPDATE SET
            nombre_indicador = excluded.nombre_indicador,
            proceso          = excluded.proceso,
            tiene_om         = excluded.tiene_om,
            tipo_accion      = excluded.tipo_accion,
            numero_om        = excluded.numero_om,
            comentario       = excluded.comentario,
            fecha_registro   = excluded.fecha_registro
    """,
        d,
    )
    conn.commit()
    conn.close()
    return True


def _upsert_postgres(d: dict) -> bool:
    """PostgreSQL upsert using ON CONFLICT ON CONSTRAINT clause."""
    conn = _connect_postgres()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO registros_om
            (id_indicador, nombre_indicador, proceso, periodo, anio,
             tiene_om, tipo_accion, numero_om, comentario, registrado_por, fecha_registro)
        VALUES
            (%(id_indicador)s, %(nombre_indicador)s, %(proceso)s, %(periodo)s,
             %(anio)s, %(tiene_om)s, %(tipo_accion)s, %(numero_om)s, %(comentario)s,
             %(registrado_por)s, %(fecha_registro)s)
        ON CONFLICT ON CONSTRAINT registros_om_unique_key DO UPDATE SET
            nombre_indicador = EXCLUDED.nombre_indicador,
            proceso          = EXCLUDED.proceso,
            tiene_om         = EXCLUDED.tiene_om,
            tipo_accion      = EXCLUDED.tipo_accion,
            numero_om        = EXCLUDED.numero_om,
            comentario       = EXCLUDED.comentario,
            fecha_registro   = EXCLUDED.fecha_registro
    """,
        d,
    )
    conn.commit()
    cur.close()
    conn.close()
    return True


# ── Registros OM: Read ─────────────────────────────────────────────────────────


def leer_registros_om(anio: int = None, periodo: str = None) -> List[Dict[str, Any]]:
    """
    Read registros_om records with optional filtering.

    Args:
        anio: Optional year filter
        periodo: Optional month filter

    Returns:
        List of dict records, ordered by fecha_registro DESC
    """
    try:
        if _use_pg():
            return _leer_postgres(anio, periodo)
        else:
            return _leer_sqlite(anio, periodo)
    except Exception as e:
        _notify_streamlit("error", f"Error al leer registros: {e}")
        return []


def _leer_sqlite(anio: Optional[int], periodo: Optional[str]) -> List[Dict[str, Any]]:
    """SQLite read implementation."""
    if not DB_PATH.exists():
        return []
    periodo_norm = ""
    if periodo:
        periodo_norm, _ = _normalize_om_periodo_anio(periodo, anio or 0)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if anio and periodo_norm:
        rows = conn.execute(
            "SELECT * FROM registros_om WHERE anio = ? AND periodo = ? ORDER BY fecha_registro DESC",
            (anio, periodo_norm),
        ).fetchall()
    elif anio:
        rows = conn.execute(
            "SELECT * FROM registros_om WHERE anio = ? ORDER BY fecha_registro DESC",
            (anio,),
        ).fetchall()
    elif periodo_norm:
        rows = conn.execute(
            "SELECT * FROM registros_om WHERE periodo = ? ORDER BY fecha_registro DESC",
            (periodo_norm,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM registros_om ORDER BY fecha_registro DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _leer_postgres(anio: Optional[int], periodo: Optional[str]) -> List[Dict[str, Any]]:
    """PostgreSQL read implementation."""
    import psycopg2.extras

    conn = _connect_postgres()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    periodo_norm = ""
    if periodo:
        periodo_norm, _ = _normalize_om_periodo_anio(periodo, anio or 0)

    if anio and periodo_norm:
        cur.execute(
            "SELECT * FROM registros_om WHERE anio = %(anio)s AND periodo = %(periodo)s ORDER BY fecha_registro DESC",
            {"anio": anio, "periodo": periodo_norm},
        )
    elif anio:
        cur.execute(
            "SELECT * FROM registros_om WHERE anio = %(anio)s ORDER BY fecha_registro DESC",
            {"anio": anio},
        )
    elif periodo_norm:
        cur.execute(
            "SELECT * FROM registros_om WHERE periodo = %(periodo)s ORDER BY fecha_registro DESC",
            {"periodo": periodo_norm},
        )
    else:
        cur.execute("SELECT * FROM registros_om ORDER BY fecha_registro DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def registros_om_como_dict(anio: int = None, periodo: str = None) -> Dict[str, Dict[str, Any]]:
    """
    Convert registros_om records to dictionary indexed by id_indicador.

    Returns:
        Dict mapping id_indicador → {tiene_om, tipo_accion, numero_om, periodo, comentario, anio}

    Note:
        If an indicator has multiple records (different periods), returns most recent.
    """
    registros = leer_registros_om(anio=anio, periodo=periodo)
    result = {}
    for r in registros:
        iid = r["id_indicador"]
        if iid not in result:  # leer_registros_om ordena DESC → primer registro = más reciente
            result[iid] = {
                "tiene_om": bool(r.get("tiene_om", 0)),
                "tipo_accion": r.get("tipo_accion", "OM Kawak"),
                "numero_om": r.get("numero_om", ""),
                "periodo": r.get("periodo", ""),
                "comentario": r.get("comentario", ""),
                "anio": r.get("anio", ""),
            }
    return result


# ── Acciones: Bulk Operations ──────────────────────────────────────────────────


def guardar_acciones_bulk(df) -> bool:
    """
    Bulk insert actions from DataFrame or list of dicts.

    Creates acciones table with TEXT columns matching DataFrame columns.
    Tolerant of various input formats - attempts conversion if needed.

    Args:
        df: pandas DataFrame or list of dicts

    Returns:
        True if successful, False on error
    """
    if df is None:
        return False
    try:
        import pandas as pd
    except Exception:
        pd = None

    # Normalize to DataFrame
    if pd is not None and not isinstance(df, pd.DataFrame):
        try:
            df = pd.DataFrame(df)
        except Exception:
            return False

    # Return if no rows
    if (hasattr(df, "empty") and df.empty) or (not hasattr(df, "shape") and len(df) == 0):
        return False

    cols = list(df.columns)
    try:
        if _use_pg():
            conn = _connect_postgres()
            cur = conn.cursor()
            # Create table with TEXT columns
            cols_defs = ", ".join([f'"{c}" TEXT' for c in cols])
            cur.execute(f"CREATE TABLE IF NOT EXISTS acciones (id SERIAL PRIMARY KEY, {cols_defs})")
            # Insert rows
            for _, row in df.iterrows():
                vals = [None if (pd is not None and pd.isna(x)) else str(x) for x in row.tolist()]
                placeholders = ",".join(["%s"] * len(vals))
                cur.execute(
                    f'INSERT INTO acciones ({", ".join([f"\"{c}\"" for c in cols])}) VALUES ({placeholders})',
                    tuple(vals),
                )
            conn.commit()
            cur.close()
            conn.close()
            return True
        else:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cols_defs = ", ".join([f'"{c}" TEXT' for c in cols])
            cur.execute(
                f"CREATE TABLE IF NOT EXISTS acciones (id INTEGER PRIMARY KEY AUTOINCREMENT, {cols_defs})"
            )
            insert_sql = f'INSERT INTO acciones ({", ".join([f"\"{c}\"" for c in cols])}) VALUES ({", ".join(["?" for _ in cols])})'
            for _, row in df.iterrows():
                vals = [None if (pd is not None and pd.isna(x)) else str(x) for x in row.tolist()]
                cur.execute(insert_sql, vals)
            conn.commit()
            conn.close()
            return True
    except Exception as e:
        _notify_streamlit("error", f"Error guardar_acciones_bulk: {e}")
        return False


def leer_acciones(limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Read acciones table records up to limit.

    Args:
        limit: Maximum rows to return

    Returns:
        List of dict records, ordered by id DESC
    """
    try:
        if _use_pg():
            import psycopg2
            import psycopg2.extras

            conn = _connect_postgres()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(f"SELECT * FROM acciones ORDER BY id DESC LIMIT {int(limit)}")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return [dict(r) for r in rows]
        else:
            if not DB_PATH.exists():
                return []
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM acciones ORDER BY id DESC LIMIT {int(limit)}")
            rows = cur.fetchall()
            conn.close()
            return [dict(r) for r in rows]
    except Exception as e:
        _notify_streamlit("error", f"Error leer_acciones: {e}")
        return []


def borrar_acciones_por_marker(col: str, value: str) -> bool:
    """
    Delete acciones records where specified column equals value.

    Args:
        col: Column name to filter by
        value: Column value to match for deletion

    Returns:
        True if successful (or table doesn't exist), False on error
    """
    try:
        if _use_pg():
            conn = _connect_postgres()
            cur = conn.cursor()
            cur.execute(f'DELETE FROM acciones WHERE "{col}" = %s', (str(value),))
            conn.commit()
            cur.close()
            conn.close()
            return True
        else:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute(f'DELETE FROM acciones WHERE "{col}" = ?', (str(value),))
            conn.commit()
            conn.close()
            return True
    except Exception as e:
        _notify_streamlit("error", f"Error borrar_acciones_por_marker: {e}")
        return False
