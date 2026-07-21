"""
core/db_manager.py — Persistencia dual SQLite (local) / PostgreSQL (Supabase).

DEPRECATED: Functions moved to core/db/ subpackage.

Prioridad de detección de DATABASE_URL:
  1. st.secrets["DATABASE_URL"]  → Streamlit Cloud
  2. Variable de entorno DATABASE_URL → .env local / Render
  3. Sin URL → SQLite local en data/db/registros_om.db
"""

import os
import re
import sqlite3
import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Import from refactored modules
from core.db.config_provider import (
    safe_streamlit_secrets_get,
    get_database_url,
    sanitize_postgres_dsn,
    extract_supabase_project_ref,
    get_postgres_connect_kwargs,
)

from core.db.data_normalizer import (
    numero_mes_a_nombre,
    normalizar_nombre_mes,
    normalizar_periodo_anio,
)

from core.db.connection_manager import (
    _connect_postgres,
    _build_ipv4_retry_connect_kwargs,
    _use_pg,
    _notify_streamlit,
    _init_sqlite,
    _init_postgres,
    inicializar_db,
)

from core.db.schema_manager import (
    _ensure_sqlite_unique_index,
    _ensure_postgres_unique_constraint,
)

from core.db.operations import (
    guardar_registro_om,
    leer_registros_om,
    registros_om_como_dict,
    guardar_acciones_bulk,
    leer_acciones,
    borrar_acciones_por_marker,
)

# Create backward-compatible aliases for private functions
# These allow existing code in this file to use _-prefixed names
_safe_st_secrets_get = safe_streamlit_secrets_get
_get_database_url = get_database_url
_sanitize_postgres_dsn = sanitize_postgres_dsn
_extract_supabase_project_ref = extract_supabase_project_ref
_get_postgres_connect_kwargs = get_postgres_connect_kwargs
_mes_numero_a_nombre = numero_mes_a_nombre
_normalize_mes_nombre = normalizar_nombre_mes
_normalize_om_periodo_anio = normalizar_periodo_anio

# Legacy path constant for backward compatibility
DB_PATH = Path(__file__).parent.parent / "data" / "db" / "registros_om.db"

# Override _init_sqlite from connection_manager to use db_manager.DB_PATH
# This allows tests to monkeypatch DB_PATH and have it propagate correctly
_original_init_sqlite = _init_sqlite


def _init_sqlite():
    """Wrapper that passes db_manager.DB_PATH to connection_manager._init_sqlite"""
    return _original_init_sqlite(db_path=DB_PATH)


# Preserve backward compatibility: import operations but wrap to use db_manager.DB_PATH
# This allows tests to monkeypatch DB_PATH and have it propagate
_original_guardar_registro_om = guardar_registro_om
_original_leer_registros_om = leer_registros_om
_original_registros_om_como_dict = registros_om_como_dict
_original_guardar_acciones_bulk = guardar_acciones_bulk
_original_leer_acciones = leer_acciones
_original_borrar_acciones_por_marker = borrar_acciones_por_marker


def guardar_registro_om(datos: dict) -> bool:
    """Wrapper that ensures DB_PATH is set from db_manager"""
    import core.db.operations as ops
    original_db_path = ops.DB_PATH
    try:
        ops.DB_PATH = DB_PATH
        return _original_guardar_registro_om(datos)
    finally:
        ops.DB_PATH = original_db_path


def leer_registros_om(anio: int = None, periodo: str = None):
    """Wrapper that ensures DB_PATH is set from db_manager"""
    import core.db.operations as ops
    original_db_path = ops.DB_PATH
    try:
        ops.DB_PATH = DB_PATH
        return _original_leer_registros_om(anio=anio, periodo=periodo)
    finally:
        ops.DB_PATH = original_db_path


def registros_om_como_dict(anio: int = None, periodo: str = None) -> dict:
    """Wrapper that ensures DB_PATH is set from db_manager"""
    import core.db.operations as ops
    original_db_path = ops.DB_PATH
    try:
        ops.DB_PATH = DB_PATH
        return _original_registros_om_como_dict(anio=anio, periodo=periodo)
    finally:
        ops.DB_PATH = original_db_path


def guardar_acciones_bulk(df) -> bool:
    """Wrapper that ensures DB_PATH is set from db_manager"""
    import core.db.operations as ops
    original_db_path = ops.DB_PATH
    try:
        ops.DB_PATH = DB_PATH
        return _original_guardar_acciones_bulk(df)
    finally:
        ops.DB_PATH = original_db_path


def leer_acciones(limit: int = 1000) -> list:
    """Wrapper that ensures DB_PATH is set from db_manager"""
    import core.db.operations as ops
    original_db_path = ops.DB_PATH
    try:
        ops.DB_PATH = DB_PATH
        return _original_leer_acciones(limit=limit)
    finally:
        ops.DB_PATH = original_db_path


def borrar_acciones_por_marker(col: str, value: str) -> bool:
    """Wrapper that ensures DB_PATH is set from db_manager"""
    import core.db.operations as ops
    original_db_path = ops.DB_PATH
    try:
        ops.DB_PATH = DB_PATH
        return _original_borrar_acciones_por_marker(col=col, value=value)
    finally:
        ops.DB_PATH = original_db_path
