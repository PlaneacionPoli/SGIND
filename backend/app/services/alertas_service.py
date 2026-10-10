"""Alertas de Seguimiento Operativo: parametrización y borradores .eml para Outlook.

No se envía correo desde el servidor: se generan borradores (.eml con ``X-Unsent: 1``) que
Outlook abre como mensajes sin enviar, para que la persona de Desempeño los revise y envíe.

Dos tipos de aviso:
- ``recordatorio``: para cada proceso, desde ``dias_antes`` días antes de SU fecha límite
  (plazo propio del proceso o el general).
- ``apertura``: para todos los procesos, una vez entre el día 1 y el día ``apertura_dias`` de
  cada mes, con los indicadores del corte recién cerrado.

El programador solo *prepara* (marca como ``listo``) y la app avisa; al descargar pasa a
``descargado``.
"""

from __future__ import annotations

import asyncio
import io
import logging
import re
import zipfile
from datetime import date, datetime, timedelta, timezone
from typing import Any

import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.concurrency import run_sync
from app.core.config import Settings
from app.domain.alertas_builders import (
    PLACEHOLDERS,
    MensajeRenderizado,
    construir_eml,
    construir_listado_outlook,
    corte_anterior,
    corte_de_apertura,
    cortes_a_notificar,
    fecha_limite,
    indicadores_a_reportar,
    nombre_archivo,
    nombre_corte,
    plazo_de,
    proximo_corte,
    renderizar_mensaje,
)
from app.domain.loader_utils import ascii_lower, id_a_str
from app.domain.seguimiento_builders import load_tracking
from app.models.alertas import (
    APERTURA_ASUNTO_DEFAULT,
    APERTURA_CUERPO_DEFAULT,
    ASUNTO_DEFAULT,
    CUERPO_DEFAULT,
    AlertaConfig,
    AlertaDestinatario,
    AlertaEnvio,
    AlertaPlazo,
)
from app.services.excel_reader import ExcelReaderService

logger = logging.getLogger(__name__)

# Colombia no tiene horario de verano: UTC-5 fijo evita depender de tzdata en Windows.
_BOGOTA = timezone(timedelta(hours=-5))
_EMAIL_RE = re.compile(r"^[^@\s,;]+@[^@\s,;]+\.[^@\s,;]+$")
_INTERVALO_SCHEDULER_S = 30 * 60
_CATALOGO = "raw/Catalogo de Indicadores.xlsx"
_DIRECTORIO = "raw/Directorio/Correos.xlsx"
TIPOS = ("recordatorio", "apertura")


def hoy_bogota() -> date:
    return datetime.now(_BOGOTA).date()


def normalizar_emails(valor: str) -> list[str]:
    """Separa por coma/punto y coma/salto de línea, valida y deduplica."""
    vistos: dict[str, None] = {}
    for crudo in re.split(r"[,;\s]+", valor or ""):
        email = crudo.strip().lower()
        if not email:
            continue
        if not _EMAIL_RE.match(email):
            raise ValueError(f"Correo inválido: {crudo}")
        vistos[email] = None
    return list(vistos)


def _plantilla(cfg: AlertaConfig, tipo: str) -> tuple[str, str]:
    if tipo == "apertura":
        return cfg.apertura_asunto, cfg.apertura_cuerpo
    return cfg.asunto, cfg.cuerpo


