"""
Módulo de ingesta y validación de plantillas Excel/PDF.
Sistema de Indicadores SGIND - Fase 1: Gobierno y calidad de datos.

Responsabilidades:
- Detectar y mapear plantillas basadas en estructura conocida.
- Extraer y normalizar datos de cada fuente.
- Aplicar validaciones automáticas por plantilla.
- Generar artefactos de calidad y logs.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any

import pandas as pd

# =============================================================================
# CONFIGURACIÓN Y CONSTANTES
# =============================================================================

RAW_PATH = Path("data/raw")
OUTPUT_PATH = Path("data/output")
ARTIFACTS_PATH = OUTPUT_PATH / "artifacts"
LOGS_PATH = OUTPUT_PATH / "logs"

# Asegurar que existen los directorios de salida
ARTIFACTS_PATH.mkdir(parents=True, exist_ok=True)
LOGS_PATH.mkdir(parents=True, exist_ok=True)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_PATH / f"ingesta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# SCHEMAS DE PLANTILLAS
# =============================================================================

@dataclass
class PlantillaSchema:
    """Define la estructura esperada de cada plantilla."""
    nombre: str
    hoja: str
    columnas_requeridas: List[str]
    columnas_opcionales: List[str]
    clave_primaria: str
    validaciones: Dict[str, Any]
    semaforizacion: Dict[str, Any]

# Catálogo de plantillas conocidas
PLANTILLAS: Dict[str, PlantillaSchema] = {
    "acciones_mejora": PlantillaSchema(
        nombre="Acciones de Mejora",
        hoja="Acciones",
        columnas_requeridas=["ID", "FECHA_IDENTIFICACION", "DESCRIPCION", "AVANCE", "ESTADO"],
        columnas_opcionales=[],
        clave_primaria="ID",
        validaciones={
            "ID": {"tipo": "unico", "nulos": False},
            "FECHA_IDENTIFICACION": {"tipo": "fecha", "nulos": False},
            "AVANCE": {"tipo": "rango", "min": 0, "max": 100},
            "ESTADO": {"tipo": "valores_validos", "valores": ["Abierto", "Cerrado", "En proceso", "Pendiente"]}
        },
        semaforizacion={
            "campo": "CUMPLIMIENTO",
            "rangos": {"critico": "<70", "atencion": "70-80", "normal": "80-105"}
        }
    ),
    "dataset_unificado": PlantillaSchema(
        nombre="Dataset Unificado",
        hoja="Unificado",
        columnas_requeridas=["Id", "Indicador", "Proceso", "Periodicidad", "Sentido"],
        columnas_opcionales=[],
        clave_primaria="Id",
        validaciones={
            "Id": {"tipo": "unico", "nulos": False},
            "Indicador": {"tipo": "texto", "nulos": False},
            "Periodicidad": {"tipo": "valores_validos", "valores": ["Mensual", "Trimestral", "Semestral", "Anual"]},
            "Sentido": {"tipo": "valores_validos", "valores": ["Ascendente", "Descendente"]}
        },
        semaforizacion={
            "campo": "Cumplimiento",
            "rangos": {"critico": "<70", "atencion": "70-80", "normal": "80-105"}
        }
    ),
    "ficha_tecnica": PlantillaSchema(
        nombre="Ficha Técnica",
        hoja="Hoja1",
        columnas_requeridas=["Id Ind", "ID Kawak", "Nombre del indicador"],
        columnas_opcionales=[],
        clave_primaria="Id Ind",
        validaciones={
            "Id Ind": {"tipo": "unico", "nulos": False},
            "ID Kawak": {"tipo": "texto", "nulos": True},
            "Nombre del indicador": {"tipo": "texto", "nulos": False}
        },
        semaforizacion={}
    ),
    "kawak": PlantillaSchema(
        nombre="Indicadores Kawak",
        hoja="Hoja1",
        columnas_requeridas=["Id", "Indicador", "Clasificación", "Proceso"],
        columnas_opcionales=[],
        clave_primaria="Id",
        validaciones={
            "Id": {"tipo": "unico", "nulos": False},
            "Indicador": {"tipo": "texto", "nulos": False},
            "Clasificación": {"tipo": "texto", "nulos": False}
        },
        semaforizacion={
            "campo": "Cumplimiento",
            "rangos": {"critico": "<70", "atencion": "70-80", "normal": "80-105"}
        }
    ),
    "api": PlantillaSchema(
        nombre="Indicadores API",
        hoja="Indicadores",
        columnas_requeridas=["ID", "nombre", "clasificacion", "sentido", "proceso"],
        columnas_opcionales=[],
        clave_primaria="ID",
        validaciones={
            "ID": {"tipo": "unico", "nulos": False},
            "nombre": {"tipo": "texto", "nulos": False},
            "clasificacion": {"tipo": "texto", "nulos": False},
            "sentido": {"tipo": "valores_validos", "valores": ["Ascendente", "Descendente"]}
        },
        semaforizacion={
            "campo": "Cumplimiento",
            "rangos": {"critico": "<70", "atencion": "70-80", "normal": "80-105"}
        }
    ),
    "plan_accion": PlantillaSchema(
        nombre="Plan de Acción",
        hoja="Worksheet",
        columnas_requeridas=["Id Acción", "Fecha creación", "Clasificación", "Avance (%)", "Estado (Plan de Acción)"],
        columnas_opcionales=[],
        clave_primaria="Id Acción",
        validaciones={
            "Id Acción": {"tipo": "unico", "nulos": False},
            "Fecha creación": {"tipo": "fecha", "nulos": False},
            "Avance (%)": {"tipo": "rango", "min": 0, "max": 100},
            "Estado (Plan de Acción)": {"tipo": "valores_validos", "valores": ["Abierto", "Cerrado", "En proceso", "Pendiente"]}
        },
        semaforizacion={
            "campo": "Avance (%)",
            "rangos": {"critico": "<50", "atencion": "50-80", "normal": "80-100"}
        }
    ),
    "salidas_no_conformes": PlantillaSchema(
        nombre="Salidas No Conformes",
        hoja="SNC",
        columnas_requeridas=["codigo", "id_salida", "estado", "activo"],
        columnas_opcionales=[],
        clave_primaria="id_salida",
        validaciones={
            "id_salida": {"tipo": "unico", "nulos": False},
            "estado": {"tipo": "valores_validos", "valores": ["Abierto", "Cerrado", "En proceso"]},
            "activo": {"tipo": "booleano", "nulos": False}
        },
        semaforizacion={}
    )
}

# =============================================================================
# RESULTADOS DE VALIDACIÓN
# =============================================================================

@dataclass
class ResultadoValidacion:
    """Almacena el resultado de una validación."""
    plantilla: str
    archivo: str
    tipo_validacion: str
    campo: str
    estado: str  # OK, ERROR, WARNING
    mensaje: str
    registros_afectados: Optional[List[int]] = None

@dataclass
class ResultadoIngesta:
    """Almacena el resultado completo de una ingesta."""
    plantilla: str
    archivo: str
    fecha_ingesta: str
    registros_leidos: int
    registros_validos: int
    validaciones: List[ResultadoValidacion]
    datos: Optional[pd.DataFrame] = None
    errores: List[str] = field(default_factory=list)
    exitosa: bool = False

# =============================================================================
# CLASE PRINCIPAL DE INGESTA
# =============================================================================

class IngestorPlantillas:
    """Motor de ingesta y validación de plantillas Excel/PDF."""

    def __init__(self, raw_path: Path = RAW_PATH):
        self.raw_path = raw_path
        self.resultados: List[ResultadoIngesta] = []

    def detectar_plantilla(self, filepath: Path) -> Optional[str]:
        """
        Detecta qué tipo de plantilla corresponde a un archivo.
        Retorna el nombre de la plantilla o None si no se reconoce.
        """
        try:
            df_sample = pd.read_excel(filepath, sheet_name=0, nrows=10)
            columns = set(df_sample.columns)

            for nombre, schema in PLANTILLAS.items():
                # Verificar coincidencia de columnas requeridas
                required = set(schema.columnas_requeridas)
                if required.issubset(columns):
                    return nombre

            # Si no hay coincidencia exacta, buscar por similitud
            for nombre, schema in PLANTILLAS.items():
                matching = sum(1 for col in schema.columnas_requeridas if col in columns)
                if matching >= len(schema.columnas_requeridas) * 0.7:  # 70% de coincidencia
                    return nombre

            return None

        except Exception as e:
            logger.error(f"Error detectando plantilla para {filepath}: {e}")
            return None

    def validar_registros(self, df: pd.DataFrame, schema: PlantillaSchema, archivo: str) -> List[ResultadoValidacion]:
        """Aplica las validaciones definidas en el schema."""
        validaciones = []

        for campo, reglas in schema.validaciones.items():
            tipo = reglas.get("tipo")

            if tipo == "unico":
                if campo in df.columns:
                    duplicados = df[campo].duplicated().sum()
                    nulos = df[campo].isna().sum()
                    if duplicados > 0:
                        ids_duplicados = df[df[campo].duplicated()][campo].tolist()
                        validaciones.append(ResultadoValidacion(
                            plantilla=schema.nombre,
                            archivo=archivo,
                            tipo_validacion="duplicado",
                            campo=campo,
                            estado="ERROR",
                            mensaje=f"Campo {campo} tiene {duplicados} valores duplicados",
                            registros_afectados=ids_duplicados[:10]
                        ))
                    if nulos > 0:
                        validaciones.append(ResultadoValidacion(
                            plantilla=schema.nombre,
                            archivo=archivo,
                            tipo_validacion="nulos",
                            campo=campo,
                            estado="WARNING",
                            mensaje=f"Campo {campo} tiene {nulos} valores nulos",
                            registros_afectados=None
                        ))

            elif tipo == "rango":
                if campo in df.columns:
                    min_val = reglas.get("min", 0)
                    max_val = reglas.get("max", 100)
                    fuera_rango = df[(df[campo] < min_val) | (df[campo] > max_val)][campo].count()
                    if fuera_rango > 0:
                        validaciones.append(ResultadoValidacion(
                            plantilla=schema.nombre,
                            archivo=archivo,
                            tipo_validacion="rango",
                            campo=campo,
                            estado="WARNING",
                            mensaje=f"Campo {campo} tiene {fuera_rango} valores fuera del rango [{min_val}-{max_val}]",
                            registros_afectados=None
                        ))

            elif tipo == "valores_validos":
                if campo in df.columns:
                    valores_validos = reglas.get("valores", [])
                    invalidos = df[~df[campo].isin(valores_validos) & df[campo].notna()]
                    if len(invalidos) > 0:
                        validaciones.append(ResultadoValidacion(
                            plantilla=schema.nombre,
                            archivo=archivo,
                            tipo_validacion="valores_invalidos",
                            campo=campo,
                            estado="WARNING",
                            mensaje=f"Campo {campo} tiene {len(invalidos)} valores no válidos. Válidos: {valores_validos}",
                            registros_afectados=None
                        ))

            elif tipo == "fecha":
                if campo in df.columns:
                    try:
                        pd.to_datetime(df[campo])
                    except:
                        validaciones.append(ResultadoValidacion(
                            plantilla=schema.nombre,
                            archivo=archivo,
                            tipo_validacion="fecha",
                            campo=campo,
                            estado="ERROR",
                            mensaje=f"Campo {campo} contiene valores de fecha inválidos",
                            registros_afectados=None
                        ))

            elif tipo == "booleano":
                if campo in df.columns:
                    valores_unicos = df[campo].dropna().unique()
                    # Aceptar booleanos, 0/1, Si/No
                    validos = {True, False, 0, 1, "Si", "No", "SI", "NO", "sí", "no", "S", "N"}
                    invalidos = [v for v in valores_unicos if v not in validos]
                    if invalidos:
                        validaciones.append(ResultadoValidacion(
                            plantilla=schema.nombre,
                            archivo=archivo,
                            tipo_validacion="booleano",
                            campo=campo,
                            estado="WARNING",
                            mensaje=f"Campo {campo} tiene valores booleanos inválidos: {invalidos}",
                            registros_afectados=None
                        ))

        return validaciones

    def ingesta_archivo(self, filepath: Path) -> ResultadoIngesta:
        """Procesa un archivo individual y aplica validaciones."""
        logger.info(f"Procesando archivo: {filepath}")

        plantilla_detectada = self.detectar_plantilla(filepath)
        archivo = filepath.name

        if plantilla_detectada is None:
            logger.warning(f"No se detectó plantilla para: {filepath}")
            return ResultadoIngesta(
                plantilla="DESCONOCIDA",
                archivo=archivo,
                fecha_ingesta=datetime.now().isoformat(),
                registros_leidos=0,
                registros_validos=0,
                validaciones=[],
                exitosa=False,
                errores=[f"Plantilla no reconocida para {archivo}"]
            )

        schema = PLANTILLAS[plantilla_detectada]

        try:
            # Leer datos
            df = pd.read_excel(filepath, sheet_name=schema.hoja)
            registros_leidos = len(df)

            # Aplicar validaciones
            validaciones = self.validar_registros(df, schema, archivo)

            # Clasificar validaciones por severidad
            errores = [v for v in validaciones if v.estado == "ERROR"]
            warnings = [v for v in validaciones if v.estado == "WARNING"]

            # Los datos se consideran válidos si no hay errores críticos
            exitosa = len(errores) == 0
            registros_validos = registros_leidos - len(errores)

            resultado = ResultadoIngesta(
                plantilla=schema.nombre,
                archivo=archivo,
                fecha_ingesta=datetime.now().isoformat(),
                registros_leidos=registros_leidos,
                registros_validos=registros_validos,
                validaciones=validaciones,
                datos=df if exitosa else None,
                exitosa=exitosa,
                errores=[f"{v.tipo_validacion}: {v.mensaje}" for v in validaciones if v.estado == "ERROR"]
            )

            logger.info(f"Archivo {archivo}: {registros_leidos} registros, {len(validaciones)} validaciones, exitosa={exitosa}")
            return resultado

        except Exception as e:
            logger.error(f"Error procesando {archivo}: {e}")
            return ResultadoIngesta(
                plantilla=schema.nombre,
                archivo=archivo,
                fecha_ingesta=datetime.now().isoformat(),
                registros_leidos=0,
                registros_validos=0,
                validaciones=[],
                exitosa=False,
                errores=[str(e)]
            )

    def ingesta_total(self) -> List[ResultadoIngesta]:
        """Ejecuta la ingesta de todos los archivos en raw/."""
        logger.info("=== INICIO DE INGESTA TOTAL ===")

        self.resultados = []
        archivos_procesados = 0

        for root, dirs, files in os.walk(self.raw_path):
            for file in files:
                if file.endswith((".xlsx", ".xls")):
                    filepath = Path(root) / file
                    resultado = self.ingesta_archivo(filepath)
                    self.resultados.append(resultado)
                    archivos_procesados += 1

        logger.info(f"=== FIN DE INGESTA: {archivos_procesados} archivos procesados ===")
        return self.resultados

    def generar_artefactos(self) -> Dict[str, Any]:
        """Genera los artefactos de calidad y logs de la ingesta."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Resumen general
        resumen = {
            "fecha": datetime.now().isoformat(),
            "total_archivos": len(self.resultados),
            "exitosos": sum(1 for r in self.resultados if r.exitosa),
            "fallidos": sum(1 for r in self.resultados if not r.exitosa),
            "total_registros": sum(r.registros_leidos for r in self.resultados),
            "total_validaciones": sum(len(r.validaciones) for r in self.resultados)
        }

        # Detalle por archivo
        detalle = []
        for r in self.resultados:
            detalle.append({
                "plantilla": r.plantilla,
                "archivo": r.archivo,
                "fecha_ingesta": r.fecha_ingesta,
                "registros_leidos": r.registros_leidos,
                "registros_validos": r.registros_validos,
                "exitosa": r.exitosa,
                "errores": r.errores,
                "validaciones": [
                    {
                        "tipo": v.tipo_validacion,
                        "campo": v.campo,
                        "estado": v.estado,
                        "mensaje": v.mensaje
                    } for v in r.validaciones
                ]
            })

        # Guardar artefactos JSON
        artefactos = {
            "resumen": resumen,
            "detalle": detalle
        }

        artefacto_path = ARTIFACTS_PATH / f"ingesta_{timestamp}.json"
        with open(artefacto_path, "w", encoding="utf-8") as f:
            json.dump(artefactos, f, indent=2, ensure_ascii=False)

        logger.info(f"Artefacto de ingesta guardado: {artefacto_path}")
        return artefactos

    def generar_reporte_qa(self) -> str:
        """Genera un reporte de calidad en formato texto."""
        lineas = []
        lineas.append("=" * 80)
        lineas.append("REPORTE DE CALIDAD - INGESTA DE PLANTILLAS")
        lineas.append("=" * 80)
        lineas.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lineas.append("")

        # Resumen
        exitosos = [r for r in self.resultados if r.exitosa]
        fallidos = [r for r in self.resultados if not r.exitosa]

        lineas.append(f"Total archivos procesados: {len(self.resultados)}")
        lineas.append(f"Exitosos: {len(exitosos)}")
        lineas.append(f"Fallidos: {len(fallidos)}")
        lineas.append("")

        # Detalle de fallidos
        if fallidos:
            lineas.append("-" * 80)
            lineas.append("ARCHIVOS CON ERRORES:")
            lineas.append("-" * 80)
            for r in fallidos:
                lineas.append(f"  {r.archivo} ({r.plantilla})")
                for error in r.errores:
                    lineas.append(f"    - {error}")
            lineas.append("")

        # Detalle de validaciones
        todas_validaciones = []
        for r in self.resultados:
            todas_validaciones.extend(r.validaciones)

        errores = [v for v in todas_validaciones if v.estado == "ERROR"]
        warnings = [v for v in todas_validaciones if v.estado == "WARNING"]

        lineas.append("-" * 80)
        lineas.append("RESUMEN DE VALIDACIONES:")
        lineas.append("-" * 80)
        lineas.append(f"Total validaciones: {len(todas_validaciones)}")
        lineas.append(f"  Errores: {len(errores)}")
        lineas.append(f"  Warnings: {len(warnings)}")
        lineas.append("")

        if errores:
            lineas.append("ERRORES DETECTADOS:")
            for v in errores[:20]:  # Limitar a 20
                lineas.append(f"  [{v.archivo}] {v.campo}: {v.mensaje}")
            lineas.append("")

        if warnings:
            lineas.append("ADVERTENCIAS DETECTADAS:")
            for v in warnings[:20]:  # Limitar a 20
                lineas.append(f"  [{v.archivo}] {v.campo}: {v.mensaje}")
            lineas.append("")

        lineas.append("=" * 80)
        return "\n".join(lineas)


# =============================================================================
# EJECUCIÓN PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    # Ejecutar ingesta completa
    ingestor = IngestorPlantillas()
    resultados = ingestor.ingesta_total()
    artefactos = ingestor.generar_artefactos()

    # Generar y mostrar reporte QA
    reporte_qa = ingestor.generar_reporte_qa()
    print(reporte_qa)

    # Guardar reporte QA
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reporte_path = LOGS_PATH / f"reporte_qa_{timestamp}.txt"
    with open(reporte_path, "w", encoding="utf-8") as f:
        f.write(reporte_qa)

    print(f"\nReporte QA guardado: {reporte_path}")
    print(f"Artefactos de ingesta: {ARTIFACTS_PATH}")
