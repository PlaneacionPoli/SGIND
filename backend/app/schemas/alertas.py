from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

TipoAlerta = Literal["recordatorio", "apertura"]


class AlertaConfigOut(BaseModel):
    activo: bool
    dias_antes: int
    plazo_dias: int
    hora_envio: int
    asunto: str
    cuerpo: str
    copia_a: str
    apertura_activo: bool
    apertura_dias: int
    apertura_asunto: str
    apertura_cuerpo: str
    updated_by: str = ""
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class AlertaConfigUpdate(BaseModel):
    activo: bool | None = None
    dias_antes: int | None = Field(None, ge=0, le=60)
    plazo_dias: int | None = Field(None, ge=0, le=120)
    hora_envio: int | None = Field(None, ge=0, le=23)
    asunto: str | None = Field(None, min_length=3, max_length=300)
    cuerpo: str | None = Field(None, min_length=10, max_length=8000)
    copia_a: str | None = Field(None, max_length=1000)
    apertura_activo: bool | None = None
    apertura_dias: int | None = Field(None, ge=1, le=10)
    apertura_asunto: str | None = Field(None, min_length=3, max_length=300)
    apertura_cuerpo: str | None = Field(None, min_length=10, max_length=8000)


class AlertasConfigResponse(BaseModel):
    config: AlertaConfigOut
    destinatarios: dict[str, list[str]]
    # "directorio" (Correos.xlsx) o "manual" (editado en pantalla), por proceso
    origen_destinatarios: dict[str, str]
    plazos: dict[str, int]
    procesos: list[str]
    placeholders: dict[str, str]
    scheduler_activo: bool
    proximo_corte: dict[str, int | str]


class PlazoUpdate(BaseModel):
    proceso: str = Field(min_length=1)
    # None = volver al plazo general
    plazo_dias: int | None = Field(None, ge=0, le=120)


class DestinatariosUpdate(BaseModel):
    proceso: str = Field(min_length=1)
    emails: list[str] = Field(default_factory=list, max_length=30)


class VistaPreviaResponse(BaseModel):
    anio: int
    mes: int
    tipo: TipoAlerta
    plazo_dias: int
    fecha_limite: str
    total_indicadores: int
    asunto: str
    html: str
    texto: str


class BorradoresRequest(BaseModel):
    tipo: TipoAlerta = "recordatorio"
    anio: int | None = None
    mes: int | None = Field(None, ge=1, le=12)
    procesos: list[str] | None = None


class NotificacionItem(BaseModel):
    anio: int
    mes: int
    tipo: TipoAlerta
    borradores: int


class NotificacionesResponse(BaseModel):
    listos: int
    items: list[NotificacionItem] = Field(default_factory=list)


class EnvioOut(BaseModel):
    id: int
    proceso: str
    anio: int
    mes: int
    tipo: str = "recordatorio"
    estado: str
    destinatarios: str
    total_indicadores: int
    detalle: str | None = None
    origen: str
    enviado_at: datetime | None = None

    model_config = {"from_attributes": True}
