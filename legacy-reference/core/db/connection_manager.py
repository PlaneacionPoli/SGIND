"""
core/db/connection_manager.py — Database connection establishment and initialization.

Responsibility: SQLite/Postgres connection management, initialization, and retry logic.

This module handles:
  - PostgreSQL connection with retry logic for IPv6/IPv4 fallback
  - SQLite connection and initialization
  - Database schema initialization (table creation)
  - Streamlit UI notifications for connection errors
"""

import os
import socket
import sqlite3
import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .config_provider import (
    safe_streamlit_secrets_get,
    get_postgres_connect_kwargs,
    sanitize_postgres_dsn,
    DB_PATH,
)


def _connect_postgres():
    """
    Establishes PostgreSQL connection with retry fallback for IPv6-incompatible networks.

    Connection priority:
      1. Direct connection with configured kwargs
      2. Fallback to SUPABASE_POOLER_URL if direct connection fails with IPv6 errors
      3. Retry with IPv4-forced hostaddr if available

    Raises:
        ValueError: If no PostgreSQL credentials are configured
        psycopg2.Error: If connection fails after all retries
    """
    import psycopg2

    kwargs = get_postgres_connect_kwargs()
    if not kwargs:
        raise ValueError(
            "No hay credenciales de PostgreSQL configuradas. Usa DATABASE_URL o SUPABASE_URL + SUPABASE_DB_PASSWORD."
        )
    try:
        return psycopg2.connect(**kwargs)
    except Exception as exc:
        msg = str(exc)
        # IPv6-incompatible networks fail with "Cannot assign requested address" or "Network is unreachable"
        if "Cannot assign requested address" in msg or "Network is unreachable" in msg:
            # Attempt fallback to SUPABASE_POOLER_URL if configured
            pooler_url = (
                safe_streamlit_secrets_get("SUPABASE_POOLER_URL")
                or os.getenv("SUPABASE_POOLER_URL", "").strip()
            )
            if pooler_url:
                try:
                    return psycopg2.connect(dsn=pooler_url)
                except Exception:
                    pass
            # Attempt retry with IPv4-forced hostaddr
            retry_kwargs = _build_ipv4_retry_connect_kwargs(kwargs)
            if retry_kwargs:
                return psycopg2.connect(**retry_kwargs)
        raise


def _build_ipv4_retry_connect_kwargs(kwargs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Creates retry kwargs forcing IPv4 hostaddr when initial connection fails.

    Strategy:
      1. Extract hostname from kwargs or DSN URL
      2. Resolve hostname to IPv4 address only (AF_INET)
      3. Return copy of kwargs with hostaddr set to IPv4 address

    Args:
        kwargs: Connection parameters dict (may contain 'host', 'dsn', or both)

    Returns:
        Modified kwargs dict with 'hostaddr' set to IPv4 address, or None if resolution fails
    """
    if "hostaddr" in kwargs:
        return None

    host = kwargs.get("host")
    port = kwargs.get("port", 5432)

    if not host and "dsn" in kwargs:
        from urllib.parse import urlparse

        parsed = urlparse(str(kwargs.get("dsn", "")))
        host = parsed.hostname
        port = parsed.port or 5432

    if not host:
        return None

    try:
        ipv4_infos = socket.getaddrinfo(str(host), int(port), socket.AF_INET, socket.SOCK_STREAM)
        if not ipv4_infos:
            return None
        ipv4_addr = ipv4_infos[0][4][0]
    except Exception:
        return None

    retry_kwargs = dict(kwargs)
    retry_kwargs["hostaddr"] = ipv4_addr
    return retry_kwargs


def _use_pg() -> bool:
    """
    Determines whether to use PostgreSQL or SQLite.

    Returns:
        True if PostgreSQL credentials are configured, False otherwise (use SQLite)
    """
    return get_postgres_connect_kwargs() is not None


def _notify_streamlit(level: str, message: str) -> None:
    """
    Publishes messages to Streamlit UI if context exists.

    This is a no-op in non-Streamlit execution environments.

    Args:
        level: Streamlit level method ('warning', 'error', 'info', 'success')
        message: Message text to display
    """
    try:
        import streamlit as st

        fn = getattr(st, level, None)
        if callable(fn):
            fn(message)
    except Exception:
        pass


# ── Database Initialization ────────────────────────────────────────────────────


def _init_sqlite(db_path: Optional[Path] = None):
    """
    Initializes SQLite database and schema if not present.

    Creates:
      - data/db/ directory if missing
      - registros_om table with columns for indicator records
      - Unique index on (id_indicador, periodo, anio) for UPSERT functionality

    Args:
        db_path: Optional Path to database file. If None, uses default from config_provider.
    """
    if db_path is None:
        db_path = DB_PATH
        
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS registros_om (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            id_indicador      TEXT NOT NULL,
            nombre_indicador  TEXT,
            proceso           TEXT,
            periodo           TEXT,
            anio              INTEGER,
            tiene_om          INTEGER DEFAULT 0,
            tipo_accion       TEXT DEFAULT 'OM Kawak',
            numero_om         TEXT,
            comentario        TEXT,
            registrado_por    TEXT DEFAULT '',
            fecha_registro    TEXT,
            UNIQUE(id_indicador, periodo, anio)
        )
    """
    )
    conn.commit()

    # Ensure unique index exists for ON CONFLICT functionality
    from .schema_manager import _ensure_sqlite_unique_index

    _ensure_sqlite_unique_index(conn)
    conn.close()


def _init_postgres():
    """
    Initializes PostgreSQL database and schema if not present.

    Creates:
      - registros_om table with columns for indicator records
      - Unique constraint on (id_indicador, periodo, anio) for ON CONFLICT functionality
    """
    conn = _connect_postgres()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS registros_om (
            id                SERIAL PRIMARY KEY,
            id_indicador      TEXT NOT NULL,
            nombre_indicador  TEXT,
            proceso           TEXT,
            periodo           TEXT,
            anio              INTEGER,
            tiene_om          INTEGER DEFAULT 0,
            tipo_accion       TEXT DEFAULT 'OM Kawak',
            numero_om         TEXT,
            comentario        TEXT,
            registrado_por    TEXT DEFAULT '',
            fecha_registro    TEXT,
            UNIQUE(id_indicador, periodo, anio)
        )
    """
    )
    conn.commit()

    from .schema_manager import _ensure_postgres_unique_constraint

    _ensure_postgres_unique_constraint(cur)
    conn.commit()
    cur.close()
    conn.close()


def inicializar_db():
    """
    Main database initialization entry point.

    Initializes either PostgreSQL or SQLite based on credential availability.
    Non-fatal errors are logged as Streamlit warnings instead of crashing.
    """
    try:
        if _use_pg():
            _init_postgres()
        else:
            _init_sqlite()
    except Exception as e:
        _notify_streamlit("warning", f"No se pudo inicializar la base de datos: {e}")
