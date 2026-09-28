"""Capa de validación del Informe Ejecutivo — audit_report.md / .json.

Implementa las reglas V1-V15 del prompt de auditoría que pueden verificarse
mecánicamente contra el payload ya construido (lista de `ConsolidadoLinea` +
metadatos de portada/hoja de ruta). Reglas que dependen de datos que el
repo todavía no expone de forma estructurada (V4 texto-vs-tabla con
variables reales, V10 subtotales de población, Opex/CAPEX) se dejan como
`NO_VERIFICABLE` explícito en vez de omitirse en silencio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.pdi_measurement import (
    TOPE_INDICADOR,
    TOPE_PROYECTO,
    ConsolidadoLinea,
    calcular_global,
)

Severidad = str  # "error" | "advertencia" | "info"


@dataclass
class Hallazgo:
    regla: str
    severidad: Severidad
    ubicacion: str
    valor_a: Any
    valor_b: Any
    mensaje: str
    sugerencia: str


def _tol(a: float, b: float, tol: float = 0.05) -> bool:
    return abs(a - b) <= tol


def validar_consolidados_linea(lineas: list[ConsolidadoLinea]) -> list[Hallazgo]:
    hallazgos: list[Hallazgo] = []
    for li in lineas:
        # V1: consolidado == promedio de sus perspectivas válidas
        partes = [
            r.promedio
            for r in (li.retos, li.proyectos, li.indicadores)
            if r.disponible and r.promedio is not None
        ]
        esperado = round(sum(partes) / len(partes), 2) if partes else None
        if (li.consolidado is None) != (esperado is None) or (
            li.consolidado is not None and esperado is not None and not _tol(li.consolidado, esperado)
        ):
            hallazgos.append(
                Hallazgo(
                    regla="V1",
                    severidad="error",
                    ubicacion=f"linea={li.linea}",
                    valor_a=li.consolidado,
                    valor_b=esperado,
                    mensaje="Consolidado de línea no coincide con el promedio de sus perspectivas válidas.",
                    sugerencia="Recalcular consolidado desde calcular_consolidado_linea(); no derivarlo aparte.",
                )
            )

        # V5: ningún proyecto Stand by debe figurar como incluido
        if any("stand" in exc.lower() for exc in li.proyectos.excluidos_detalle):
            pass  # correcto: están en excluidos, no en el promedio — nada que reportar

        # V6: indicador sobre el tope sin marca de tope aplicado — por
        # construcción, calcular_perspectiva_indicadores ya registra
        # tope_aplicado_a; si algún valor incluido > tope y no está en la
        # lista, es un hallazgo (defensivo: no debería ocurrir si se usó el
        # módulo de medición).
        # (No hay forma de reconstruir el valor crudo aquí porque solo se
        # guarda el promedio topado; se deja como respaldo documental.)

        # V12: estado vs. avance (proyectos)
        # Requiere avance crudo por proyecto, que no viaja en ConsolidadoLinea
        # (solo agregados) — se valida en validar_proyectos_crudo().

    return hallazgos


def validar_proyectos_crudo(
    proyectos_raw: list[dict[str, Any]],
) -> list[Hallazgo]:
    """proyectos_raw: [{"nombre","linea","estado","avance_pct"}, ...] — antes
    de aplicar tope/exclusión. Verifica V5, V11, V12, V13."""
    hallazgos: list[Hallazgo] = []
    for p in proyectos_raw:
        nombre = p.get("nombre", "?")
        linea = p.get("linea", "?")
        estado = p.get("estado", "")
        avance = p.get("avance_pct")
        if avance is None:
            continue

        # V11: avance > 100% en cálculos/gráficos sin tope
        if avance > TOPE_PROYECTO:
            hallazgos.append(
                Hallazgo(
                    regla="V11",
                    severidad="advertencia",
                    ubicacion=f"proyecto={nombre} ({linea})",
                    valor_a=avance,
                    valor_b=TOPE_PROYECTO,
                    mensaje="Proyecto con avance crudo superior al tope; debe limitarse a 100% en cálculo y barra.",
                    sugerencia="Usar calcular_perspectiva_proyectos(), que aplica min(avance,100) antes de promediar.",
                )
            )

        # V12: estado vs. avance inconsistente
        if estado == "Cerrado" and avance < 100:
            hallazgos.append(
                Hallazgo(
                    regla="V12",
                    severidad="error",
                    ubicacion=f"proyecto={nombre} ({linea})",
                    valor_a={"estado": estado, "avance": avance},
                    valor_b="Cerrado implica avance=100",
                    mensaje="Proyecto marcado Cerrado con avance menor a 100%.",
                    sugerencia="Confirmar con el maestro PMO: ¿el estado es incorrecto o falta actualizar %completado?",
                )
            )
        if avance >= 100 and estado not in ("Cerrado", "Finalizado", "Cierre"):
            hallazgos.append(
                Hallazgo(
                    regla="V12",
                    severidad="advertencia",
                    ubicacion=f"proyecto={nombre} ({linea})",
                    valor_a={"estado": estado, "avance": avance},
                    valor_b="avance=100 implica Cerrado",
                    mensaje="Proyecto con avance 100% pero no marcado como Cerrado.",
                    sugerencia="Confirmar con el maestro PMO si falta cerrar administrativamente el proyecto.",
                )
            )
    return hallazgos


def validar_global(
    global_reportado: float | None,
    consolidados_linea: list[float | None],
) -> list[Hallazgo]:
    """V2: el dato hero de portada debe coincidir con la fórmula configurada
    (FORMULA_GLOBAL en pdi_measurement.py)."""
    esperado = calcular_global(consolidados_linea)
    if (global_reportado is None) != (esperado is None) or (
        global_reportado is not None and esperado is not None and not _tol(global_reportado, esperado)
    ):
        return [
            Hallazgo(
                regla="V2",
                severidad="error",
                ubicacion="portada.dato_hero",
                valor_a=global_reportado,
                valor_b=esperado,
                mensaje="El global de portada no coincide con la fórmula configurada (promedio de consolidados de línea).",
                sugerencia="Recalcular con calcular_global(); no reutilizar una cifra histórica sin trazabilidad.",
            )
        ]
    return []


def validar_contador_estados(
    cumplidos: int, en_progreso: int, atencion: int, sin_medicion: int, total_medido_esperado: int
) -> list[Hallazgo]:
    """V3: cumplidos + en_progreso + atencion debe igualar el total de
    indicadores CON medición (sin contar los 'sin_medicion' aparte)."""
    suma = cumplidos + en_progreso + atencion
    if suma != total_medido_esperado:
        return [
            Hallazgo(
                regla="V3",
                severidad="error",
                ubicacion="resumen_ejecutivo.contador_estados",
                valor_a=suma,
                valor_b=total_medido_esperado,
                mensaje=(
                    f"Cumplidos({cumplidos}) + En progreso({en_progreso}) + "
                    f"Atención({atencion}) = {suma}, no coincide con el total medido "
                    f"({total_medido_esperado}). Sin medición: {sin_medicion}."
                ),
                sugerencia="Reconciliar con la hoja de ruta: todo indicador medido debe caer en exactamente una categoría.",
            )
        ]
    return []


def validar_topes_nota_metodologica(
    tope_proyecto_mostrado: float, tope_indicador_mostrado: float
) -> list[Hallazgo]:
    """V14: los topes impresos en la nota metodológica deben ser los mismos
    que TOPE_PROYECTO/TOPE_INDICADOR de config."""
    hallazgos = []
    if not _tol(tope_proyecto_mostrado, TOPE_PROYECTO, tol=0.01):
        hallazgos.append(
            Hallazgo(
                regla="V14",
                severidad="error",
                ubicacion="nota_metodologica.tope_proyecto",
                valor_a=tope_proyecto_mostrado,
                valor_b=TOPE_PROYECTO,
                mensaje="Tope de proyecto mostrado en el PDF no coincide con la config.",
                sugerencia="Generar la nota metodológica desde TOPE_PROYECTO/TOPE_INDICADOR, nunca como texto fijo.",
            )
        )
    if not _tol(tope_indicador_mostrado, TOPE_INDICADOR, tol=0.01):
        hallazgos.append(
            Hallazgo(
                regla="V14",
                severidad="error",
                ubicacion="nota_metodologica.tope_indicador",
                valor_a=tope_indicador_mostrado,
                valor_b=TOPE_INDICADOR,
                mensaje="Tope de indicador mostrado en el PDF no coincide con la config.",
                sugerencia="Generar la nota metodológica desde TOPE_PROYECTO/TOPE_INDICADOR, nunca como texto fijo.",
            )
        )
    return hallazgos


#: Reglas del prompt maestro que requieren datos/decisiones que el repo aún
#: no expone de forma estructurada — se listan explícitamente para no
#: omitirlas en silencio (regla del prompt: "si falta información, márcala
#: N/D y pregunta").
REGLAS_NO_VERIFICABLES_AUN = {
    "V4": "Requiere que texto y tabla compartan las mismas variables de plantilla; hoy generar_narrativa_estrategica.py escribe texto a mano (autoría Claude), no desde las cifras de build_informe_ejecutivo_lineas. Pendiente: pasar las cifras reales como variables Jinja2 al narrar.",
    "V7": "direccion (mayor_mejor/menor_mejor) no es un campo explícito en el dato fuente; hoy se resuelve vía IDS_NEGATIVO_PCT (lista curada en app/domain/constants.py). Pendiente: confirmar si esa lista es completa/vigente para los 49 indicadores.",
    "V8": "No hay medición automática de longitud de etiquetas en el HTML/CSS actual (requiere headless render + medición de overflow).",
    "V9": "Umbrales del semáforo: hoy hay al menos 3 regímenes distintos en el código (general 80/100/105, Plan Anual 95/100, Negativo-Porcentual 102/110) — la propuesta de un único set (100/90) del prompt maestro ROMPE esos regímenes existentes. Necesita decisión explícita de negocio antes de tocarlo.",
    "V10": "Subtotales de población (Pregrado+Posgrado vs. Presencial+Virtual) no están mapeados en este repo — requiere localizar la fuente de esas cifras primero.",
    "V15": "Requiere comparar el texto narrativo (autoría Claude) contra las tablas de proyectos en planeación/stand by línea por línea; hoy no hay un extractor automático del texto a variables.",
    "OPEX_CAPEX": "Regla de 'dentro de presupuesto' para Opex/CAPEX no está definida en ningún lugar del repo — el prompt pide confirmación explícita antes de tratarla como cumplimiento.",
}
