"""Modelo acciones de mejora."""

from datetime import datetime

from sqlalchemy import DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Accion(Base):
    __tablename__ = "acciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    accion: Mapped[str | None] = mapped_column(Text)
    responsable: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[str | None] = mapped_column(Text)
    marker_col: Mapped[str | None] = mapped_column(Text)
    marker_value: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
