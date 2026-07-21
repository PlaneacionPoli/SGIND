"""
consolidation/core/rules_engine.py
Motor de reglas de negocio y alertas - Fase 2.

Responsabilidades:
- Definir y aplicar reglas de negocio por indicador
- Generar alertas automáticas (semaforización, umbrales)
- Detectar anomalías y variaciones abruptas
- Soportar personalización de reglas por perfil
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

import pandas as pd

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS Y CONSTANTES
# =============================================================================

class NivelAlerta(str, Enum):
    """Niveles de alerta."""
    CRITICO = "critico"
    ATENCION = "atencion"
    NORMAL = "normal"
    INFO = "info"


class TipoRegla(str, Enum):
    """Tipos de reglas de negocio."""
    RANGO_CUMPLIMIENTO = "rango_cumplimiento"
    VARIACION = "variacion"
    TENDENCIA = "tendencia"
    ACTUALIZACION = "actualizacion"
    DUPLICADO = "duplicado"
    NULOS = "nulos"
    CUSTOM = "custom"


# Configuración estándar de semaforización
SEMAFORO_STANDARD = {
    "critico_low": 0.70,      # < 70% es crítico
    "atencion_low": 0.80,     # 70-80% requiere atención
    "normal_low": 0.80,       # 80-100% normal
    "normal_high": 1.05,      # 80-105% normal
    "atencion_high": 1.20,   # 105-120% requiere atención
    "critico_high": 1.20,    # > 120% es crítico
}


# =============================================================================
# ESTRUCTURAS DE DATOS
# =============================================================================

@dataclass
class Regla:
    """Define una regla de negocio individual."""
    id: str
    nombre: str
    tipo: TipoRegla
    descripcion: str
    configuracion: Dict[str, Any]
    habilitada: bool = True
    prioridad: int = 1  # 1 = más alta


@dataclass
class ResultadoRegla:
    """Resultado de evaluar una regla sobre un registro."""
    regla_id: str
    regla_nombre: str
    registro_id: str
    campo: str
    nivel: NivelAlerta
    mensaje: str
    valor_encontrado: Any
    valor_esperado: Any
    detalles: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alerta:
    """Alerta generada por el motor de reglas."""
    id: str
    timestamp: datetime
    nivel: NivelAlerta
    indicador_id: str
    indicador_nombre: str
    mensaje: str
    resultado_regla: ResultadoRegla
    accionable: bool = True
    acknowledged: bool = False


# =============================================================================
# MOTOR DE REGLAS
# =============================================================================

class RulesEngine:
    """
    Motor de reglas de negocio y alertas.
    
    Aplica reglas configuradas sobre DataFrames de indicadores
    y genera alertas automáticas.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa el motor de reglas.
        
        Args:
            config: Configuración opcional con reglas customizadas
        """
        self.config = config or {}
        self.reglas: Dict[str, Regla] = {}
        self.alertas: List[Alerta] = []
        self._inicializar_reglas_default()
    
    def _inicializar_reglas_default(self):
        """Inicializa las reglas por defecto."""
        
        # Regla 1: Semaforización de cumplimiento
        self.agregar_regla(Regla(
            id="semaforizacion",
            nombre="Semaforización de Cumplimiento",
            tipo=TipoRegla.RANGO_CUMPLIMIENTO,
            descripcion="Clasifica el cumplimiento en niveles según rangos predefinidos",
            configuracion={
                "campo": "Cumplimiento",
                "rangos": SEMAFORO_STANDARD.copy()
            },
            prioridad=1
        ))
        
        # Regla 2: Detección de variación abrupta
        self.agregar_regla(Regla(
            id="variacion_abrupta",
            nombre="Variación Arupta",
            tipo=TipoRegla.VARIACION,
            descripcion="Detecta cambios bruscos en el cumplimiento",
            configuracion={
                "campo": "Cumplimiento",
                "umbral_variacion": 0.20,  # 20% de cambio
                "comparar": "anterior"  # vs periodo anterior
            },
            prioridad=2
        ))
        
        # Regla 3: Tendencia descendente
        self.agregar_regla(Regla(
            id="tendencia_descendente",
            nombre="Tendencia Descendente",
            tipo=TipoRegla.TENDENCIA,
            descripcion="Detecta tendencia negativa en últimos 3 periodos",
            configuracion={
                "campo": "Cumplimiento",
                "periodos": 3,
                "sentido": "descendente"
            },
            prioridad=3
        ))
        
        # Regla 4: Falta de actualización
        self.agregar_regla(Regla(
            id="falta_actualizacion",
            nombre="Falta de Actualización",
            tipo=TipoRegla.ACTUALIZACION,
            descripcion="Alerta si un indicador no se ha actualizado en el periodo esperado",
            configuracion={
                "campo": "Fecha",
                "dias_esperado": 30  # Mensual
            },
            prioridad=2
        ))
        
        # Regla 5: Nulos excesivos
        self.agregar_regla(Regla(
            id="nulos_excesivos",
            nombre="Nulos Excesivos",
            tipo=TipoRegla.NULOS,
            descripcion="Detecta porcentaje alto de valores nulos",
            configuracion={
                "campo": "Ejecucion",
                "umbral_nulos": 0.10  # 10%
            },
            prioridad=3
        ))
        
        logger.info(f"Inicializadas {len(self.reglas)} reglas por defecto")
    
    def agregar_regla(self, regla: Regla):
        """Agrega una regla al motor."""
        self.reglas[regla.id] = regla
        logger.info(f"Regla agregada: {regla.id} - {regla.nombre}")
    
    def eliminar_regla(self, regla_id: str):
        """Elimina una regla del motor."""
        if regla_id in self.reglas:
            del self.reglas[regla_id]
            logger.info(f"Regla eliminada: {regla_id}")
    
    def obtener_regla(self, regla_id: str) -> Optional[Regla]:
        """Obtiene una regla por su ID."""
        return self.reglas.get(regla_id)
    
    def listar_reglas(self) -> List[Regla]:
        """Lista todas las reglas ordenadas por prioridad."""
        return sorted(self.reglas.values(), key=lambda r: r.prioridad)
    
    def evaluar_semaforizacion(
        self,
        df: pd.DataFrame,
        regla: Regla
    ) -> List[ResultadoRegla]:
        """Evalúa la regla de semaforización."""
        resultados = []
        campo = regla.configuracion["campo"]
        rangos = regla.configuracion["rangos"]
        
        if campo not in df.columns:
            return resultados
        
        for idx, row in df.iterrows():
            valor = row.get(campo)
            if pd.isna(valor):
                continue
            
            # Normalizar valor (puede venir como 0.85 o 85)
            if valor > 1:
                valor_norm = valor / 100
            else:
                valor_norm = valor
            
            # Clasificar
            if valor_norm < rangos["critico_low"] or valor_norm > rangos["critico_high"]:
                nivel = NivelAlerta.CRITICO
            elif valor_norm < rangos["atencion_low"] or valor_norm > rangos["atencion_high"]:
                nivel = NivelAlerta.ATENCION
            else:
                nivel = NivelAlerta.NORMAL
            
            resultados.append(ResultadoRegla(
                regla_id=regla.id,
                regla_nombre=regla.nombre,
                registro_id=str(row.get("Id", idx)),
                campo=campo,
                nivel=nivel,
                mensaje=f"Cumplimiento {valor:.1%}: {nivel.value}",
                valor_encontrado=valor,
                valor_esperado=f"{rangos['atencion_low']:.0%} - {rangos['atencion_high']:.0%}",
                detalles={"valor_normalizado": valor_norm}
            ))
        
        return resultados
    
    def evaluar_variacion_abrupta(
        self,
        df: pd.DataFrame,
        regla: Regla
    ) -> List[ResultadoRegla]:
        """Evalúa la regla de variación abrupta."""
        resultados = []
        
        if len(df) < 2:
            return resultados
        
        # Ordenar por fecha
        if "Fecha" in df.columns:
            df_sorted = df.sort_values("Fecha")
        else:
            df_sorted = df
        
        campo = regla.configuracion["campo"]
        umbral = regla.configuracion["umbral_variacion"]
        
        for i in range(1, len(df_sorted)):
            row_prev = df_sorted.iloc[i - 1]
            row_curr = df_sorted.iloc[i]
            
            val_prev = row_prev.get(campo)
            val_curr = row_curr.get(campo)
            
            if pd.isna(val_prev) or pd.isna(val_curr):
                continue
            
            # Normalizar
            if val_prev > 1:
                val_prev = val_prev / 100
            if val_curr > 1:
                val_curr = val_curr / 100
            
            variacion = abs(val_curr - val_prev)
            
            if variacion > umbral:
                nivel = NivelAlerta.ATENCION if variacion < 0.30 else NivelAlerta.CRITICO
                
                resultados.append(ResultadoRegla(
                    regla_id=regla.id,
                    regla_nombre=regla.nombre,
                    registro_id=str(row_curr.get("Id", i)),
                    campo=campo,
                    nivel=nivel,
                    mensaje=f"Variación de {variacion:.1%} detectada",
                    valor_encontrado=val_curr,
                    valor_esperado=f"±{umbral:.0%} del anterior",
                    detalles={
                        "valor_anterior": val_prev,
                        "variacion": variacion
                    }
                ))
        
        return resultados
    
    def evaluar_nulos_excesivos(
        self,
        df: pd.DataFrame,
        regla: Regla
    ) -> List[ResultadoRegla]:
        """Evalúa la regla de nulos excesivos."""
        resultados = []
        campo = regla.configuracion["campo"]
        umbral = regla.configuracion["umbral_nulos"]
        
        if campo not in df.columns:
            return resultados
        
        total = len(df)
        nulos = df[campo].isna().sum()
        porcentaje_nulos = nulos / total if total > 0 else 0
        
        if porcentaje_nulos > umbral:
            nivel = NivelAlerta.ATENCION if porcentaje_nulos < 0.30 else NivelAlerta.CRITICO
            
            resultados.append(ResultadoRegla(
                regla_id=regla.id,
                regla_nombre=regla.nombre,
                registro_id="GLOBAL",
                campo=campo,
                nivel=nivel,
                mensaje=f"{nulos} valores nulos ({porcentaje_nulos:.1%})",
                valor_encontrado=nulos,
                valor_esperado=f"Máximo {umbral:.0%}",
                detalles={
                    "total_registros": total,
                    "porcentaje": porcentaje_nulos
                }
            ))
        
        return resultados
    
    def evaluar_regla(
        self,
        df: pd.DataFrame,
        regla: Regla
    ) -> List[ResultadoRegla]:
        """
        Evalúa una regla específica sobre un DataFrame.
        
        Args:
            df: DataFrame con los datos
            regla: Regla a evaluar
            
        Returns:
            Lista de resultados de la evaluación
        """
        if not regla.habilitada:
            return []
        
        try:
            if regla.tipo == TipoRegla.RANGO_CUMPLIMIENTO:
                return self.evaluar_semaforizacion(df, regla)
            
            elif regla.tipo == TipoRegla.VARIACION:
                return self.evaluar_variacion_abrupta(df, regla)
            
            elif regla.tipo == TipoRegla.NULOS:
                return self.evaluar_nulos_excesivos(df, regla)
            
            elif regla.tipo == TipoRegla.TENDENCIA:
                # Placeholder para tendencia - requiere más contexto
                return []
            
            elif regla.tipo == TipoRegla.ACTUALIZACION:
                # Placeholder para actualización - requiere lógica de fechas
                return []
            
            else:
                logger.warning(f"Tipo de regla no soportado: {regla.tipo}")
                return []
                
        except Exception as e:
            logger.error(f"Error evaluando regla {regla.id}: {e}")
            return []
    
    def evaluar_todo(self, df: pd.DataFrame) -> List[ResultadoRegla]:
        """
        Evalúa todas las reglas habilitadas sobre un DataFrame.
        
        Args:
            df: DataFrame con los datos
            
        Returns:
            Lista consolidada de resultados
        """
        todos_resultados = []
        
        for regla in self.listar_reglas():
            if not regla.habilitada:
                continue
            
            resultados = self.evaluar_regla(df, regla)
            todos_resultados.extend(resultados)
        
        logger.info(f"Evaluadas {len(todos_resultados)} reglas, {len([r for r in todos_resultados if r.nivel != NivelAlerta.NORMAL])} alertas generadas")
        
        return todos_resultados
    
    def generar_alertas(self, resultados: List[ResultadoRegla]) -> List[Alerta]:
        """
        Convierte resultados de reglas en alertas formales.
        
        Args:
            resultados: Resultados de evaluar reglas
            
        Returns:
            Lista de alertas generadas
        """
        alertas = []
        
        for i, resultado in enumerate(resultados):
            if resultado.nivel in [NivelAlerta.CRITICO, NivelAlerta.ATENCION]:
                alertas.append(Alerta(
                    id=f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{i}",
                    timestamp=datetime.now(),
                    nivel=resultado.nivel,
                    indicador_id=resultado.registro_id,
                    indicador_nombre=resultado.registro_id,  # TODO: enriquecer con nombre
                    mensaje=resultado.mensaje,
                    resultado_regla=resultado,
                    accionable=True
                ))
        
        self.alertas.extend(alertas)
        return alertas
    
    def obtener_alertas(
        self,
        nivel: Optional[NivelAlerta] = None,
        indicador_id: Optional[str] = None
    ) -> List[Alerta]:
        """
        Obtiene alertas filtradas.
        
        Args:
            nivel: Filtrar por nivel de alerta
            indicador_id: Filtrar por ID de indicador
            
        Returns:
            Lista de alertas filtradas
        """
        alertas = self.alertas
        
        if nivel:
            alertas = [a for a in alertas if a.nivel == nivel]
        
        if indicador_id:
            alertas = [a for a in alertas if a.indicador_id == indicador_id]
        
        return alertas
    
    def resumen_alertas(self) -> Dict[str, Any]:
        """
        Genera un resumen de las alertas actuales.
        
        Returns:
            Diccionario con resumen por nivel
        """
        total = len(self.alertas)
        por_nivel = {
            "total": total,
            "critico": len([a for a in self.alertas if a.nivel == NivelAlerta.CRITICO]),
            "atencion": len([a for a in self.alertas if a.nivel == NivelAlerta.ATENCION]),
            "normal": len([a for a in self.alertas if a.nivel == NivelAlerta.NORMAL]),
            "info": len([a for a in self.alertas if a.nivel == NivelAlerta.INFO])
        }
        
        return por_nivel
    
    def exportar_alertas(self, formato: str = "df") -> Any:
        """
        Exporta las alertas en el formato especificado.
        
        Args:
            formato: "df" para DataFrame, "dict" para diccionario
            
        Returns:
            Alertas en el formato solicitado
        """
        if formato == "df":
            if not self.alertas:
                return pd.DataFrame()
            
            datos = []
            for alerta in self.alertas:
                datos.append({
                    "id": alerta.id,
                    "timestamp": alerta.timestamp,
                    "nivel": alerta.nivel.value,
                    "indicador_id": alerta.indicador_id,
                    "indicador_nombre": alerta.indicador_nombre,
                    "mensaje": alerta.mensaje,
                    "campo": alerta.resultado_regla.campo,
                    "valor_encontrado": alerta.resultado_regla.valor_encontrado,
                    "accionable": alerta.accionable,
                    "acknowledged": alerta.acknowledged
                })
            
            return pd.DataFrame(datos)
        
        elif formato == "dict":
            return [
                {
                    "id": a.id,
                    "timestamp": a.timestamp.isoformat(),
                    "nivel": a.nivel.value,
                    "indicador_id": a.indicador_id,
                    "mensaje": a.mensaje
                }
                for a in self.alertas
            ]
        
        return self.alertas


# =============================================================================
# EJEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    # Ejemplo rápido de uso
    logging.basicConfig(level=logging.INFO)
    
    # Crear datos de prueba
    datos = {
        "Id": ["IND-001", "IND-002", "IND-003", "IND-004"],
        "Indicador": ["Tasa de Deserción", "Eficiencia Terminal", "Cobertura", "Acreditación"],
        "Cumplimiento": [0.65, 0.85, 0.92, 1.15],
        "Ejecucion": [65, 85, 92, 115],
        "Fecha": ["2026-01", "2026-01", "2026-01", "2026-01"]
    }
    df_prueba = pd.DataFrame(datos)
    
    # Crear motor y evaluar
    motor = RulesEngine()
    resultados = motor.evaluar_todo(df_prueba)
    
    # Filtrar solo alertas (no normales)
    alertas_resultados = [r for r in resultados if r.nivel != NivelAlerta.NORMAL]
    
    print(f"\n📊 Resumen de evaluación:")
    print(f"  Total reglas evaluadas: {len(resultados)}")
    print(f"  Alertas generadas: {len(alertas_resultados)}")
    
    for r in alertas_resultados:
        emoji = "🔴" if r.nivel == NivelAlerta.CRITICO else "🟡"
        print(f"  {emoji} [{r.nivel.value}] {r.registro_id}: {r.mensaje}")
    
    # Generar alertas formales
    alertas = motor.generar_alertas(resultados)
    print(f"\n🚨 Alertas formales generadas: {len(alertas)}")
    
    # Exportar
    df_alertas = motor.exportar_alertas("df")
    if not df_alertas.empty:
        print(f"\n📋 DataFrame de alertas:")
        print(df_alertas[["indicador_id", "nivel", "mensaje"]].to_string(index=False))
