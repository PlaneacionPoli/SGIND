from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

ASUNTO_DEFAULT = "Recordatorio: reporte de indicadores en KAWAK — corte {corte} ({proceso})"
APERTURA_ASUNTO_DEFAULT = "Reporte de indicadores en KAWAK — corte {corte} ({proceso})"

# Plantilla HTML (fragmento). Variables: ver PLACEHOLDERS en domain/alertas_builders.py.
CUERPO_DEFAULT = """<p>Estimados,</p>

<p>
    Desde el proceso de Desempeño Institucional, solicitamos de manera atenta su colaboración con el reporte de resultados y análisis de los indicadores habilitados en <b><a href="https://kawak.com.co/poligran/" target="_blank" style="color: #1F4E78; text-decoration: underline;">KAWAK</a></b>, con corte al mes de {corte_mes}.
    Este ejercicio es fundamental para visibilizar el desempeño institucional, identificar los principales desafíos y asegurar el cumplimiento de las metas definidas.
</p>

<br>
{tabla_html}
<br>

<p>
    <b>Fecha máxima de reporte: {fecha_limite}.</b>
</p>

<p>
    Para el correcto diligenciamiento del <b>análisis de cada indicador</b>, es indispensable desarrollar de manera clara y concreta los siguientes aspectos:
</p>

<ul>
    <li>Interpretación del resultado: ¿qué indica el resultado del indicador y cómo se interpreta frente al periodo evaluado?</li>
    <li>Cumplimiento de la meta: ¿el indicador cumple o no cumple la meta establecida?</li>
    <li>Causas: principales factores que explican el resultado obtenido.</li>
    <li>Impacto: efecto del resultado en el logro de los objetivos y en el desempeño del proceso.</li>
    <li>Acciones: acciones implementadas o de mejora propuestas en caso de desviaciones.</li>
</ul>

<p>
    Adicionalmente, es obligatorio cargar en Kawak la evidencia correspondiente a cada indicador reportado, la cual debe soportar de manera clara los resultados registrados y el análisis realizado.
</p>

<p>
    En caso de requerir acompañamiento, el Sistema Integrado de Aseguramiento y Gestión para la Sostenibilidad – <b>POLISIGS</b>, en cabeza de Camilo Coronel, y con el apoyo de sus dinamizadores
    (Ximena Silva, Miguel López, Carolina Montaño y Maria Paula Pinzón), estará atento a atender sus inquietudes y novedades.
</p>

<br>
<p>Cordialmente,</p>
<p>
    <b>Sistema Integrado de Aseguramiento y Gestión para la Sostenibilidad – POLISIGS</b>
</p>"""
APERTURA_CUERPO_DEFAULT = CUERPO_DEFAULT


class AlertaConfig(Base):
    """Parámetros globales de las alertas por correo (una sola fila, id=1)."""

    __tablename__ = "alertas_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    activo: Mapped[bool] = mapped_column(Boolean, default=False)
    dias_antes: Mapped[int] = mapped_column(Integer, default=5)
    # Días calendario tras el cierre del mes del corte para reportar.
    # Plazo general; cada proceso puede tener el suyo en `alertas_plazos`.
    plazo_dias: Mapped[int] = mapped_column(Integer, default=15)
    hora_envio: Mapped[int] = mapped_column(Integer, default=7)
    asunto: Mapped[str] = mapped_column(Text, default=ASUNTO_DEFAULT)
    cuerpo: Mapped[str] = mapped_column(Text, default=CUERPO_DEFAULT)
    copia_a: Mapped[str] = mapped_column(Text, default="")
    # Aviso de apertura: una vez al mes, a todos los procesos, entre el día 1 y el
    # día `apertura_dias` (por defecto 3), con los indicadores del corte recién cerrado.
    apertura_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    apertura_dias: Mapped[int] = mapped_column(Integer, default=3)
    apertura_asunto: Mapped[str] = mapped_column(Text, default=APERTURA_ASUNTO_DEFAULT)
    apertura_cuerpo: Mapped[str] = mapped_column(Text, default=APERTURA_CUERPO_DEFAULT)
    updated_by: Mapped[str] = mapped_column(String, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AlertaDestinatario(Base):
    __tablename__ = "alertas_destinatarios"
    __table_args__ = (UniqueConstraint("proceso", "email", name="uq_alerta_proceso_email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proceso: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AlertaPlazo(Base):
    """Plazo propio de un proceso (sustituye al plazo general de la configuración)."""

    __tablename__ = "alertas_plazos"

    proceso: Mapped[str] = mapped_column(Text, primary_key=True)
    plazo_dias: Mapped[int] = mapped_column(Integer, nullable=False)


class AlertaEnvio(Base):
    """Historial de envíos; también evita reenviar el mismo corte a un proceso."""

    __tablename__ = "alertas_envios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proceso: Mapped[str] = mapped_column(Text, nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)
    # recordatorio | apertura
    tipo: Mapped[str] = mapped_column(String, default="recordatorio")
    # listo (preparado, pendiente de descargar) | descargado
    estado: Mapped[str] = mapped_column(String, nullable=False)
    destinatarios: Mapped[str] = mapped_column(Text, default="")
    total_indicadores: Mapped[int] = mapped_column(Integer, default=0)
    detalle: Mapped[str | None] = mapped_column(Text)
    origen: Mapped[str] = mapped_column(String, default="automatico")
    enviado_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
