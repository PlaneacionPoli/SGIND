"""
core/db — Persistencia de datos (dual SQLite/PostgreSQL).

API pública que mantiene backward compatibility con core.db_manager.
"""

from core.db.config_provider import (
    DB_PATH,
    get_database_url,
    get_postgres_connect_kwargs,
    get_sqlite_path,
    safe_streamlit_secrets_get,
    use_postgres,
    sanitize_postgres_dsn,
    extract_supabase_project_ref,
)

from core.db.data_normalizer import (
    numero_mes_a_nombre,
    normalizar_nombre_mes,
    normalizar_periodo_anio,
)

from core.db.connection_manager import (
    inicializar_db,
    _connect_postgres,
    _build_ipv4_retry_connect_kwargs,
    _use_pg,
    _notify_streamlit,
    _init_sqlite,
    _init_postgres,
)

from core.db.operations import (
    guardar_registro_om,
    leer_registros_om,
    registros_om_como_dict,
    guardar_acciones_bulk,
    leer_acciones,
    borrar_acciones_por_marker,
)

__all__ = [
    # Config provider
    "DB_PATH",
    "get_database_url",
    "get_postgres_connect_kwargs",
    "get_sqlite_path",
    "safe_streamlit_secrets_get",
    "use_postgres",
    "sanitize_postgres_dsn",
    "extract_supabase_project_ref",
    # Data normalizer
    "numero_mes_a_nombre",
    "normalizar_nombre_mes",
    "normalizar_periodo_anio",
    # Connection manager
    "inicializar_db",
    "_connect_postgres",
    "_build_ipv4_retry_connect_kwargs",
    "_use_pg",
    "_notify_streamlit",
    "_init_sqlite",
    "_init_postgres",
    # Operations
    "guardar_registro_om",
    "leer_registros_om",
    "registros_om_como_dict",
    "guardar_acciones_bulk",
    "leer_acciones",
    "borrar_acciones_por_marker",
]
