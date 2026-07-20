"""Servicio de dashboard — delega en ResumenService (fuente Consolidado Cierres)."""



from __future__ import annotations



from app.services.excel_reader import ExcelReaderService

from app.services.resumen_service import ResumenService





class DashboardService:

    def __init__(self, excel: ExcelReaderService) -> None:

        self._resumen = ResumenService(excel)



    def get_filtros(self) -> dict:

        return self._resumen.get_filtros()



    def get_kpis(

        self,

        anio: int | None = None,

        periodo: str | None = None,

        vista: str = "indicadores",

    ) -> list[dict]:

        return self._resumen.get_kpis(anio=anio, periodo=periodo, vista=vista)



    def get_lineas(

        self,

        anio: int | None = None,

        periodo: str | None = None,

        vista: str = "indicadores",

    ) -> list[dict]:

        return self._resumen.get_lineas(anio=anio, periodo=periodo, vista=vista)



    def get_semaphore(

        self,

        anio: int | None = None,

        periodo: str | None = None,

        vista: str = "indicadores",

    ) -> list[dict]:

        return self._resumen.get_semaphore(anio=anio, periodo=periodo, vista=vista)



    def get_trend(

        self,

        anio: int | None = None,

        vista: str = "indicadores",

    ) -> list[dict]:

        return self._resumen.get_trend(anio=anio, vista=vista)



    def get_sunburst(self, anio: int | None = None, vista: str = "indicadores") -> list[dict]:

        return self._resumen.get_sunburst(anio=anio, vista=vista)



    def get_yoy(self, anio: int, vista: str = "indicadores") -> list[dict]:

        return self._resumen.get_yoy(anio=anio, vista=vista)



    def get_narrativa(self, anio: int | None = None, vista: str = "indicadores") -> dict:
        return self._resumen.get_narrativa(anio=anio, vista=vista)

    def get_resumen_completo(self, anio: int, vista: str = "indicadores", rango: bool = False) -> dict:
        return self._resumen.get_resumen_completo(anio=anio, vista=vista, rango=rango)

