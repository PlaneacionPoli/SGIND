"""
consolidation/core/audit.py
Módulo de auditoría y versionado de artefactos - Fase 2.

Responsabilidades:
- Registrar todas las operaciones del pipeline
- Versionar artefactos generados
- Mantener trazabilidad end-to-end
- Generar reportes de auditoría
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS Y CONSTANTES
# =============================================================================

class TipoOperacion(str, Enum):
    """Tipos de operaciones auditadas."""
    EXTRACCION = "extraccion"
    TRANSFORMACION = "transformacion"
    CONSOLIDACION = "consolidacion"
    VALIDACION = "validacion"
    ALERTA = "alerta"
    EXPORTACION = "exportacion"
    ERROR = "error"


class TipoArtefacto(str, Enum):
    """Tipos de artefactos generados."""
    DATASET = "dataset"
    REPORTE = "reporte"
    ALERTA = "alerta"
    LOG = "log"
    METADATA = "metadata"
    CONFIG = "config"


# =============================================================================
# ESTRUCTURAS DE DATOS
# =============================================================================

@dataclass
class RegistroAuditoria:
    """Registro individual de una operación auditada."""
    timestamp: datetime
    operacion: TipoOperacion
    usuario: str
    detalle: str
    registros_procesados: int = 0
    registros_exitosos: int = 0
    registros_fallidos: int = 0
    duracion_ms: float = 0
    origen: Optional[str] = None
    destino: Optional[str] = None
    errores: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArtefactoVersionado:
    """Representa un artefacto versionado."""
    nombre: str
    tipo: TipoArtefacto
    ruta: Path
    checksum: str
    version: str
    timestamp: datetime
    pipeline_run: str
    registros: int
    tamanio_bytes: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineRun:
    """Representa una ejecución completa del pipeline."""
    id: str
    timestamp: datetime
    duracion_total_ms: float
    estado: str  # SUCCESS, PARTIAL, FAILED
    artefactos: List[ArtefactoVersionado]
    registros_auditoria: List[RegistroAuditoria]
    resumen: Dict[str, Any] = field(default_factory=dict)
    errores: List[str] = field(default_factory=list)


# =============================================================================
# MOTOR DE AUDITORÍA
# =============================================================================

class AuditEngine:
    """
    Motor de auditoría y versionado.
    
    Gestiona el registro de operaciones, versionado de artefactos
    y trazabilidad end-to-end del pipeline.
    """

    def __init__(self, base_path: Path):
        """
        Inicializa el motor de auditoría.
        
        Args:
            base_path: Ruta base para almacenar artefactos y logs
        """
        self.base_path = base_path
        self.audit_path = base_path / "audit"
        self.versions_path = base_path / "versions"
        
        # Crear directorios si no existen
        self.audit_path.mkdir(parents=True, exist_ok=True)
        self.versions_path.mkdir(parents=True, exist_ok=True)
        
        # Registros de la sesión actual
        self.registros: List[RegistroAuditoria] = []
        self.artefactos: List[ArtefactoVersionado] = []
        self.pipeline_runs: List[PipelineRun] = []
        
        # ID de la sesión actual
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        logger.info(f"Motor de auditoría inicializado. Sesión: {self.session_id}")
        logger.info(f"  Audit path: {self.audit_path}")
        logger.info(f"  Versions path: {self.versions_path}")
    
    def registrar_operacion(
        self,
        operacion: TipoOperacion,
        detalle: str,
        usuario: str = "system",
        registros_procesados: int = 0,
        registros_exitosos: int = 0,
        registros_fallidos: int = 0,
        duracion_ms: float = 0,
        origen: Optional[str] = None,
        destino: Optional[str] = None,
        errores: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RegistroAuditoria:
        """
        Registra una operación en el log de auditoría.
        
        Returns:
            El registro de auditoría creado
        """
        registro = RegistroAuditoria(
            timestamp=datetime.now(),
            operacion=operacion,
            usuario=usuario,
            detalle=detalle,
            registros_procesados=registros_procesados,
            registros_exitosos=registros_exitosos,
            registros_fallidos=registros_fallidos,
            duracion_ms=duracion_ms,
            origen=origen,
            destino=destino,
            errores=errores or [],
            metadata=metadata or {}
        )
        
        self.registros.append(registro)
        
        # Log en archivo
        self._escribir_log(registro)
        
        logger.info(
            f"[AUDIT] {operacion.value} - {detalle} | "
            f"Procesados: {registros_procesados} | "
            f"Exitosos: {registros_exitosos} | "
            f"Fallidos: {registros_fallidos}"
        )
        
        return registro
    
    def versionar_artefacto(
        self,
        nombre: str,
        tipo: TipoArtefacto,
        ruta: Path,
        pipeline_run: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ArtefactoVersionado:
        """
        Versiona un artefacto generado.
        
        Args:
            nombre: Nombre del artefacto
            tipo: Tipo de artefacto
            ruta: Ruta al archivo
            pipeline_run: ID del pipeline run
            metadata: Metadatos adicionales
            
        Returns:
            El artefacto versionado
        """
        if not ruta.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {ruta}")
        
        # Calcular checksum
        checksum = self._calcular_checksum(ruta)
        
        # Obtener tamaño
        tamanio = ruta.stat().st_size
        
        # Contar registros si es CSV o Excel
        registros = self._contar_registros(ruta)
        
        # Determinar versión
        version = self._obtener_siguiente_version(nombre, tipo)
        
        artefacto = ArtefactoVersionado(
            nombre=nombre,
            tipo=tipo,
            ruta=ruta,
            checksum=checksum,
            version=version,
            timestamp=datetime.now(),
            pipeline_run=pipeline_run,
            registros=registros,
            tamanio_bytes=tamanio,
            metadata=metadata or {}
        )
        
        self.artefactos.append(artefacto)
        
        # Guardar metadata del artefacto
        self._guardar_metadata_artefacto(artefacto)
        
        logger.info(f"[VERSION] {nombre} v{version} - Checksum: {checksum[:8]}...")
        
        return artefacto
    
    def iniciar_pipeline_run(self) -> str:
        """
        Inicia una nueva ejecución de pipeline.
        
        Returns:
            ID del pipeline run
        """
        run_id = f"RUN-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"[PIPELINE] Iniciando: {run_id}")
        return run_id
    
    def finalizar_pipeline_run(
        self,
        run_id: str,
        estado: str,
        duracion_ms: float,
        errores: Optional[List[str]] = None
    ) -> PipelineRun:
        """
        Finaliza una ejecución de pipeline.
        
        Returns:
            El pipeline run completado
        """
        # Filtrar registros y artefactos de este run
        registros_run = [r for r in self.registros if run_id in str(r.metadata.get("pipeline_run", ""))]
        
        # Obtener artefactos de este run
        # (pendiente: asociar artefactos a runs específicos)
        
        run = PipelineRun(
            id=run_id,
            timestamp=datetime.now(),
            duracion_total_ms=duracion_ms,
            estado=estado,
            artefactos=self.artefactos[-10:],  # Últimos 10
            registros_auditoria=registros_run,
            resumen=self._generar_resumen_run(registros_run),
            errores=errores or []
        )
        
        self.pipeline_runs.append(run)
        
        # Guardar reporte del run
        self._guardar_reporte_run(run)
        
        emoji = "✅" if estado == "SUCCESS" else "⚠️" if estado == "PARTIAL" else "❌"
        logger.info(f"[PIPELINE] Finalizado: {run_id} - {emoji} {estado} - Duración: {duracion_ms/1000:.1f}s")
        
        return run
    
    def _escribir_log(self, registro: RegistroAuditoria):
        """Escribe un registro de auditoría en el log."""
        log_file = self.audit_path / f"audit_{self.session_id}.log"
        
        linea = (
            f"{registro.timestamp.isoformat()} | "
            f"{registro.operacion.value} | "
            f"{registro.usuario} | "
            f"{registro.detalle} | "
            f"Procesados: {registro.registros_procesados} | "
            f"Exitosos: {registro.registros_exitosos} | "
            f"Fallidos: {registro.registros_fallidos} | "
            f"Duración: {registro.duracion_ms:.0f}ms"
        )
        
        if registro.errores:
            linea += f" | Errores: {'; '.join(registro.errores)}"
        
        linea += "\n"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(linea)
    
    def _calcular_checksum(self, ruta: Path) -> str:
        """Calcula el checksum SHA256 de un archivo."""
        sha256 = hashlib.sha256()
        
        with open(ruta, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def _contar_registros(self, ruta: Path) -> int:
        """Cuenta el número de registros en un archivo."""
        try:
            if ruta.suffix == ".csv":
                df = pd.read_csv(ruta)
                return len(df)
            elif ruta.suffix in [".xlsx", ".xls"]:
                df = pd.read_excel(ruta)
                return len(df)
        except Exception as e:
            logger.warning(f"No se pudieron contar registros de {ruta}: {e}")
        
        return 0
    
    def _obtener_siguiente_version(self, nombre: str, tipo: TipoArtefacto) -> str:
        """Obtiene la siguiente versión para un artefacto."""
        versiones = [
            a.version for a in self.artefactos
            if a.nombre == nombre and a.tipo == tipo
        ]
        
        if not versiones:
            return "v1.0.0"
        
        # Parsear última versión
        ultima = sorted(versiones)[-1]
        try:
            major, minor, patch = ultima.replace("v", "").split(".")
            return f"v{major}.{minor}.{int(patch) + 1}"
        except:
            return f"v1.0.0"
    
    def _guardar_metadata_artefacto(self, artefacto: ArtefactoVersionado):
        """Guarda metadata de un artefacto versionado."""
        metadata_file = self.versions_path / f"{artefacto.nombre}_{artefacto.version}.json"
        
        data = {
            "nombre": artefacto.nombre,
            "tipo": artefacto.tipo.value,
            "ruta": str(artefacto.ruta),
            "checksum": artefacto.checksum,
            "version": artefacto.version,
            "timestamp": artefacto.timestamp.isoformat(),
            "pipeline_run": artefacto.pipeline_run,
            "registros": artefacto.registros,
            "tamanio_bytes": artefacto.tamanio_bytes,
            "metadata": artefacto.metadata
        }
        
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _generar_resumen_run(self, registros: List[RegistroAuditoria]) -> Dict[str, Any]:
        """Genera un resumen del pipeline run."""
        return {
            "total_operaciones": len(registros),
            "total_registros_procesados": sum(r.registros_procesados for r in registros),
            "total_registros_exitosos": sum(r.registros_exitosos for r in registros),
            "total_registros_fallidos": sum(r.registros_fallidos for r in registros),
            "operaciones_por_tipo": {
                op.value: sum(1 for r in registros if r.operacion == op)
                for op in TipoOperacion
            }
        }
    
    def _guardar_reporte_run(self, run: PipelineRun):
        """Guarda un reporte del pipeline run."""
        reporte_file = self.audit_path / f"run_{run.id}.json"
        
        data = {
            "id": run.id,
            "timestamp": run.timestamp.isoformat(),
            "duracion_total_ms": run.duracion_total_ms,
            "estado": run.estado,
            "resumen": run.resumen,
            "errores": run.errores,
            "artefactos": [
                {
                    "nombre": a.nombre,
                    "tipo": a.tipo.value,
                    "version": a.version,
                    "checksum": a.checksum,
                    "registros": a.registros
                }
                for a in run.artefactos
            ]
        }
        
        with open(reporte_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def generar_reporte_auditoria(
        self,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None
    ) -> str:
        """
        Genera un reporte de auditoría en texto plano.
        
        Returns:
            String con el reporte
        """
        lineas = []
        lineas.append("=" * 80)
        lineas.append("REPORTE DE AUDITORÍA - SISTEMA DE INDICADORES")
        lineas.append("=" * 80)
        lineas.append(f"Fecha generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lineas.append(f"Sesión: {self.session_id}")
        lineas.append("")
        
        # Filtrar por fechas si se especifica
        registros = self.registros
        if fecha_inicio:
            registros = [r for r in registros if r.timestamp >= fecha_inicio]
        if fecha_fin:
            registros = [r for r in registros if r.timestamp <= fecha_fin]
        
        lineas.append(f"Total operaciones registradas: {len(registros)}")
        lineas.append("")
        
        # Resumen por tipo de operación
        lineas.append("-" * 80)
        lineas.append("OPERACIONES POR TIPO:")
        lineas.append("-" * 80)
        
        for op in TipoOperacion:
            count = sum(1 for r in registros if r.operacion == op)
            if count > 0:
                lineas.append(f"  {op.value}: {count}")
        
        lineas.append("")
        
        # Resumen de artefactos
        lineas.append("-" * 80)
        lineas.append("ARTEFACTOS VERSIONADOS:")
        lineas.append("-" * 80)
        
        for a in self.artefactos[-10:]:  # Últimos 10
            lineas.append(
                f"  {a.nombre} {a.version} | "
                f"Registros: {a.registros} | "
                f"Tamaño: {a.tamanio_bytes:,} bytes | "
                f"Checksum: {a.checksum[:8]}..."
            )
        
        lineas.append("")
        
        # Detalle de errores
        errores = [r for r in registros if r.operacion == TipoOperacion.ERROR]
        if errores:
            lineas.append("-" * 80)
            lineas.append(f"ERRORES DETECTADOS ({len(errores)}):")
            lineas.append("-" * 80)
            
            for r in errores[:20]:  # Limitar a 20
                lineas.append(f"  [{r.timestamp.strftime('%Y-%m-%d %H:%M')}] {r.detalle}")
                for err in r.errores[:3]:  # Máximo 3 errores por registro
                    lineas.append(f"    - {err}")
        
        lineas.append("")
        lineas.append("=" * 80)
        
        return "\n".join(lineas)
    
    def exportar_metadata(self, formato: str = "json") -> Dict:
        """
        Exporta la metadata de auditoría.
        
        Returns:
            Diccionario con metadata completa
        """
        return {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "audit_path": str(self.audit_path),
            "versions_path": str(self.versions_path),
            "total_registros": len(self.registros),
            "total_artefactos": len(self.artefactos),
            "total_pipeline_runs": len(self.pipeline_runs),
            "registros": [
                {
                    "timestamp": r.timestamp.isoformat(),
                    "operacion": r.operacion.value,
                    "usuario": r.usuario,
                    "detalle": r.detalle,
                    "registros_procesados": r.registros_procesados,
                    "registros_exitosos": r.registros_exitosos,
                    "registros_fallidos": r.registros_fallidos,
                    "duracion_ms": r.duracion_ms
                }
                for r in self.registros[-100:]  # Últimos 100
            ],
            "artefactos": [
                {
                    "nombre": a.nombre,
                    "tipo": a.tipo.value,
                    "version": a.version,
                    "checksum": a.checksum,
                    "timestamp": a.timestamp.isoformat(),
                    "pipeline_run": a.pipeline_run,
                    "registros": a.registros
                }
                for a in self.artefactos[-50:]  # Últimos 50
            ]
        }


# =============================================================================
# EJEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    import tempfile
    
    logging.basicConfig(level=logging.INFO)
    
    # Crear motor de auditoría en directorio temporal
    with tempfile.TemporaryDirectory() as tmpdir:
        audit = AuditEngine(Path(tmpdir))
        
        # Simular operaciones
        audit.registrar_operacion(
            operacion=TipoOperacion.EXTRACCION,
            detalle="Extracción de archivo Kawak 2026",
            registros_procesados=100,
            registros_exitosos=98,
            registros_fallidos=2
        )
        
        audit.registrar_operacion(
            operacion=TipoOperacion.VALIDACION,
            detalle="Validación de rango de cumplimiento",
            registros_procesados=100,
            registros_exitosos=95,
            registros_fallidos=5
        )
        
        # Simular un error
        audit.registrar_operacion(
            operacion=TipoOperacion.ERROR,
            detalle="Error en transformación",
            errores=["Valor inválido en campo X", "Tipo de dato incorrecto"]
        )
        
        # Generar reporte
        reporte = audit.generar_reporte_auditoria()
        print(reporte)
        
        # Exportar metadata
        metadata = audit.exportar_metadata()
        print(f"\n📊 Metadata exportada: {metadata['total_registros']} registros")
