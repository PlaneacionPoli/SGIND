"""Modelo de medición del Informe Ejecutivo — fuente única de verdad para
topes, exclusiones y fórmula de consolidado (auditoría 2026-09-27).

Este módulo NO sustituye todavía a `resumen_builders.build_informe_ejecutivo_lineas`
(ver hallazgos en el reporte de auditoría). Aísla las reglas de cálculo en un
solo lugar, parametrizable, para que:
  1. puedan probarse con pytest de forma aislada,
  2. `resumen_builders` las importe y las use en vez de recalcular a mano,
  3. cualquier cambio de tope/umbral se haga en un solo sitio.

Decisiones pendientes de confirmar con negocio (ver DECISION_* más abajo):
señaladas explícitamente para no fijarlas en silencio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Direccion = Literal["mayor_mejor", "menor_mejor"]

# ── Config (una sola fuente; nada de esto se repite en otro módulo) ────────

#: Tope de avance aplicado a CADA proyecto antes de promediar. Un proyecto no
#: puede "compensar" a otros por encima de su propia meta.
TOPE_PROYECTO = 100.0

#: Tope de cumplimiento aplicado a CADA indicador antes de promediar.
#: 130% ya es el techo vigente en el resto de la app (RANGO_CUMPLIMIENTO_MAX
#: en app/domain/constants.py) — se reutiliza aquí, no se reinventa.
TOPE_INDICADOR = 130.0

#: Estados de proyecto que se excluyen de numerador Y denominador del
#: promedio de la dimensión "proyectos" de una línea.
ESTADOS_EXCLUIDOS_PROMEDIO = frozenset({"Stand by"})

#: DECISIÓN PENDIENTE (confirmar con negocio): fórmula del dato hero de
#: portada. Recomendada — promedio simple de los consolidados de línea, NO
#: un recálculo distinto a partir de retos/proyectos/indicadores globales
#: (evita que portada y detalle por línea diverjan, V2).
FORMULA_GLOBAL = "promedio_consolidados_linea"

#: DECISIÓN PENDIENTE (confirmar con negocio): umbrales del semáforo único
#: usado en TODO el informe (resumen, tablas, hoja de ruta — V9).
UMBRAL_SEMAFORO_CUMPLIDO = 100.0  # >= => "Cumplido"
UMBRAL_SEMAFORO_EN_PROGRESO = 90.0  # >= => "En progreso"; debajo => "Atención"


@dataclass
class ProyectoInput:
    nombre: str
    linea: str
    estado: str
    avance_pct: float | None  # crudo, sin tope


@dataclass
class IndicadorInput:
    nombre: str
    linea: str
    meta: float | None
    ejecucion: float | None
    direccion: Direccion = "mayor_mejor"
    cumplimiento_pct: float | None = None  # ya calculado aguas arriba (con dirección aplicada)


@dataclass
class PerspectivaResultado:
    """Resultado de una perspectiva (retos | proyectos | indicadores) para
    una línea: promedio con topes/exclusiones ya aplicados, o N/A."""

    promedio: float | None
    n_incluidos: int
    n_excluidos: int = 0
    excluidos_detalle: list[str] = field(default_factory=list)
    tope_aplicado_a: list[str] = field(default_factory=list)
    disponible: bool = True


@dataclass
class ConsolidadoLinea:
    linea: str
    retos: PerspectivaResultado
    proyectos: PerspectivaResultado
    indicadores: PerspectivaResultado
    consolidado: float | None
    formula_texto: str


def calcular_perspectiva_proyectos(
    proyectos: list[ProyectoInput],
    *,
    tope: float = TOPE_PROYECTO,
    estados_excluidos: frozenset[str] = ESTADOS_EXCLUIDOS_PROMEDIO,
) -> PerspectivaResultado:
    """V5: un proyecto en Stand by NO entra al numerador ni al denominador,
    sin importar su avance. V13/C1: tope aplicado ANTES de promediar."""
    incluidos: list[float] = []
    excluidos: list[str] = []
    tope_aplicado: list[str] = []
    for p in proyectos:
        if p.estado in estados_excluidos:
            excluidos.append(p.nombre)
            continue
        avance = p.avance_pct if p.avance_pct is not None else 0.0
        if avance > tope:
            tope_aplicado.append(p.nombre)
        incluidos.append(min(avance, tope))

    if not incluidos:
        return PerspectivaResultado(
            promedio=None,
            n_incluidos=0,
            n_excluidos=len(excluidos),
            excluidos_detalle=excluidos,
            disponible=False,
        )
    promedio = round(sum(incluidos) / len(incluidos), 2)
    return PerspectivaResultado(
        promedio=promedio,
        n_incluidos=len(incluidos),
        n_excluidos=len(excluidos),
        excluidos_detalle=excluidos,
        tope_aplicado_a=tope_aplicado,
        disponible=True,
    )


def calcular_perspectiva_indicadores(
    indicadores: list[IndicadorInput],
    *,
    tope: float = TOPE_INDICADOR,
) -> PerspectivaResultado:
    """V7: la dirección (mayor_mejor/menor_mejor) debe resolverse AGUAS ARRIBA
    en `cumplimiento_pct` (ver categorizar_cumplimiento + IDS_NEGATIVO_PCT en
    app/domain/constants.py) — aquí solo se topa y se promedia. Indicadores
    sin meta o sin medición (cumplimiento_pct None) se excluyen y se cuentan
    aparte."""
    incluidos: list[float] = []
    excluidos: list[str] = []
    tope_aplicado: list[str] = []
    for ind in indicadores:
        if ind.cumplimiento_pct is None:
            excluidos.append(ind.nombre)
            continue
        valor = ind.cumplimiento_pct
        if valor > tope:
            tope_aplicado.append(ind.nombre)
        incluidos.append(min(valor, tope))

    if not incluidos:
        return PerspectivaResultado(
            promedio=None,
            n_incluidos=0,
            n_excluidos=len(excluidos),
            excluidos_detalle=excluidos,
            disponible=False,
        )
    promedio = round(sum(incluidos) / len(incluidos), 2)
    return PerspectivaResultado(
        promedio=promedio,
        n_incluidos=len(incluidos),
        n_excluidos=len(excluidos),
        excluidos_detalle=excluidos,
        tope_aplicado_a=tope_aplicado,
        disponible=True,
    )


def calcular_consolidado_linea(
    linea: str,
    *,
    retos_cumplimiento: float | None,
    proyectos: list[ProyectoInput],
    indicadores: list[IndicadorInput],
) -> ConsolidadoLinea:
    """Consolidado = promedio simple de las perspectivas VÁLIDAS (con dato).
    Si una perspectiva es N/A, el consolidado se calcula solo con las
    restantes (nunca se sustituye por 0)."""
    retos_res = PerspectivaResultado(
        promedio=retos_cumplimiento,
        n_incluidos=1 if retos_cumplimiento is not None else 0,
        disponible=retos_cumplimiento is not None,
    )
    proy_res = calcular_perspectiva_proyectos(proyectos)
    ind_res = calcular_perspectiva_indicadores(indicadores)

    partes = [r.promedio for r in (retos_res, proy_res, ind_res) if r.disponible and r.promedio is not None]
    consolidado = round(sum(partes) / len(partes), 2) if partes else None

    etiquetas = []
    if retos_res.disponible:
        etiquetas.append(f"{retos_res.promedio}")
    if proy_res.disponible:
        etiquetas.append(f"{proy_res.promedio}")
    if ind_res.disponible:
        etiquetas.append(f"{ind_res.promedio}")
    formula_texto = f"({' + '.join(etiquetas)}) / {len(etiquetas)}" if etiquetas else "N/A"

    return ConsolidadoLinea(
        linea=linea,
        retos=retos_res,
        proyectos=proy_res,
        indicadores=ind_res,
        consolidado=consolidado,
        formula_texto=formula_texto,
    )


def calcular_global(consolidados_linea: list[float | None]) -> float | None:
    """FORMULA_GLOBAL = 'promedio_consolidados_linea' (recomendada, pendiente
    de confirmar). Ignora líneas sin consolidado en vez de tratarlas como 0."""
    validos = [c for c in consolidados_linea if c is not None]
    if not validos:
        return None
    return round(sum(validos) / len(validos), 2)


def clasificar_semaforo(
    valor: float | None,
    *,
    cumplido: float = UMBRAL_SEMAFORO_CUMPLIDO,
    en_progreso: float = UMBRAL_SEMAFORO_EN_PROGRESO,
) -> str:
    if valor is None:
        return "Sin medición"
    if valor >= cumplido:
        return "Cumplido"
    if valor >= en_progreso:
        return "En progreso"
    return "Atención"
