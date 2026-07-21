"""
analytics/data_preparator.py
Preparación de datasets para analítica predictiva - Fase 4.

Responsabilidades:
- Cargar y limpiar datos de Resultados Consolidados
- Generar features para modelos predictivos
- Crear datasets de entrenamiento y validación
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTES
# =============================================================================

DATA_PATH = Path("data/output/Resultados Consolidados.xlsx")
OUTPUT_PATH = Path("data/output/analytics")


# =============================================================================
# CONFIGURACIÓN DE HOJAS
# =============================================================================

HOJA_CONSOLIDADO = "Consolidado Historico"
HOJA_CATALOGO = "Catalogo Indicadores"
HOJA_BASE_NORMALIZADA = "Base Normalizada"


# =============================================================================
# ESTRUCTURAS DE DATOS
# =============================================================================

@dataclass
class DatasetInfo:
    """Información sobre un dataset preparado."""
    nombre: str
    filas: int
    columnas: int
    periodo_min: Optional[str]
    periodo_max: Optional[str]
    indicadores_unicos: int
    rutas: List[str]


@dataclass
class PreparacionResult:
    """Resultado de la preparación de datos."""
    exitosa: bool
    dataset_info: Optional[DatasetInfo]
    errores: List[str]
    warnings: List[str]


# =============================================================================
# PREPARADOR DE DATOS
# =============================================================================

class DataPreparator:
    """
    Preparador de datos para analítica predictiva.
    
    Carga, limpia y transforma datos históricos para generar
    datasets listos para modelado.
    """

    def __init__(self, data_path: Path = DATA_PATH):
        """
        Inicializa el preparador.
        
        Args:
            data_path: Ruta al archivo de datos consolidados
        """
        self.data_path = data_path
        self.OUTPUT_PATH = OUTPUT_PATH
        self.OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
        
        self.df_original: Optional[pd.DataFrame] = None
        self.df_limpio: Optional[pd.DataFrame] = None
        self.df_features: Optional[pd.DataFrame] = None
        
        self.dataset_info: Optional[DatasetInfo] = None
        
        logger.info(f"DataPreparator inicializado. Data path: {data_path}")

    def cargar_datos(self) -> PreparacionResult:
        """
        Carga los datos desde el archivo Excel.
        
        Returns:
            Resultado de la carga
        """
        errores = []
        warnings = []
        
        try:
            logger.info(f"Cargando datos desde {self.data_path}")
            
            # Cargar hoja principal
            self.df_original = pd.read_excel(
                self.data_path,
                sheet_name=HOJA_CONSOLIDADO
            )
            
            filas = len(self.df_original)
            columnas = len(self.df_original.columns)
            indicadores = self.df_original["Id"].nunique() if "Id" in self.df_original.columns else 0
            
            # Obtener rango de fechas
            periodo_min = None
            periodo_max = None
            if "Fecha" in self.df_original.columns:
                try:
                    self.df_original["Fecha"] = pd.to_datetime(self.df_original["Fecha"])
                    periodo_min = self.df_original["Fecha"].min()
                    periodo_max = self.df_original["Fecha"].max()
                except:
                    warnings.append("No se pudo parsear la columna Fecha")
            
            self.dataset_info = DatasetInfo(
                nombre="Consolidado Historico",
                filas=filas,
                columnas=columnas,
                periodo_min=str(periodo_min) if periodo_min else None,
                periodo_max=str(periodo_max) if periodo_max else None,
                indicadores_unicos=indicadores,
                rutas=[str(self.data_path)]
            )
            
            logger.info(f"Datos cargados: {filas} filas, {columnas} columnas, {indicadores} indicadores")
            
            return PreparacionResult(
                exitosa=True,
                dataset_info=self.dataset_info,
                errores=errores,
                warnings=warnings
            )
            
        except FileNotFoundError:
            errores.append(f"Archivo no encontrado: {self.data_path}")
            return PreparacionResult(
                exitosa=False,
                dataset_info=None,
                errores=errores,
                warnings=warnings
            )
            
        except Exception as e:
            errores.append(f"Error cargando datos: {str(e)}")
            logger.exception("Error en cargar_datos")
            return PreparacionResult(
                exitosa=False,
                dataset_info=None,
                errores=errores,
                warnings=warnings
            )

    def limpiar_datos(self) -> PreparacionResult:
        """
        Limpia los datos cargados.
        
        Returns:
            Resultado de la limpieza
        """
        errores = []
        warnings = []
        
        if self.df_original is None:
            errores.append("No hay datos cargados. Ejecute cargar_datos() primero.")
            return PreparacionResult(
                exitosa=False,
                dataset_info=None,
                errores=errores,
                warnings=warnings
            )
        
        try:
            logger.info("Iniciando limpieza de datos...")
            self.df_limpio = self.df_original.copy()
            
            # 1. Eliminar duplicados
            inicial_filas = len(self.df_limpio)
            self.df_limpio = self.df_limpio.drop_duplicates()
            dup_eliminados = inicial_filas - len(self.df_limpio)
            if dup_eliminados > 0:
                warnings.append(f"Eliminados {dup_eliminados} duplicados")
            
            # 2. Manejar nulos en columnas clave
            # Solo requerimos Id, Indicador, Fecha y Cumplimiento (calculado)
            columnas_clave = ["Id", "Indicador", "Fecha"]
            # Cumplimiento puede estar vacío si se calcula desde Meta/Ejecucion
            columnas_opcionales = ["Meta", "Ejecucion", "Proceso", "Periodicidad", "Sentido"]
            
            for col in columnas_clave:
                if col in self.df_limpio.columns:
                    nulos = self.df_limpio[col].isna().sum()
                    if nulos > 0:
                        warnings.append(f"Columna {col}: {nulos} valores nulos")
                        # Eliminar filas con nulos en columnas clave
                        self.df_limpio = self.df_limpio.dropna(subset=[col])
            
            # 3. Calcular Cumplimiento si está vacío
            if "Cumplimiento" in self.df_limpio.columns:
                nulos_cumplimiento = self.df_limpio["Cumplimiento"].isna().sum()
                
                # Si Cumplimiento está vacío pero hay Meta y Ejecucion, calcular
                if nulos_cumplimiento == len(self.df_limpio):
                    if "Ejecucion" in self.df_limpio.columns and "Meta" in self.df_limpio.columns:
                        # Calcular: Ejecucion / Meta
                        self.df_limpio["Cumplimiento"] = (
                            self.df_limpio["Ejecucion"] / self.df_limpio["Meta"]
                        )
                        warnings.append(
                            f"Cumplimiento calculado desde Ejecucion/Meta: "
                            f"{nulos_cumplimiento} valores"
                        )
                        logger.info(f"Cumplimiento calculado: {nulos_cumplimiento} valores")
                
                # Convertir a numeric
                self.df_limpio["Cumplimiento"] = pd.to_numeric(
                    self.df_limpio["Cumplimiento"],
                    errors="coerce"
                )
                
                # Normalizar a porcentaje (0-1) si viene como 0-100
                max_val = self.df_limpio["Cumplimiento"].max()
                if pd.notna(max_val) and max_val > 1:
                    self.df_limpio["Cumplimiento_Norm"] = self.df_limpio["Cumplimiento"] / 100
                else:
                    self.df_limpio["Cumplimiento_Norm"] = self.df_limpio["Cumplimiento"]
            elif "Ejecucion" in self.df_limpio.columns and "Meta" in self.df_limpio.columns:
                # Si no existe columna Cumplimiento, crearla
                self.df_limpio["Cumplimiento"] = (
                    self.df_limpio["Ejecucion"] / self.df_limpio["Meta"]
                )
                self.df_limpio["Cumplimiento_Norm"] = self.df_limpio["Cumplimiento"]
                warnings.append("Cumplimiento calculado desde Ejecucion/Meta")
            
            # 4. Normalizar Fecha
            if "Fecha" in self.df_limpio.columns:
                self.df_limpio["Fecha"] = pd.to_datetime(self.df_limpio["Fecha"], errors="coerce")
                self.df_limpio = self.df_limpio.dropna(subset=["Fecha"])
                
                # Extraer componentes de fecha
                self.df_limpio["Año"] = self.df_limpio["Fecha"].dt.year
                self.df_limpio["Mes"] = self.df_limpio["Fecha"].dt.month
                self.df_limpio["Trimestre"] = self.df_limpio["Fecha"].dt.quarter
            
            # 5. Limpiar columna LLAVE si existe
            if "LLAVE" in self.df_limpio.columns:
                self.df_limpio["LLAVE"] = self.df_limpio["LLAVE"].fillna("").astype(str)
            
            final_filas = len(self.df_limpio)
            logger.info(f"Limpieza completada: {inicial_filas} -> {final_filas} filas")
            
            return PreparacionResult(
                exitosa=True,
                dataset_info=self.dataset_info,
                errores=errores,
                warnings=warnings
            )
            
        except Exception as e:
            errores.append(f"Error en limpieza: {str(e)}")
            logger.exception("Error en limpiar_datos")
            return PreparacionResult(
                exitosa=False,
                dataset_info=None,
                errores=errores,
                warnings=warnings
            )

    def generar_features(self) -> PreparacionResult:
        """
        Genera features para modelos predictivos.
        
        Features generadas:
        - Lag features (valor anterior, hace 2 periodos, etc.)
        - Rolling features (media, std, min, max de últimos N periodos)
        - Tendencia (diferencia con periodo anterior)
        - Estacionalidad (mes, trimestre)
        - Indicador de riesgo
        
        Returns:
            Resultado de la generación de features
        """
        errores = []
        warnings = []
        
        if self.df_limpio is None:
            errores.append("No hay datos limpios. Ejecute limpiar_datos() primero.")
            return PreparacionResult(
                exitosa=False,
                dataset_info=None,
                errores=errores,
                warnings=warnings
            )
        
        try:
            logger.info("Generando features para modelado...")
            
            self.df_features = self.df_limpio.copy()
            
            # Features por indicador (agrupados por Id)
            df_features = []
            
            for indicador_id, grupo in self.df_features.groupby("Id"):
                grupo = grupo.sort_values("Fecha")
                
                # Lag features
                for lag in [1, 2, 3]:
                    grupo[f"Cumplimiento_Lag{lag}"] = grupo["Cumplimiento_Norm"].shift(lag)
                
                # Rolling features (últimos 3 y 6 periodos)
                for window in [3, 6]:
                    grupo[f"Cumplimiento_Media_{window}m"] = (
                        grupo["Cumplimiento_Norm"].shift(1).rolling(window=window).mean()
                    )
                    grupo[f"Cumplimiento_Std_{window}m"] = (
                        grupo["Cumplimiento_Norm"].shift(1).rolling(window=window).std()
                    )
                    grupo[f"Cumplimiento_Min_{window}m"] = (
                        grupo["Cumplimiento_Norm"].shift(1).rolling(window=window).min()
                    )
                    grupo[f"Cumplimiento_Max_{window}m"] = (
                        grupo["Cumplimiento_Norm"].shift(1).rolling(window=window).max()
                    )
                
                # Tendencia (diferencia con valor anterior)
                grupo["Tendencia"] = grupo["Cumplimiento_Norm"].diff(1)
                
                # Tendencia de la media móvil
                grupo["Tendencia_Media_3m"] = (
                    grupo["Cumplimiento_Media_3m"].diff(1) if "Cumplimiento_Media_3m" in grupo.columns else np.nan
                )
                
                # Indicador de riesgo (1 si está en zona crítica)
                grupo["Riesgo"] = (
                    (grupo["Cumplimiento_Norm"] < 0.70) | 
                    (grupo["Cumplimiento_Norm"] > 1.20)
                ).astype(int)
                
                # Semaforización
                def clasificar_cumplimiento(val):
                    if pd.isna(val):
                        return "sin_datos"
                    elif val < 0.70:
                        return "critico"
                    elif val < 0.80:
                        return "atencion"
                    elif val <= 1.05:
                        return "normal"
                    elif val <= 1.20:
                        return "atencion"
                    else:
                        return "critico"
                
                grupo["Semaforo"] = grupo["Cumplimiento_Norm"].apply(clasificar_cumplimiento)
                
                df_features.append(grupo)
            
            self.df_features = pd.concat(df_features, ignore_index=True)
            
            # Eliminar filas con NaN en features de lag (primeros periodos)
            filas_inicial = len(self.df_features)
            self.df_features = self.df_features.dropna(
                subset=["Cumplimiento_Lag1", "Cumplimiento_Media_3m"]
            )
            filas_final = len(self.df_features)
            
            if filas_final < filas_inicial:
                warnings.append(
                    f"Eliminadas {filas_inicial - filas_final} filas por falta de "
                    f"historial para calcular features"
                )
            
            logger.info(
                f"Features generadas: {len(self.df_features)} filas, "
                f"{len(self.df_features.columns)} columnas"
            )
            
            return PreparacionResult(
                exitosa=True,
                dataset_info=self.dataset_info,
                errores=errores,
                warnings=warnings
            )
            
        except Exception as e:
            errores.append(f"Error generando features: {str(e)}")
            logger.exception("Error en generar_features")
            return PreparacionResult(
                exitosa=False,
                dataset_info=None,
                errores=errores,
                warnings=warnings
            )

    def guardar_datasets(self) -> List[Path]:
        """
        Guarda los datasets preparados en archivos.
        
        Returns:
            Lista de rutas de archivos guardados
        """
        if self.df_features is None:
            logger.warning("No hay features generados. Ejecute generar_features() primero.")
            return []
        
        rutas = []
        
        # Dataset completo con features
        output_file = self.OUTPUT_PATH / "dataset_features.parquet"
        self.df_features.to_parquet(output_file, index=False)
        rutas.append(output_file)
        logger.info(f"Guardado: {output_file}")
        
        # Dataset solo con columnas útiles para modelado
        columnas_modelado = [
            "Id", "Indicador", "Proceso", "Fecha", "Año", "Mes", "Trimestre",
            "Cumplimiento", "Cumplimiento_Norm",
            "Cumplimiento_Lag1", "Cumplimiento_Lag2", "Cumplimiento_Lag3",
            "Cumplimiento_Media_3m", "Cumplimiento_Media_6m",
            "Cumplimiento_Std_3m", "Cumplimiento_Std_6m",
            "Cumplimiento_Min_3m", "Cumplimiento_Max_3m",
            "Tendencia", "Tendencia_Media_3m",
            "Riesgo", "Semaforo"
        ]
        
        columnas_disponibles = [c for c in columnas_modelado if c in self.df_features.columns]
        df_modelado = self.df_features[columnas_disponibles]
        
        output_modelado = self.OUTPUT_PATH / "dataset_modelado.parquet"
        df_modelado.to_parquet(output_modelado, index=False)
        rutas.append(output_modelado)
        logger.info(f"Guardado: {output_modelado}")
        
        # Dataset resumido por indicador (último periodo)
        df_resumen = (
            self.df_features
            .sort_values("Fecha")
            .groupby("Id")
            .last()
            .reset_index()
        )
        
        output_resumen = self.OUTPUT_PATH / "dataset_resumen.parquet"
        df_resumen.to_parquet(output_resumen, index=False)
        rutas.append(output_resumen)
        logger.info(f"Guardado: {output_resumen}")
        
        # Guardar info del dataset
        info_file = self.OUTPUT_PATH / "dataset_info.json"
        import json
        with open(info_file, "w") as f:
            json.dump({
                "nombre": self.dataset_info.nombre if self.dataset_info else "unknown",
                "filas": len(self.df_features),
                "columnas": len(self.df_features.columns),
                "indicadores_unicos": int(self.df_features["Id"].nunique()),
                "periodo_min": str(self.df_features["Fecha"].min()) if "Fecha" in self.df_features.columns else None,
                "periodo_max": str(self.df_features["Fecha"].max()) if "Fecha" in self.df_features.columns else None,
                "features_generadas": list(self.df_features.columns)
            }, f, indent=2)
        rutas.append(info_file)
        
        return rutas

    def ejecutar_pipeline_completo(self) -> Tuple[bool, List[Path]]:
        """
        Ejecuta el pipeline completo de preparación.
        
        Returns:
            Tupla (exitosa, lista de archivos guardados)
        """
        logger.info("=" * 60)
        logger.info("INICIANDO PIPELINE DE PREPARACIÓN DE DATOS")
        logger.info("=" * 60)
        
        # 1. Cargar
        resultado = self.cargar_datos()
        if not resultado.exitosa:
            logger.error("Falló carga de datos")
            return False, []
        
        # 2. Limpiar
        resultado = self.limpiar_datos()
        if not resultado.exitosa:
            logger.error("Falló limpieza de datos")
            return False, []
        
        for w in resultado.warnings:
            logger.warning(f"  {w}")
        
        # 3. Generar features
        resultado = self.generar_features()
        if not resultado.exitosa:
            logger.error("Falló generación de features")
            return False, []
        
        for w in resultado.warnings:
            logger.warning(f"  {w}")
        
        # 4. Guardar
        rutas = self.guardar_datasets()
        
        logger.info("=" * 60)
        logger.info("PIPELINE DE PREPARACIÓN COMPLETADO")
        logger.info(f"Archivos generados: {len(rutas)}")
        logger.info("=" * 60)
        
        return True, rutas


# =============================================================================
# EJECUCIÓN
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    # Ejecutar pipeline
    preparator = DataPreparator()
    exitosa, rutas = preparator.ejecutar_pipeline_completo()
    
    if exitosa:
        print(f"\n✅ Pipeline completado. Archivos generados:")
        for ruta in rutas:
            print(f"  - {ruta}")
    else:
        print("\n❌ Pipeline falló")
