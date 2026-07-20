from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RegistroOM(Base):
    __tablename__ = "registros_om"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_indicador: Mapped[str] = mapped_column(String, nullable=False)
    nombre_indicador: Mapped[str | None] = mapped_column(Text)
    proceso: Mapped[str | None] = mapped_column(Text)
    periodo: Mapped[str | None] = mapped_column(String)
    anio: Mapped[int | None] = mapped_column(Integer)
    sede: Mapped[str | None] = mapped_column(Text)
    tiene_om: Mapped[int] = mapped_column(Integer, default=0)
    tipo_accion: Mapped[str] = mapped_column(String, default="OM Kawak")
    numero_om: Mapped[str | None] = mapped_column(Text)
    comentario: Mapped[str | None] = mapped_column(Text)
    registrado_por: Mapped[str] = mapped_column(String, default="")
    fecha_registro: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
