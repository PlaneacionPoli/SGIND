"""
analytics/predictor.py
Modelos predictivos para indicadores - Fase 4.

Responsabilidades:
- Predicción de cumplimiento proyectado
- Predicción de riesgo (deserción, bajo rendimiento)
- Simulación de escenarios
- Recomendaciones automáticas basadas en datos
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTES
# =============================================================================

MODELOS_PATH = Path("data/output/analytics/modelos")
PREDICCIONES_PATH = Path("data/output/analytics/predicciones")
MODELOS_PATH.mkdir(parents=True, exist_ok=True)
PREDICCIONES_PATH.mkdir(parents=True, exist_ok=True)


# =============================================================================
# ESTRUCTURAS DE DATOS
# =============================================================================

@dataclass
class MetricasModelo:
    """Métricas de evaluación de un modelo."""
    nombre: str
    mae: float = 0.0  # Mean Absolute Error
    rmse: float = 0.0  # Root Mean Square Error
    mape: float = 0.0  # Mean Absolute Percentage Error
    r2: float = 0.0  # R-squared
    exactitud: float = 0.0  # Para clasificación


@dataclass
class Prediccion:
    """Resultado de una predicción."""
    indicador_id: str
    indicador_nombre: str
    periodo_predicho: str
    valor_predicho: float
    valor_predicho_norm: float
    intervalo_confianza: Tuple[float, float]
    nivel_riesgo: str  # critico, atencion, normal
    semaforo_predicho: str
    confianza_modelo: float  # 0-1
    factores_influyentes: List[str] = field(default_factory=list)


@dataclass
class EscenarioSimulado:
    """Resultado de una simulación de escenario."""
    nombre: str
    descripcion: str
    indicadores_afectados: List[str]
    resultados: Dict[str, float]
    impacto_total: float
    probabilidad: float = 0.5


@dataclass
class Recomendacion:
    """Recomendación generada por el sistema."""
    indicador_id: str
    indicador_nombre: str
    tipo: str  # prevencion, optimizacion, investigacion
    prioridad: str  # alta, media, baja
    titulo: str
    descripcion: str
    acciones_sugeridas: List[str]
    evidencia: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# MODELO PREDICTIVO (IMPLEMENTACIÓN SIMPLIFICADA)
# =============================================================================

class ModeloPredictivo:
    """
    Modelo predictivo simplificado para predicción de cumplimiento.
    
    NOTA: Esta es una implementación de referencia que usa métodos estadísticos.
    Para producción, considerar usar scikit-learn, TensorFlow, etc.
    """

    def __init__(self):
        self.entrenado = False
        self.parametros = {}
        self.metrica = None

    def entrenar(self, df: pd.DataFrame, target_col: str = "Cumplimiento_Norm") -> MetricasModelo:
        """
        Entrena el modelo con datos históricos.
        
        Args:
            df: DataFrame con features
            target_col: Columna objetivo
            
        Returns:
            Métricas del modelo
        """
        try:
            # Features para entrenamiento
            feature_cols = [
                "Cumplimiento_Lag1", "Cumplimiento_Lag2", "Cumplimiento_Lag3",
                "Cumplimiento_Media_3m", "Tendencia"
            ]
            
            # Filtrar filas válidas
            df_train = df.dropna(subset=feature_cols + [target_col])
            
            if len(df_train) < 10:
                logger.warning("Datos insuficientes para entrenar modelo")
                return MetricasModelo(nombre="Media Historica")
            
            X = df_train[feature_cols].values
            y = df_train[target_col].values
            
            # Modelo simple: media ponderada de lags
            # Pesos: más peso a periodos recientes
            pesos = np.array([0.5, 0.3, 0.2])
            
            # Calcular predicción como media ponderada
            predicciones = (
                pesos[0] * X[:, 0] +  # Lag1
                pesos[1] * X[:, 1] +  # Lag2
                pesos[2] * X[:, 2]    # Lag3
            )
            
            # Ajustar con tendencia
            tendencia_peso = 0.1
            predicciones = predicciones + tendencia_peso * X[:, 4]
            
            # Guardar parámetros
            self.parametros = {
                "pesos_lags": pesos.tolist(),
                "tendencia_peso": tendencia_peso,
                "n_entrenamiento": len(df_train)
            }
            
            # Calcular métricas
            errores = np.abs(y - predicciones)
            mae = float(np.mean(errores))
            rmse = float(np.sqrt(np.mean(errores ** 2)))
            mape = float(np.mean(errores / np.abs(y)) * 100) if np.any(y != 0) else 0
            r2 = float(1 - np.sum((y - predicciones) ** 2) / np.sum((y - np.mean(y)) ** 2))
            
            self.metrica = MetricasModelo(
                nombre="Media Ponderada de Lags",
                mae=mae,
                rmse=rmse,
                mape=mape,
                r2=r2
            )
            
            self.entrenado = True
            
            logger.info(f"Modelo entrenado: MAE={mae:.4f}, R2={r2:.4f}")
            
            return self.metrica
            
        except Exception as e:
            logger.error(f"Error entrenando modelo: {e}")
            return MetricasModelo(nombre="Error")

    def predecir(self, df: pd.DataFrame) -> List[Prediccion]:
        """
        Genera predicciones para el siguiente periodo.
        
        Args:
            df: DataFrame con datos históricos (features)
            
        Returns:
            Lista de predicciones por indicador
        """
        if not self.entrenado:
            logger.warning("Modelo no entrenado. Ejecutar entrenar() primero.")
            return []
        
        predicciones = []
        
        # Obtener último periodo de cada indicador
        df_ultimo = df.sort_values("Fecha").groupby("Id").last().reset_index()
        
        feature_cols = [
            "Cumplimiento_Lag1", "Cumplimiento_Lag2", "Cumplimiento_Lag3",
            "Cumplimiento_Media_3m", "Tendencia"
        ]
        
        pesos = np.array(self.parametros.get("pesos_lags", [0.5, 0.3, 0.2]))
        tendencia_peso = self.parametros.get("tendencia_peso", 0.1)
        
        for _, row in df_ultimo.iterrows():
            try:
                # Verificar que tenemos features
                if any(pd.isna(row.get(f)) for f in feature_cols):
                    continue
                
                # Calcular predicción
                X = row[feature_cols].values.astype(float)
                prediccion = (
                    pesos[0] * X[0] +
                    pesos[1] * X[1] +
                    pesos[2] * X[2] +
                    tendencia_peso * X[4]
                )
                
                # Normalizar si es necesario
                if prediccion > 1:
                    prediccion_norm = prediccion / 100
                else:
                    prediccion_norm = prediccion
                
                # Intervalo de confianza (aproximado)
                margen = 0.10  # 10% de margen
                intervalo = (
                    max(0, prediccion_norm - margen),
                    min(1.5, prediccion_norm + margen)
                )
                
                # Determinar nivel de riesgo
                if prediccion_norm < 0.70 or prediccion_norm > 1.20:
                    nivel_riesgo = "critico"
                elif prediccion_norm < 0.80 or prediccion_norm > 1.05:
                    nivel_riesgo = "atencion"
                else:
                    nivel_riesgo = "normal"
                
                # Semaforización predicha
                if prediccion_norm < 0.70:
                    semaforo = "critico"
                elif prediccion_norm < 0.80:
                    semaforo = "atencion"
                elif prediccion_norm <= 1.05:
                    semaforo = "normal"
                elif prediccion_norm <= 1.20:
                    semaforo = "atencion"
                else:
                    semaforo = "critico"
                
                # Calcular confianza basada en variabilidad histórica
                variabilidad = row.get("Cumplimiento_Std_3m", 0.1)
                confianza = max(0.5, min(0.95, 1 - variabilidad * 2))
                
                predicciones.append(Prediccion(
                    indicador_id=str(row["Id"]),
                    indicador_nombre=str(row.get("Indicador", "Sin nombre")),
                    periodo_predicho=self._siguiente_periodo(str(row.get("Fecha", ""))),
                    valor_predicho=prediccion * 100 if prediccion > 1 else prediccion,
                    valor_predicho_norm=prediccion_norm,
                    intervalo_confianza=intervalo,
                    nivel_riesgo=nivel_riesgo,
                    semaforo_predicho=semaforo,
                    confianza_modelo=confianza,
                    factores_influyentes=["tendencia_historica", "variabilidad_3m"]
                ))
                
            except Exception as e:
                logger.warning(f"Error prediciendo para {row.get('Id')}: {e}")
                continue
        
        logger.info(f"Predicciones generadas: {len(predicciones)}")
        return predicciones

    def _siguiente_periodo(self, fecha_str: str) -> str:
        """Calcula el siguiente periodo."""
        try:
            fecha = pd.to_datetime(fecha_str)
            siguiente = fecha + pd.DateOffset(months=1)
            return siguiente.strftime("%Y-%m")
        except:
            return "N/A"


# =============================================================================
# SIMULADOR DE ESCENARIOS
# =============================================================================

class SimuladorEscenarios:
    """
    Simulador de escenarios para soporte a decisiones.
    
    Permite evaluar el impacto de diferentes acciones
    sobre el cumplimiento de indicadores.
    """

    # Escenarios predefinidos
    ESCENARIOS = {
        "mejor_caso": {
            "descripcion": "Mejora del 10% en ejecución",
            "factor": 1.10
        },
        "peor_caso": {
            "descripcion": "Disminución del 10% en ejecución",
            "factor": 0.90
        },
        "meta_optimista": {
            "descripcion": "Cumplimiento de meta al 100%",
            "factor": 1.0
        },
        "tendencia_continua": {
            "descripcion": "Continúa tendencia actual",
            "factor": None  # Se calcula dinámicamente
        }
    }

    def simular(
        self,
        df: pd.DataFrame,
        escenario: str = "mejor_caso",
        indicadores_seleccionados: Optional[List[str]] = None
    ) -> List[EscenarioSimulado]:
        """
        Simula un escenario para indicadores seleccionados.
        
        Args:
            df: DataFrame con datos históricos
            escenario: Nombre del escenario
            indicadores_seleccionados: Lista de IDs de indicadores (None = todos)
            
        Returns:
            Lista de escenarios simulados
        """
        if escenario not in self.ESCENARIOS:
            logger.warning(f"Escenario '{escenario}' no reconocido")
            return []
        
        config = self.ESCENARIOS[escenario]
        
        # Filtrar indicadores
        if indicadores_seleccionados:
            df_sim = df[df["Id"].isin(indicadores_seleccionados)]
        else:
            df_sim = df
        
        # Obtener último valor de cada indicador
        df_ultimo = df_sim.sort_values("Fecha").groupby("Id").last().reset_index()
        
        resultados = []
        
        for _, row in df_ultimo.iterrows():
            valor_actual = row.get("Cumplimiento_Norm", 0)
            
            if config["factor"] is None:
                # Usar tendencia
                tendencia = row.get("Tendencia", 0)
                valor_simulado = valor_actual + tendencia
            else:
                valor_simulado = valor_actual * config["factor"]
            
            impacto = valor_simulado - valor_actual
            impacto_pct = (impacto / valor_actual * 100) if valor_actual != 0 else 0
            
            resultados.append(EscenarioSimulado(
                nombre=escenario,
                descripcion=config["descripcion"],
                indicadores_afectados=[str(row["Id"])],
                resultados={str(row["Id"]): valor_simulado},
                impacto_total=impacto_pct,
                probabilidad=0.7 if escenario == "mejor_caso" else 0.5
            ))
        
        logger.info(f"Simulación '{escenario}': {len(resultados)} indicadores")
        return resultados

    def simular_comparativo(
        self,
        df: pd.DataFrame,
        indicadores_seleccionados: Optional[List[str]] = None
    ) -> Dict[str, List[EscenarioSimulado]]:
        """
        Simula múltiples escenarios para comparación.
        
        Returns:
            Diccionario de escenarios por nombre
        """
        resultados = {}
        
        for escenario_nombre in self.ESCENARIOS.keys():
            resultados[escenario_nombre] = self.simular(
                df,
                escenario=escenario_nombre,
                indicadores_seleccionados=indicadores_seleccionados
            )
        
        return resultados


# =============================================================================
# GENERADOR DE RECOMENDACIONES
# =============================================================================

class GeneradorRecomendaciones:
    """
    Genera recomendaciones automáticas basadas en análisis de datos.
    """

    def generar(
        self,
        df: pd.DataFrame,
        predicciones: List[Prediccion],
        top_n: int = 10
    ) -> List[Recomendacion]:
        """
        Genera recomendaciones basadas en riesgos y tendencias.
        
        Args:
            df: DataFrame con datos históricos
            predicciones: Lista de predicciones
            top_n: Número máximo de recomendaciones
            
        Returns:
            Lista de recomendaciones ordenadas por prioridad
        """
        recomendaciones = []
        
        # 1. Recomendaciones basadas en predicciones de riesgo crítico
        predicciones_riesgo = sorted(
            [p for p in predicciones if p.nivel_riesgo == "critico"],
            key=lambda x: x.confianza_modelo,
            reverse=True
        )
        
        for pred in predicciones_riesgo[:5]:
            recomendaciones.append(Recomendacion(
                indicador_id=pred.indicador_id,
                indicador_nombre=pred.indicador_nombre,
                tipo="prevencion",
                prioridad="alta",
                titulo=f"Riesgo crítico predicho: {pred.indicador_nombre}",
                descripcion=(
                    f"Se predice que el indicador '{pred.indicador_nombre}' "
                    f"estaré en {pred.semaforo_predicho.upper()} ({pred.valor_predicho:.1%}) "
                    f"en el próximo periodo con {pred.confianza_modelo:.0%} de confianza."
                ),
                acciones_sugeridas=[
                    "Revisar causas raíz del bajo rendimiento",
                    "Escalar a nivel directivo",
                    "Definir plan de acción correctiva inmediata"
                ],
                evidencia={
                    "prediccion": pred.valor_predicho,
                    "confianza": pred.confianza_modelo,
                    "intervalo": pred.intervalo_confianza
                }
            ))
        
        # 2. Recomendaciones basadas en tendencia descendente
        df_ultimo = df.sort_values("Fecha").groupby("Id").last().reset_index()
        
        tendencia_desc = df_ultimo[
            (df_ultimo.get("Tendencia", 0) < -0.05) &
            (df_ultimo.get("Cumplimiento_Norm", 1) < 0.90)
        ]
        
        for _, row in tendencia_desc.iterrows():
            if len(recomendaciones) >= top_n:
                break
                
            recomendaciones.append(Recomendacion(
                indicador_id=str(row["Id"]),
                indicador_nombre=str(row.get("Indicador", "Sin nombre")),
                tipo="optimizacion",
                prioridad="media",
                titulo=f"Tendencia descendente: {row.get('Indicador', 'Sin nombre')}",
                descripcion=(
                    f"El indicador muestra una tendencia descendente de "
                    f"{row.get('Tendencia', 0):.1%}. Es necesario investigar "
                    f"las causas y tomar acciones preventivas."
                ),
                acciones_sugeridas=[
                    "Analizar factores que han influido en la caída",
                    "Comparar con periodos similares anteriores",
                    "Definir acciones correctivas"
                ],
                evidencia={
                    "tendencia": row.get("Tendencia", 0),
                    "cumplimiento_actual": row.get("Cumplimiento_Norm", 0)
                }
            ))
        
        # 3. Recomendaciones para indicadores en zona de atención
        predicciones_atencion = sorted(
            [p for p in predicciones if p.nivel_riesgo == "atencion"],
            key=lambda x: x.valor_predicho_norm,
            reverse=True
        )
        
        for pred in predicciones_atencion[:3]:
            if len(recomendaciones) >= top_n:
                break
                
            recomendaciones.append(Recomendacion(
                indicador_id=pred.indicador_id,
                indicador_nombre=pred.indicador_nombre,
                tipo="investigacion",
                prioridad="baja",
                titulo=f"Monitorear: {pred.indicador_nombre}",
                descripcion=(
                    f"El indicador '{pred.indicador_nombre}' se encuentra en zona "
                    f"de atención con predicción de {pred.valor_predicho:.1%}. "
                    f"Se recomienda seguimiento cercano."
                ),
                acciones_sugeridas=[
                    "Incrementar frecuencia de monitoreo",
                    "Documentar cualquier cambio en el proceso",
                    "Preparar acciones correctivas si es necesario"
                ],
                evidencia={
                    "prediccion": pred.valor_predicho,
                    "confianza": pred.confianza_modelo
                }
            ))
        
        # Ordenar por prioridad
        prioridad_order = {"alta": 0, "media": 1, "baja": 2}
        recomendaciones = sorted(
            recomendaciones,
            key=lambda r: prioridad_order.get(r.prioridad, 3)
        )
        
        logger.info(f"Generadas {len(recomendaciones)} recomendaciones")
        return recomendaciones[:top_n]


# =============================================================================
# ORQUESTADOR DE ANALÍTICA
# =============================================================================

class AnaliticaOrchestrator:
    """
    Orquestador de analítica predictiva.
    
    Coordina la preparación de datos, entrenamiento de modelos,
    predicciones, simulaciones y generación de recomendaciones.
    """

    def __init__(self):
        self.preparator = None
        self.modelo = ModeloPredictivo()
        self.simulador = SimuladorEscenarios()
        self.generador = GeneradorRecomendaciones()
        
        self.df_procesado: Optional[pd.DataFrame] = None
        self.predicciones: List[Prediccion] = []
        self.recomendaciones: List[Recomendacion] = []
        
        logger.info("AnaliticaOrchestrator inicializado")

    def ejecutar_pipeline_completo(self) -> bool:
        """
        Ejecuta el pipeline completo de analítica.
        
        Returns:
            True si fue exitoso
        """
        try:
            # 1. Cargar y preparar datos
            logger.info("=" * 60)
            logger.info("PASO 1: PREPARACIÓN DE DATOS")
            logger.info("=" * 60)
            
            from .data_preparator import DataPreparator
            
            self.preparator = DataPreparator()
            exitosa, rutas = self.preparator.ejecutar_pipeline_completo()
            
            if not exitosa:
                logger.error("Falló preparación de datos")
                return False
            
            self.df_procesado = pd.read_parquet(
                Path("data/output/analytics/dataset_modelado.parquet")
            )
            
            # 2. Entrenar modelo
            logger.info("=" * 60)
            logger.info("PASO 2: ENTRENAMIENTO DE MODELO")
            logger.info("=" * 60)
            
            metricas = self.modelo.entrenar(self.df_procesado)
            logger.info(f"Métricas: MAE={metricas.mae:.4f}, R2={metricas.r2:.4f}")
            
            # 3. Generar predicciones
            logger.info("=" * 60)
            logger.info("PASO 3: PREDICCIONES")
            logger.info("=" * 60)
            
            self.predicciones = self.modelo.predecir(self.df_procesado)
            logger.info(f"Predicciones generadas: {len(self.predicciones)}")
            
            # 4. Simular escenarios
            logger.info("=" * 60)
            logger.info("PASO 4: SIMULACIÓN DE ESCENARIOS")
            logger.info("=" * 60)
            
            escenarios = self.simulador.simular_comparativo(self.df_procesado)
            for nombre, lista in escenarios.items():
                logger.info(f"  {nombre}: {len(lista)} simulaciones")
            
            # 5. Generar recomendaciones
            logger.info("=" * 60)
            logger.info("PASO 5: RECOMENDACIONES")
            logger.info("=" * 60)
            
            self.recomendaciones = self.generador.generar(
                self.df_procesado,
                self.predicciones
            )
            logger.info(f"Recomendaciones generadas: {len(self.recomendaciones)}")
            
            # 6. Guardar resultados
            self._guardar_resultados()
            
            logger.info("=" * 60)
            logger.info("✅ PIPELINE DE ANALÍTICA COMPLETADO")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.exception("Error en pipeline de analítica")
            return False

    def _guardar_resultados(self):
        """Guarda los resultados en archivos."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Guardar predicciones
        if self.predicciones:
            df_pred = pd.DataFrame([
                {
                    "indicador_id": p.indicador_id,
                    "indicador_nombre": p.indicador_nombre,
                    "periodo_predicho": p.periodo_predicho,
                    "valor_predicho": p.valor_predicho,
                    "valor_predicho_norm": p.valor_predicho_norm,
                    "intervalo_bajo": p.intervalo_confianza[0],
                    "intervalo_alto": p.intervalo_confianza[1],
                    "nivel_riesgo": p.nivel_riesgo,
                    "semaforo_predicho": p.semaforo_predicho,
                    "confianza_modelo": p.confianza_modelo
                }
                for p in self.predicciones
            ])
            
            output_pred = PREDICCIONES_PATH / f"predicciones_{timestamp}.parquet"
            df_pred.to_parquet(output_pred, index=False)
            logger.info(f"Predicciones guardadas: {output_pred}")
        
        # Guardar recomendaciones
        if self.recomendaciones:
            df_rec = pd.DataFrame([
                {
                    "indicador_id": r.indicador_id,
                    "indicador_nombre": r.indicador_nombre,
                    "tipo": r.tipo,
                    "prioridad": r.prioridad,
                    "titulo": r.titulo,
                    "descripcion": r.descripcion,
                    "acciones_sugeridas": "; ".join(r.acciones_sugeridas)
                }
                for r in self.recomendaciones
            ])
            
            output_rec = PREDICCIONES_PATH / f"recomendaciones_{timestamp}.parquet"
            df_rec.to_parquet(output_rec, index=False)
            logger.info(f"Recomendaciones guardadas: {output_rec}")
        
        # Guardar resumen JSON
        resumen = {
            "timestamp": timestamp,
            "total_predicciones": len(self.predicciones),
            "total_recomendaciones": len(self.recomendaciones),
            "predicciones_riesgo_critico": sum(
                1 for p in self.predicciones if p.nivel_riesgo == "critico"
            ),
            "predicciones_riesgo_atencion": sum(
                1 for p in self.predicciones if p.nivel_riesgo == "atencion"
            ),
            "recomendaciones_alta_prioridad": sum(
                1 for r in self.recomendaciones if r.prioridad == "alta"
            )
        }
        
        output_resumen = PREDICCIONES_PATH / f"resumen_{timestamp}.json"
        with open(output_resumen, "w") as f:
            json.dump(resumen, f, indent=2)
        
        logger.info(f"Resumen guardado: {output_resumen}")


# =============================================================================
# EJECUCIÓN
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    # Ejecutar pipeline
    orchestrator = AnaliticaOrchestrator()
    exitosa = orchestrator.ejecutar_pipeline_completo()
    
    if exitosa:
        print("\n" + "=" * 60)
        print("✅ ANALÍTICA PREDICTIVA COMPLETADA")
        print("=" * 60)
        
        print(f"\n📊 Predicciones: {len(orchestrator.predicciones)}")
        criticas = [p for p in orchestrator.predicciones if p.nivel_riesgo == "critico"]
        if criticas:
            print(f"\n🔴 EN RIESGO CRÍTICO ({len(criticas)}):")
            for p in criticas[:5]:
                print(f"   - {p.indicador_nombre}: {p.valor_predicho:.1%}")
        
        print(f"\n💡 Recomendaciones: {len(orchestrator.recomendaciones)}")
        alta_prioridad = [r for r in orchestrator.recomendaciones if r.prioridad == "alta"]
        if alta_prioridad:
            print(f"\n⚡ ALTA PRIORIDAD ({len(alta_prioridad)}):")
            for r in alta_prioridad[:3]:
                print(f"   - {r.titulo}")
    else:
        print("\n❌ Pipeline de analítica falló")
