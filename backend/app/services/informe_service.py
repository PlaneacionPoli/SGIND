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


class InformeService:
    def __init__(self, excel: ExcelReaderService) -> None:
        self._excel = excel
        self._cmi = CMIService(excel)

    def get_filtros(self) -> dict:
        """Devuelve filtros disponibles (años, meses, procesos, etc.) reutilizando CMI procesos."""
        try:
            return self._cmi.get_procesos_filtros()
        except FileNotFoundError:
            return {"anios": [], "meses": [], "procesos": [], "subprocesos": [], "error": "datos no disponibles"}

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
            base_indicadores = self._cmi.get_procesos_indicators_light(
                anio=prev_year,
                mes=mes,
                unidad=unidad,
                proceso=proceso,
                subproceso=subproceso,
                clasificacion=clasificacion,
                frecuencia=frecuencia,
            )

        resumen = build_resumen_ejecutivo(indicadores, base_indicadores)
        vista_global = dash.get("vista_global", {})
        comparativa = vista_global.get("comparativa_anual") or build_comparativa_anual(
            vista_global.get("historico", []), mes
        )
        propuestas, prop_err = load_propuestas(self._excel, proceso or "Todos", subproceso or "Todos")
        auditoria, aud_err = load_auditoria(self._excel, proceso or "Todos")

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
        }