def _zip(items: list[tuple[str, bytes]], leeme: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for nombre, contenido in items:
            z.writestr(nombre, contenido)
        z.writestr("LEEME.txt", leeme.encode("utf-8"))
    return buf.getvalue()


def _leeme(titulo: str, n: int, sin_dest: list[str]) -> str:
    txt = (
        f"{titulo}\n"
        f"{n} borradores. Abra cada archivo .eml con Outlook: se abre como mensaje sin enviar.\n"
        "Revise la tabla, ajuste si hace falta y envíe.\n"
    )
    if sin_dest:
        txt += "\nSin destinatarios configurados (agréguelos en Outlook antes de enviar):\n"
        txt += "".join(f"  - {p}\n" for p in sin_dest)
    return txt


class AlertasService:
    def __init__(self, excel: ExcelReaderService, settings: Settings) -> None:
        self._excel = excel
        self._settings = settings

    # ── Parametrización ──────────────────────────────────────────────────────
    async def get_config(self, db: AsyncSession) -> AlertaConfig:
        cfg = await db.get(AlertaConfig, 1)
        if cfg is None:
            cfg = AlertaConfig(id=1)
            db.add(cfg)
        # Filas creadas por SQL sin plantilla (DEFAULT '') se completan con la plantilla base.
        for campo, defecto in (
            ("asunto", ASUNTO_DEFAULT),
            ("cuerpo", CUERPO_DEFAULT),
            ("apertura_asunto", APERTURA_ASUNTO_DEFAULT),
            ("apertura_cuerpo", APERTURA_CUERPO_DEFAULT),
        ):
            if not (getattr(cfg, campo) or "").strip():
                setattr(cfg, campo, defecto)
        await db.flush()
        await db.refresh(cfg)
        return cfg

    async def update_config(
        self, db: AsyncSession, datos: dict[str, Any], usuario: str
    ) -> AlertaConfig:
        cfg = await self.get_config(db)
        if "copia_a" in datos:
            datos["copia_a"] = ", ".join(normalizar_emails(datos["copia_a"] or ""))
        for campo, valor in datos.items():
            setattr(cfg, campo, valor)
        cfg.updated_by = usuario
        await db.flush()
        await db.refresh(cfg)
        return cfg

    async def listar_plazos(self, db: AsyncSession) -> dict[str, int]:
        rows = await db.execute(select(AlertaPlazo).order_by(AlertaPlazo.proceso))
        return {r.proceso: r.plazo_dias for r in rows.scalars()}

    async def guardar_plazo(self, db: AsyncSession, proceso: str, plazo_dias: int | None) -> None:
        """Fija el plazo propio del proceso; `None` lo devuelve al plazo general."""
        await db.execute(delete(AlertaPlazo).where(AlertaPlazo.proceso == proceso))
        if plazo_dias is not None:
            db.add(AlertaPlazo(proceso=proceso, plazo_dias=plazo_dias))
        await db.flush()

    def _directorio(self) -> dict[str, list[str]]:
        """Correos del directorio institucional (Correos.xlsx), por proceso del tracking.

        El cruce ignora mayúsculas y tildes. Las filas sin correo válido se omiten.
        """
        try:
            df = self._excel.read_excel(_DIRECTORIO, sheet_name="Destinatarios")
        except Exception:  # noqa: BLE001 — sin directorio, solo rigen los correos editados
            logger.warning("No se pudo leer el directorio de correos", exc_info=True)
            return {}
        df.columns = [str(c).strip() for c in df.columns]
        if not {"Proceso", "Correo"}.issubset(df.columns):
            return {}
        nombres = {ascii_lower(p).strip(): p for p in self.procesos_disponibles()}
        out: dict[str, list[str]] = {}
        for proceso, correo in zip(df["Proceso"], df["Correo"], strict=True):
            proceso_tracking = nombres.get(ascii_lower(str(proceso)).strip())
            if proceso_tracking is None:
                continue
            try:
                emails = normalizar_emails(str(correo)) if pd.notna(correo) else []
            except ValueError:
                logger.warning("Correo inválido en el directorio para %s: %s", proceso, correo)
                continue
            for e in emails:
                if e not in out.setdefault(proceso_tracking, []):
                    out[proceso_tracking].append(e)
        return out

    async def listar_destinatarios(
        self, db: AsyncSession, con_origen: bool = False
    ) -> Any:
        """Destinatarios vigentes por proceso.

        Los correos editados en la pantalla (BD) reemplazan a los del directorio; si un
        proceso no tiene correos editados, se usan los del directorio. Con `con_origen`
        devuelve además `{proceso: "directorio" | "manual"}`.
        """
        rows = (
            await db.execute(
                select(AlertaDestinatario)
                .where(AlertaDestinatario.activo.is_(True))
                .order_by(AlertaDestinatario.proceso, AlertaDestinatario.email)
            )
        ).scalars()
        editados: dict[str, list[str]] = {}
        for r in rows:
            editados.setdefault(r.proceso, []).append(r.email)
        efectivos = await run_sync(self._directorio)
        origen = dict.fromkeys(efectivos, "directorio")
        for proceso, emails in editados.items():
            efectivos[proceso] = emails
            origen[proceso] = "manual"
        return (efectivos, origen) if con_origen else efectivos

    async def guardar_destinatarios(
        self, db: AsyncSession, proceso: str, emails: list[str]
    ) -> list[str]:
        """Reemplaza la lista de destinatarios del proceso."""
        limpios = normalizar_emails(", ".join(emails))
        await db.execute(delete(AlertaDestinatario).where(AlertaDestinatario.proceso == proceso))
        db.add_all([AlertaDestinatario(proceso=proceso, email=e) for e in limpios])
        await db.flush()
        return limpios

    async def historial(self, db: AsyncSession, limit: int = 50) -> list[AlertaEnvio]:
        rows = await db.execute(select(AlertaEnvio).order_by(AlertaEnvio.id.desc()).limit(limit))
        return list(rows.scalars())

    def procesos_disponibles(self) -> list[str]:
        df = load_tracking(self._excel)
        if df.empty or "Proceso" not in df.columns:
            return []
        return sorted(df["Proceso"].dropna().astype(str).unique().tolist())

    # ── Datos de indicadores ─────────────────────────────────────────────────
    def _subprocesos(self) -> dict[str, str]:
        """Id de indicador → Subproceso, desde el Catálogo de Indicadores."""
        try:
            cat = self._excel.read_excel(_CATALOGO, sheet_name="Catalogo Indicadores")
        except Exception:  # noqa: BLE001 — sin catálogo, la tabla muestra "—"
            logger.warning("No se pudo leer el catálogo para Subproceso", exc_info=True)
            return {}
        cat.columns = [str(c).strip() for c in cat.columns]
        if not {"Id", "Subproceso"}.issubset(cat.columns):
            return {}
        cat = cat.dropna(subset=["Id", "Subproceso"])
        return {
            id_a_str(i): str(s).strip() for i, s in zip(cat["Id"], cat["Subproceso"], strict=True)
        }

    def consolidado_por_proceso(self, anio: int, mes: int) -> dict[str, pd.DataFrame]:
        df = indicadores_a_reportar(load_tracking(self._excel), anio, mes, self._subprocesos())
        return {str(p): g.reset_index(drop=True) for p, g in df.groupby("Proceso")}

    # ── Mensajes ─────────────────────────────────────────────────────────────
    def _mensaje(
        self,
        cfg: AlertaConfig,
        plazo: int,
        proceso: str,
        indicadores: pd.DataFrame,
        anio: int,
        mes: int,
        tipo: str,
    ) -> MensajeRenderizado:
        asunto, cuerpo = _plantilla(cfg, tipo)
        return renderizar_mensaje(
            asunto,
            cuerpo,
            proceso=proceso,
            anio=anio,
            mes=mes,
            plazo_dias=plazo,
            hoy=hoy_bogota(),
            indicadores=indicadores,
        )

    @staticmethod
    def _corte_por_defecto(plazo: int, tipo: str) -> tuple[int, int]:
        hoy = hoy_bogota()
        return corte_anterior(hoy) if tipo == "apertura" else proximo_corte(hoy, plazo)

    def vista_previa(
        self,
        cfg: AlertaConfig,
        plazos: dict[str, int],
        proceso: str,
        anio: int | None,
        mes: int | None,
        tipo: str = "recordatorio",
    ) -> dict[str, Any]:
        plazo = plazo_de(proceso, cfg.plazo_dias, plazos)
        if anio is None or mes is None:
            anio, mes = self._corte_por_defecto(plazo, tipo)
        indicadores = self.consolidado_por_proceso(anio, mes).get(proceso)
        if indicadores is None:
            indicadores = pd.DataFrame(
                columns=["Id", "Indicador", "Proceso", "Subproceso", "Periodicidad", "Estado"]
            )
        msg = self._mensaje(cfg, plazo, proceso, indicadores, anio, mes, tipo)
        return {
            "anio": anio,
            "mes": mes,
            "tipo": tipo,
            "plazo_dias": plazo,
            "fecha_limite": fecha_limite(anio, mes, plazo).isoformat(),
            "total_indicadores": len(indicadores),
            "asunto": msg.asunto,
            "html": msg.html,
            "texto": msg.texto,
        }

    # ── Borradores ───────────────────────────────────────────────────────────
    def _borradores(
        self,
        cfg: AlertaConfig,
        plazos: dict[str, int],
        destinatarios: dict[str, list[str]],
        anio: int,
        mes: int,
        tipo: str,
        procesos: list[str] | None,
    ) -> tuple[list[tuple[str, bytes]], list[str], list[str]]:
        """(archivos, procesos incluidos, procesos sin destinatarios) del corte."""
        cc = normalizar_emails(cfg.copia_a)
        archivos: list[tuple[str, bytes]] = []
        incluidos: list[str] = []
        sin_dest: list[str] = []
        for proceso, indicadores in self.consolidado_por_proceso(anio, mes).items():
            if procesos is not None and proceso not in procesos:
                continue
            plazo = plazo_de(proceso, cfg.plazo_dias, plazos)
            msg = self._mensaje(cfg, plazo, proceso, indicadores, anio, mes, tipo)
            para = destinatarios.get(proceso, [])
            if not para:
                sin_dest.append(proceso)
            eml = construir_eml(msg, para=para, cc=cc)
            archivos.append((nombre_archivo(tipo, anio, mes, proceso), eml))
            incluidos.append(proceso)
        return archivos, incluidos, sin_dest

    async def _marcar_descargado(
        self, db: AsyncSession, proceso: str, anio: int, mes: int, tipo: str, para: list[str]
    ) -> None:
        """Deja el corte del proceso como 'descargado' (reutiliza la fila 'listo' si existe)."""
        fila = (
            (
                await db.execute(
                    select(AlertaEnvio).where(
                        AlertaEnvio.proceso == proceso,
                        AlertaEnvio.anio == anio,
                        AlertaEnvio.mes == mes,
                        AlertaEnvio.tipo == tipo,
                        AlertaEnvio.estado == "listo",
                    )
                )
            )
            .scalars()
            .first()
        )
        if fila is not None:
            fila.estado = "descargado"
            return
        db.add(
            AlertaEnvio(
                proceso=proceso,
                anio=anio,
                mes=mes,
                tipo=tipo,
                estado="descargado",
                destinatarios=", ".join(para),
                origen="manual",
            )
        )

    async def generar_paquete(
        self,
        db: AsyncSession,
        anio: int | None,
        mes: int | None,
        tipo: str,
        procesos: list[str] | None = None,
    ) -> tuple[bytes, dict[str, Any]]:
        """ZIP con un borrador por proceso para el corte indicado (descarga manual)."""
        cfg = await self.get_config(db)
        plazos = await self.listar_plazos(db)
        destinatarios = await self.listar_destinatarios(db)
        if anio is None or mes is None:
            anio, mes = self._corte_por_defecto(cfg.plazo_dias, tipo)
        archivos, incluidos, sin_dest = await run_sync(
            self._borradores, cfg, plazos, destinatarios, anio, mes, tipo, procesos
        )
        for p in incluidos:
            await self._marcar_descargado(db, p, anio, mes, tipo, destinatarios.get(p, []))
        titulo = f"Borradores de {tipo} — corte {nombre_corte(anio, mes)}"
        resumen = {
            "anio": anio,
            "mes": mes,
            "tipo": tipo,
            "total": len(archivos),
            "sin_destinatarios": sin_dest,
        }
        return _zip(archivos, _leeme(titulo, len(archivos), sin_dest)), resumen

    async def borrador_proceso(
        self, db: AsyncSession, proceso: str, anio: int | None, mes: int | None, tipo: str
    ) -> tuple[str, bytes]:
        """Un solo .eml (para revisar un proceso sin generar todo el paquete)."""
        cfg = await self.get_config(db)
        plazos = await self.listar_plazos(db)
        destinatarios = await self.listar_destinatarios(db)
        if anio is None or mes is None:
            anio, mes = self._corte_por_defecto(plazo_de(proceso, cfg.plazo_dias, plazos), tipo)
        archivos, _, _ = await run_sync(
            self._borradores, cfg, plazos, destinatarios, anio, mes, tipo, [proceso]
        )
        if not archivos:
            raise LookupError("Este proceso no tiene indicadores por reportar en ese corte")
        return archivos[0]

    async def listado_outlook(
        self, db: AsyncSession, anio: int | None, mes: int | None, tipo: str
    ) -> tuple[bytes, int, int]:
        """.xlsx para la automatización local Auto_Correo (borradores directos en Outlook)."""
        cfg = await self.get_config(db)
        plazos = await self.listar_plazos(db)
        destinatarios = await self.listar_destinatarios(db)
        if anio is None or mes is None:
            anio, mes = self._corte_por_defecto(cfg.plazo_dias, tipo)
        consolidado = await run_sync(self.consolidado_por_proceso, anio, mes)
        plazo_por_proceso = {p: plazo_de(p, cfg.plazo_dias, plazos) for p in consolidado}
        contenido = await run_sync(
            construir_listado_outlook, consolidado, destinatarios, plazo_por_proceso, anio, mes, tipo
        )
        return contenido, anio, mes

    # ── Notificación y preparación automática ────────────────────────────────
    async def notificaciones(self, db: AsyncSession) -> dict[str, Any]:
        rows = (await db.execute(select(AlertaEnvio).where(AlertaEnvio.estado == "listo"))).scalars()
        grupos: dict[tuple[int, int, str], int] = {}
        for r in rows:
            clave = (r.anio, r.mes, r.tipo)
            grupos[clave] = grupos.get(clave, 0) + 1
        items = [
            {"anio": a, "mes": m, "tipo": t, "borradores": n}
            for (a, m, t), n in sorted(grupos.items())
        ]
        return {"listos": sum(i["borradores"] for i in items), "items": items}

    async def descargar_pendientes(self, db: AsyncSession) -> tuple[bytes, dict[str, Any]]:
        """ZIP con todos los borradores 'listo' (una carpeta por corte); pasan a 'descargado'."""
        cfg = await self.get_config(db)
        plazos = await self.listar_plazos(db)
        destinatarios = await self.listar_destinatarios(db)
        filas = list(
            (await db.execute(select(AlertaEnvio).where(AlertaEnvio.estado == "listo"))).scalars()
        )
        por_corte: dict[tuple[int, int, str], list[str]] = {}
        for f in filas:
            por_corte.setdefault((f.anio, f.mes, f.tipo), []).append(f.proceso)
        archivos: list[tuple[str, bytes]] = []
        sin_dest: list[str] = []
        for (anio, mes, tipo), procesos in por_corte.items():
            arch, _, sd = await run_sync(
                self._borradores, cfg, plazos, destinatarios, anio, mes, tipo, procesos
            )
            carpeta = nombre_corte(anio, mes).replace(" ", "_")
            archivos += [(f"{carpeta}/{n}", c) for n, c in arch]
            sin_dest += sd
        for f in filas:
            f.estado = "descargado"
        titulo = "Borradores pendientes de revisión y envío"
        resumen = {"total": len(archivos), "sin_destinatarios": sin_dest}
        return _zip(archivos, _leeme(titulo, len(archivos), sin_dest)), resumen

    async def _preparar(
        self, db: AsyncSession, anio: int, mes: int, tipo: str, hoy: date | None
    ) -> list[str]:
        """Marca como 'listo' los procesos del corte que aún no tienen registro.

        Con `hoy` (recordatorios) solo entran los procesos cuya fecha límite —según su
        propio plazo— cae dentro de la ventana de aviso.
        """
        cfg = await self.get_config(db)
        plazos = await self.listar_plazos(db)
        consolidado = await run_sync(self.consolidado_por_proceso, anio, mes)
        destinatarios = await self.listar_destinatarios(db)
        nuevos: list[str] = []
        for proceso, indicadores in consolidado.items():
            if hoy is not None:
                limite = fecha_limite(anio, mes, plazo_de(proceso, cfg.plazo_dias, plazos))
                if not 0 <= (limite - hoy).days <= cfg.dias_antes:
                    continue
            existe = await db.execute(
                select(AlertaEnvio.id)
                .where(
                    AlertaEnvio.proceso == proceso,
                    AlertaEnvio.anio == anio,
                    AlertaEnvio.mes == mes,
                    AlertaEnvio.tipo == tipo,
                )
                .limit(1)
            )
            if existe.first() is not None:
                continue
            db.add(
                AlertaEnvio(
                    proceso=proceso,
                    anio=anio,
                    mes=mes,
                    tipo=tipo,
                    estado="listo",
                    destinatarios=", ".join(destinatarios.get(proceso, [])),
                    total_indicadores=len(indicadores),
                    origen="automatico",
                )
            )
            nuevos.append(proceso)
        await db.flush()
        return nuevos

    async def ejecutar_programado(
        self, db: AsyncSession, hoy: date | None = None
    ) -> dict[str, Any]:
        """Un ciclo del scheduler: prepara la apertura mensual y los recordatorios en ventana."""
        cfg = await self.get_config(db)
        if not cfg.activo:
            return {"activo": False}
        ahora = datetime.now(_BOGOTA)
        hoy = hoy or ahora.date()
        if hoy == ahora.date() and ahora.hour < cfg.hora_envio:
            return {"activo": True, "esperando_hora": True}

        preparados: dict[str, list[str]] = {}
        if cfg.apertura_activo and (corte := corte_de_apertura(hoy, cfg.apertura_dias)):
            if nuevos := await self._preparar(db, *corte, "apertura", None):
                preparados[f"apertura {corte[0]}-{corte[1]:02d}"] = nuevos

        # Cortes candidatos: unión de los de cada plazo distinto (general + propios).
        plazos = await self.listar_plazos(db)
        candidatos: set[tuple[int, int]] = set()
        for plazo in {cfg.plazo_dias, *plazos.values()}:
            candidatos.update(cortes_a_notificar(hoy, cfg.dias_antes, plazo))
        for anio, mes in sorted(candidatos):
            if nuevos := await self._preparar(db, anio, mes, "recordatorio", hoy):
                preparados[f"recordatorio {anio}-{mes:02d}"] = nuevos
        return {"activo": True, "preparados": preparados}


async def scheduler_loop(settings: Settings) -> None:
    """Revisa cada 30 min si hay borradores por preparar (ALERTAS_SCHEDULER_ENABLED)."""
    from app.api.deps import get_excel_service
    from app.core.database import AsyncSessionLocal

    service = AlertasService(get_excel_service(settings), settings)
    logger.info("Scheduler de alertas de seguimiento iniciado")
    while True:
        try:
            async with AsyncSessionLocal() as db:
                res = await service.ejecutar_programado(db)
                await db.commit()
                if res.get("preparados"):
                    logger.info("Borradores de seguimiento preparados: %s", res["preparados"])
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Error en el ciclo del scheduler de alertas")
        await asyncio.sleep(_INTERVALO_SCHEDULER_S)


__all__ = ["AlertasService", "PLACEHOLDERS", "TIPOS", "normalizar_emails", "scheduler_loop"]
