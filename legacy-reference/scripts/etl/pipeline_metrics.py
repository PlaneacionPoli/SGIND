"""
scripts/etl/pipeline_metrics.py
Métricas de rendimiento del pipeline ETL.

Rastrea tiempos de ejecución, uso de memoria y métricas de calidad.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class StepMetrics:
    """Métricas de un paso del pipeline."""
    
    step_name: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration_seconds: Optional[float] = None
    input_rows: int = 0
    output_rows: int = 0
    memory_mb: Optional[float] = None
    status: str = "pending"
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def start(self) -> None:
        """Iniciar temporizador."""
        self.start_time = time.time()
        self.status = "running"
    
    def finish(self, status: str = "ok", error: Optional[str] = None) -> None:
        """Finalizar paso."""
        self.end_time = time.time()
        if self.start_time:
            self.duration_seconds = round(self.end_time - self.start_time, 3)
        self.status = status
        self.error = error
    
    def set_rows(self, input_rows: int, output_rows: int) -> None:
        """Establecer filas de entrada/salida."""
        self.input_rows = input_rows
        self.output_rows = output_rows
    
    def set_memory(self, memory_mb: float) -> None:
        """Establecir uso de memoria."""
        self.memory_mb = round(memory_mb, 2)


@dataclass
class PipelineMetrics:
    """Métricas totales del pipeline."""
    
    pipeline_name: str = "SGIND_ETL"
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    total_duration_seconds: Optional[float] = None
    steps: List[StepMetrics] = field(default_factory=list)
    status: str = "pending"
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def start(self) -> None:
        """Iniciar pipeline."""
        self.start_time = time.time()
        self.status = "running"
        logger.info(f"🚀 Pipeline {self.pipeline_name} iniciado")
    
    def finish(self, status: str = "ok", error: Optional[str] = None) -> None:
        """Finalizar pipeline."""
        self.end_time = time.time()
        if self.start_time:
            self.total_duration_seconds = round(self.end_time - self.start_time, 3)
        self.status = status
        self.error = error
        
        # Calcular métricas resumen
        total_input = sum(s.input_rows for s in self.steps)
        total_output = sum(s.output_rows for s in self.steps)
        
        logger.info(f"✅ Pipeline {self.pipeline_name} completado")
        logger.info(f"   Duración total: {self.total_duration_seconds}s")
        logger.info(f"   Pasos ejecutados: {len(self.steps)}")
        logger.info(f"   Filas procesadas: {total_input} → {total_output}")
    
    def add_step(self, step: StepMetrics) -> None:
        """Agregar paso al pipeline."""
        self.steps.append(step)
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtener resumen de métricas."""
        return {
            "pipeline": self.pipeline_name,
            "status": self.status,
            "total_duration_seconds": self.total_duration_seconds,
            "steps_count": len(self.steps),
            "total_input_rows": sum(s.input_rows for s in self.steps),
            "total_output_rows": sum(s.output_rows for s in self.steps),
            "steps": [
                {
                    "name": s.step_name,
                    "duration_seconds": s.duration_seconds,
                    "input_rows": s.input_rows,
                    "output_rows": s.output_rows,
                    "status": s.status
                }
                for s in self.steps
            ]
        }
    
    def save(self, path: Path) -> None:
        """Guardar métricas a archivo JSON."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.get_summary(), f, indent=2, ensure_ascii=False)
        logger.info(f"📊 Métricas guardadas en {path}")


class MetricsCollector:
    """Recolector de métricas del pipeline."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metrics = PipelineMetrics()
        self.current_step: Optional[StepMetrics] = None
    
    def start_pipeline(self) -> None:
        """Iniciar recolección de métricas."""
        self.metrics.start()
    
    def start_step(self, step_name: str) -> StepMetrics:
        """Iniciar paso."""
        # Finalizar paso anterior si existe
        if self.current_step and self.current_step.status == "running":
            self.current_step.finish("interrupted")
        
        self.current_step = StepMetrics(step_name=step_name)
        self.current_step.start()
        self.metrics.add_step(self.current_step)
        
        logger.info(f"  📏 Paso '{step_name}' iniciado")
        return self.current_step
    
    def finish_step(
        self,
        status: str = "ok",
        error: Optional[str] = None,
        input_rows: int = 0,
        output_rows: int = 0
    ) -> None:
        """Finalizar paso actual."""
        if self.current_step:
            self.current_step.set_rows(input_rows, output_rows)
            self.current_step.finish(status, error)
            
            logger.info(
                f"  ✅ Paso '{self.current_step.step_name}' completado "
                f"({self.current_step.duration_seconds}s, "
                f"{input_rows}→{output_rows} filas)"
            )
    
    def finish_pipeline(
        self,
        status: str = "ok",
        error: Optional[str] = None
    ) -> None:
        """Finalizar recolección de métricas."""
        # Finalizar último paso si está pendiente
        if self.current_step and self.current_step.status == "running":
            self.current_step.finish("completed")
        
        self.metrics.finish(status, error)
        
        # Guardar métricas
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics_path = self.output_dir / f"pipeline_metrics_{timestamp}.json"
        self.metrics.save(metrics_path)
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtener resumen de métricas."""
        return self.metrics.get_summary()


def get_memory_usage_mb() -> float:
    """Obtener uso de memoria actual en MB."""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0
