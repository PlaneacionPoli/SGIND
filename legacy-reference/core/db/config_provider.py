"""
core/db/config_provider.py — Gestión de configuración y secretos.

Responsabilidad única: Proveer credenciales y URLs de base de datos desde:
  1. Streamlit secrets (Cloud)
  2. Variables de entorno (.env)
  3. Defaults (SQLite local)

Sin lógica de conexión o CRUD.
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

logger = logging.getLogger(__name__)

# Rutas estándar
DB_PATH = Path(__file__).parent.parent.parent / "data" / "db" / "registros_om.db"


def safe_streamlit_secrets_get(key: str, default: str = "") -> str:
    """Lee un secret de Streamlit si está disponible, sin romper en ejecución no-Streamlit.
    
    Args:
        key: Nombre del secret
        default: Valor default si no existe o Streamlit no está disponible
        
    Returns:
        String del secret, o default si no disponible
    """
    try:
        import streamlit as st
        return str(st.secrets.get(key, default)).strip()
    except Exception:
        return default


def get_database_url() -> str:
    """Lee DATABASE_URL desde st.secrets o variable de entorno.
    
    Prioridad:
      1. Streamlit secrets
      2. Variable de entorno DATABASE_URL
      3. String vacío (fallback a SQLite)
      
    Returns:
        DATABASE_URL sanitizada, o string vacío
    """
    db_url = safe_streamlit_secrets_get("DATABASE_URL")
    if db_url:
        return sanitize_postgres_dsn(db_url)
    return sanitize_postgres_dsn(os.getenv("DATABASE_URL", "").strip())


def sanitize_postgres_dsn(dsn: str) -> str:
    """Elimina parámetros de query no soportados por psycopg2 en URIs PostgreSQL.
    
    Args:
        dsn: PostgreSQL connection string (postgresql://...)
        
    Returns:
        DSN limpio con parámetros soportados
    """
    raw = str(dsn or "").strip()
    if not raw or not raw.startswith("postgresql://"):
        return raw

    parsed = urlparse(raw)
    unsupported = {"pgbouncer"}
    cleaned_qs = [
        (k, v)
        for (k, v) in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in unsupported
    ]
    new_query = urlencode(cleaned_qs, doseq=True)
    return urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
    )


def extract_supabase_project_ref(supabase_url: str) -> str:
    """Extrae el project_ref desde https://<project_ref>.supabase.co.
    
    Args:
        supabase_url: URL de Supabase (ej: https://abcdef.supabase.co)
        
    Returns:
        Project reference (ej: abcdef)
    """
    if not supabase_url:
        return ""
    raw = str(supabase_url).strip().replace("https://", "").replace("http://", "")
    return raw.split(".")[0] if raw else ""


def get_postgres_connect_kwargs() -> Optional[Dict[str, Any]]:
    """Construye kwargs de conexión a Postgres para Supabase.

    Prioridad:
      1) DATABASE_URL → retorna {"dsn": url}
      2) SUPABASE_POOLER_URL → retorna {"dsn": url}
      3) SUPABASE_URL + SUPABASE_DB_PASSWORD + SUPABASE_DB_* → construye kwargs
      4) None si no hay credenciales disponibles

    Returns:
        Dict con {"dsn": ...} o {"host": ..., "port": ..., "dbname": ..., ...}
        o None si no hay configuración PostgreSQL
    """
    # Opción 1: DATABASE_URL (más específico, prioritario)
    db_url = get_database_url()
    if db_url:
        return {"dsn": db_url}

    # Opción 2: SUPABASE_POOLER_URL
    pooler_url = (
        safe_streamlit_secrets_get("SUPABASE_POOLER_URL") 
        or os.getenv("SUPABASE_POOLER_URL", "").strip()
    )
    if pooler_url:
        return {"dsn": sanitize_postgres_dsn(pooler_url)}

    # Opción 3: SUPABASE_URL + componentes individuales
    supabase_url = (
        safe_streamlit_secrets_get("SUPABASE_URL") 
        or os.getenv("SUPABASE_URL", "").strip()
    )
    supabase_db_password = (
        safe_streamlit_secrets_get("SUPABASE_DB_PASSWORD")
        or os.getenv("SUPABASE_DB_PASSWORD", "").strip()
    )

    if not (supabase_url and supabase_db_password):
        return None

    # Leer componentes opcionales con defaults
    supabase_db_host = (
        safe_streamlit_secrets_get("SUPABASE_DB_HOST") 
        or os.getenv("SUPABASE_DB_HOST", "").strip()
    )
    supabase_db_port = (
        safe_streamlit_secrets_get("SUPABASE_DB_PORT") 
        or os.getenv("SUPABASE_DB_PORT", "").strip()
    )
    supabase_db_user = (
        safe_streamlit_secrets_get("SUPABASE_DB_USER") 
        or os.getenv("SUPABASE_DB_USER", "").strip()
    )
    supabase_db_name = (
        safe_streamlit_secrets_get("SUPABASE_DB_NAME") 
        or os.getenv("SUPABASE_DB_NAME", "").strip()
    )

    # Construir kwargs con valores default de Supabase
    project_ref = extract_supabase_project_ref(supabase_url)
    host = supabase_db_host or f"db.{project_ref}.supabase.co"
    port = int(supabase_db_port) if supabase_db_port.isdigit() else 5432
    user = supabase_db_user or "postgres"
    dbname = supabase_db_name or "postgres"

    return {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": supabase_db_password,
        "sslmode": "require",
    }


def use_postgres() -> bool:
    """Determina si usar PostgreSQL o SQLite basado en credenciales disponibles.
    
    Returns:
        True si hay credenciales PostgreSQL disponibles, False para SQLite
    """
    return get_postgres_connect_kwargs() is not None


def get_sqlite_path() -> Path:
    """Retorna la ruta del archivo SQLite.
    
    Returns:
        Path a registros_om.db
    """
    return DB_PATH
