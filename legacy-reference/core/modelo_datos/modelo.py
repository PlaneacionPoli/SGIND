"""
Modelo de Datos Relacional SGIND

- Todas las entidades y relaciones se gestionan aquí.
- Los joins y cálculos se hacen siempre por ID.
- Este módulo es la única fuente de verdad para la estructura de datos y reglas de negocio.
"""

import pandas as pd
from typing import Optional


class ModeloSGIND:
    def __init__(
        self,
        df_indicadores: pd.DataFrame,
        df_lineas: Optional[pd.DataFrame] = None,
        df_objetivos: Optional[pd.DataFrame] = None,
        df_metas: Optional[pd.DataFrame] = None,
    ):
        self.df_indicadores = df_indicadores.copy()
        self.df_lineas = df_lineas.copy() if df_lineas is not None else None
        self.df_objetivos = df_objetivos.copy() if df_objetivos is not None else None
        self.df_metas = df_metas.copy() if df_metas is not None else None

    def join_linea(self):
        if self.df_lineas is not None:
            return self.df_indicadores.merge(self.df_lineas, on="ID", how="left")
        return self.df_indicadores

    def join_objetivo(self):
        if self.df_objetivos is not None:
            return self.df_indicadores.merge(self.df_objetivos, on="ID", how="left")
        return self.df_indicadores

    def join_meta(self):
        if self.df_metas is not None:
            return self.df_indicadores.merge(self.df_metas, on="ID", how="left")
        return self.df_indicadores

    def cumplimiento_por_linea(self, resultados: pd.DataFrame) -> pd.DataFrame:
        # Solo cierre anual (mes 12)
        cierre = resultados[resultados["Mes"] == 12]
        join = (
            cierre.merge(self.df_lineas, on="ID", how="left")
            if self.df_lineas is not None
            else cierre
        )
        return join.groupby("Linea")["cumplimiento_pct"].mean().reset_index()

    # Agrega aquí más métodos para KPIs, tendencias, etc.
