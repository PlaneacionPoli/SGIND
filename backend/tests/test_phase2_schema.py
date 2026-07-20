"""Tests Fase 2 — Modelo de datos PostgreSQL (TP-2.1 a TP-2.5)."""

import os
import time

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.schemas.common import RegistroOMCreate
from app.services.om_service import OMService

PG_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://sgind:sgind_dev_password@localhost:5432/sgind",
)


async def _pg_available() -> bool:
    try:
        engine = create_async_engine(PG_URL, pool_pre_ping=True)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def db_session():
    if not await _pg_available():
        pytest.skip("PostgreSQL no disponible en TEST_DATABASE_URL")

    engine = create_async_engine(PG_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session
        await session.rollback()

    await engine.dispose()


async def test_tp_2_1_schema_tables_exist(db_session: AsyncSession):
    """TP-2.1: tablas del esquema inicial presentes."""
    result = await db_session.execute(
        text(
            """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN (
                'roles', 'users', 'registros_om', 'acciones',
                'audit_log', 'ai_configs', 'ai_prompts'
              )
            ORDER BY table_name
            """
        )
    )
    tables = [row[0] for row in result.fetchall()]
    assert tables == [
        "acciones",
        "ai_configs",
        "ai_prompts",
        "audit_log",
        "registros_om",
        "roles",
        "users",
    ]


async def test_tp_2_2_upsert_om(db_session: AsyncSession):
    """TP-2.2: UPSERT con constraint UNIQUE(id_indicador, periodo, anio)."""
    service = OMService()
    key = f"TEST-{int(time.time())}"

    first = await service.create(
        db_session,
        RegistroOMCreate(
            id_indicador=key,
            nombre_indicador="Indicador test",
            proceso="Proceso test",
            periodo="Enero",
            anio=2025,
            sede="Bogotá",
            tiene_om=0,
            numero_om=None,
            comentario="Primera inserción",
            registrado_por="test@poligran.edu.co",
        ),
    )
    await db_session.flush()

    second = await service.create(
        db_session,
        RegistroOMCreate(
            id_indicador=key,
            nombre_indicador="Indicador test actualizado",
            proceso="Proceso test",
            periodo="Enero",
            anio=2025,
            sede="Medellín",
            tiene_om=1,
            numero_om="OM-999",
            comentario="Segunda inserción (upsert)",
            registrado_por="test@poligran.edu.co",
        ),
    )
    await db_session.flush()

    assert first.id == second.id
    assert second.nombre_indicador == "Indicador test actualizado"
    assert second.tiene_om == 1
    assert second.sede == "Medellín"
    assert second.numero_om == "OM-999"

    count = await db_session.execute(
        text(
            "SELECT COUNT(*) FROM registros_om WHERE id_indicador = :key"
        ),
        {"key": key},
    )
    assert count.scalar_one() == 1

    await db_session.execute(
        text("DELETE FROM registros_om WHERE id_indicador = :key"),
        {"key": key},
    )


async def test_tp_2_3_dashboard_query_performance(db_session: AsyncSession):
    """TP-2.3: query KPIs OM responde en < 500ms."""
    start = time.perf_counter()
    result = await db_session.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_registros,
                COUNT(*) FILTER (WHERE tiene_om = 1) AS con_om,
                COUNT(DISTINCT id_indicador) AS indicadores_unicos
            FROM registros_om
            WHERE anio = :anio AND periodo = :periodo
            """
        ),
        {"anio": 2025, "periodo": "Enero"},
    )
    row = result.fetchone()
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert row is not None
    assert elapsed_ms < 500


async def test_tp_2_5_referential_integrity(db_session: AsyncSession):
    """TP-2.5: roles seed y prompts IA sin violaciones FK."""
    roles = await db_session.execute(text("SELECT COUNT(*) FROM roles"))
    assert roles.scalar_one() >= 3

    prompts = await db_session.execute(
        text("SELECT COUNT(*) FROM ai_prompts WHERE name LIKE 'PT-%'")
    )
    assert prompts.scalar_one() >= 3

    orphans = await db_session.execute(
        text(
            """
            SELECT COUNT(*) FROM users u
            LEFT JOIN roles r ON r.id = u.role_id
            WHERE r.id IS NULL
            """
        )
    )
    assert orphans.scalar_one() == 0
