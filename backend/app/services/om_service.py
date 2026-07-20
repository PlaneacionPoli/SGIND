from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.om import RegistroOM
from app.schemas.common import RegistroOMCreate, RegistroOMCerrar, RegistroOMUpdate


class OMService:
    async def list_registros(
        self,
        db: AsyncSession,
        *,
        anio: int | None = None,
        periodo: str | None = None,
    ) -> list[RegistroOM]:
        query = select(RegistroOM).order_by(RegistroOM.anio.desc(), RegistroOM.periodo)
        if anio is not None:
            query = query.where(RegistroOM.anio == anio)
        if periodo is not None:
            query = query.where(RegistroOM.periodo == periodo)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, data: RegistroOMCreate) -> RegistroOM:
        now = datetime.now(UTC).isoformat()
        stmt = (
            insert(RegistroOM)
            .values(**data.model_dump(), fecha_registro=now)
            .on_conflict_do_update(
                index_elements=["id_indicador", "periodo", "anio"],
                set_={
                    "nombre_indicador": data.nombre_indicador,
                    "proceso": data.proceso,
                    "sede": data.sede,
                    "tiene_om": data.tiene_om,
                    "tipo_accion": data.tipo_accion,
                    "numero_om": data.numero_om,
                    "comentario": data.comentario,
                    "registrado_por": data.registrado_por,
                    "fecha_registro": now,
                },
            )
            .returning(RegistroOM)
        )
        result = await db.execute(stmt)
        registro = result.scalar_one()
        await db.refresh(registro)
        return registro

    async def update(
        self, db: AsyncSession, registro_id: int, data: RegistroOMUpdate
    ) -> RegistroOM | None:
        result = await db.execute(select(RegistroOM).where(RegistroOM.id == registro_id))
        registro = result.scalar_one_or_none()
        if registro is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(registro, field, value)
        registro.fecha_registro = datetime.now(UTC).isoformat()
        return registro

    async def cerrar(
        self, db: AsyncSession, registro_id: int, data: RegistroOMCerrar
    ) -> RegistroOM | None:
        """Cierra un OM: establece tiene_om=0 y registra fecha de cierre."""
        result = await db.execute(select(RegistroOM).where(RegistroOM.id == registro_id))
        registro = result.scalar_one_or_none()
        if registro is None:
            return None
        registro.tiene_om = 0
        if data.comentario is not None:
            registro.comentario = data.comentario
        registro.fecha_registro = datetime.now(UTC).isoformat()
        return registro

    async def delete(self, db: AsyncSession, registro_id: int) -> bool:
        result = await db.execute(select(RegistroOM).where(RegistroOM.id == registro_id))
        registro = result.scalar_one_or_none()
        if registro is None:
            return False
        await db.delete(registro)
        return True
