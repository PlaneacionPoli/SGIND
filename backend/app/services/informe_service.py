"""Servicio Informe por Procesos — compone CMI procesos + auditoría/propuestas."""

from __future__ import annotations

from typing import Any

from app.domain.informe_builders import (
    build_analisis_ia,
    build_comparativa_anual,
    build_criticos,
    build_resumen_ejecutivo,
    load_auditoria,
    load_propuestas,
)
from app.services.cmi_service import CMIService
from app.services.excel_reader import ExcelReaderService
from app.services.narrativa_ia_proceso_service import get_or_refresh_narrativa_ia_proceso


class InformeService:
    def __init__(self, excel: ExcelReaderService) -> None:
        self._excel = excel
        self._cmi = CMIService(excel)

    def get_filtros(self) -> dict:
        """Devuelve filtros disponibles (años, meses, procesos, etc.) reutilizando CMI procesos."""
        try:
            return self._cmi.get_procesos_filtros()
        except FileNotFoundError:
            return {
                "anios": [],
                "meses": [],
                "procesos": [],
                "subprocesos": [],
                "error": "datos no disponibles",
            }

    def get_dashboard(
        self,
        *,
        anio: int,
        mes: int = 12,
        unidad: str | None = None,
        proceso: str | None = None,
        subproceso: str | None = None,
        clasificacion: str | None = None,
        frecuencia: str | None = None,
    ) -> dict[str, Any]:
        dash = self._cmi.get_procesos_dashboard(
            anio=anio,
            mes=mes,
            unidad=unidad,
            proceso=proceso,
            subproceso=subproceso,
            clasificacion=clasificacion,
            frecuencia=frecuencia,
        )
        indicadores = dash.get("indicadores", [])
        prev_year = anio - 1
        base_indicadores: list[dict[str, Any]] = []
        if prev_year in dash.get("anios_disponibles", []):
            # Paridad con el original: el año base solo aplica el filtro
            # organizacional por defecto (año/mes), no los filtros de UI
            # seleccionados (proceso/subproceso/clasificacion/frecuencia/unidad).
            base_indicadores = self._cmi.get_procesos_indicators_light(
                anio=prev_year,
                mes=mes,
            )

        resumen = build_resumen_ejecutivo(indicadores, base_indicadores)
        historico_anual = self._cmi.get_procesos_historico_anual(
            anio_actual=anio, mes=mes, proceso=proceso, subproceso=subproceso
        )
        comparativa = build_comparativa_anual(historico_anual, mes)
        propuestas, prop_err = load_propuestas(
            self._excel, proceso or "Todos", subproceso or "Todos"
        )
        auditoria, aud_err = load_auditoria(self._excel, proceso or "Todos")

        variacion_procesos = dash.get("analisis_avanzado", {}).get("variacion_procesos", {})
        try:
            narrativa_entry = get_or_refresh_narrativa_ia_proceso(
                proceso=proceso or "Todos",
                anio=anio,
                mes=mes,
                resumen=resumen,
                criticos=build_criticos(indicadores, limit=3),
                mejora=(variacion_procesos.get("mejoraron") or [None])[0],
                riesgo=(variacion_procesos.get("empeoraron") or [None])[0],
                base_anio=prev_year,
            )
        except Exception:
            narrativa_entry = {"publicado": None, "borrador": None, "historial": []}
        publicado = narrativa_entry.get("publicado")
        narrativa_ia_proceso = (
            {
                "titulo": publicado["titulo"],
                "estado_color": publicado["estado_color"],
                "foco_urgente": publicado["foco_urgente"],
                "directrices": publicado["directrices"],
                "texto_html": publicado["texto_html"],
                "modelo": publicado["modelo"],
                "generado_en": publicado["generado_en"],
                "revisado_por": publicado.get("revisado_por"),
                "revisado_en": publicado.get("revisado_en"),
            }
            if publicado
            else None
        )

        return {
            **dash,
            "resumen_ejecutivo": resumen,
            "comparativa_interanual": comparativa,
            "criticos": build_criticos(indicadores),
            "distribucion_estado": {
                "cumple": resumen["cumple"],
                "alerta": resumen["alerta"],
                "critico": resumen["peligro"],
                "sin_dato": resumen["sin_dato"],
            },
            "propuestas": propuestas,
            "propuestas_error": prop_err,
            "auditoria": auditoria,
            "auditoria_error": aud_err,
            "analisis_ia": build_analisis_ia(indicadores),
            "narrativa_ia_proceso": narrativa_ia_proceso,
            "narrativa_ia_pendiente": narrativa_entry.get("borrador") is not None,
        }
