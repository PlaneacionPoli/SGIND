"""
scripts/etl/agent5_corrections.py
Correcciones de hallazgos CRÍTICOS detectados por AGENT 5

HALLAZGOS CRÍTICOS A RESOLVER:
1. Ejecución = 1.35 (máximo debe ser 1.3) → Aplicar capping
2. Meta = 0 (inválido, debe ser > 0) → Validar y filtrar

RESPONSABILIDAD: Aplicar validaciones y correcciones en el pipeline ETL.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


class AGENT5Corrections:
    """Correcciones para hallazgos detectados por AGENT 5"""

    # Constantes de validación (desde core/config.py)
    EJECUCION_MAX = 1.3  # Máximo permitido para ejecución
    META_MIN = 0.0001    # Mínimo permitido (> 0)
    META_MAX = 1.0       # Máximo permitido (100%)

    @staticmethod
    def apply_ejecucion_capping(df: pd.DataFrame, column: str = "Ejecucion") -> Tuple[pd.DataFrame, int]:
        """
        CORRECCIÓN 1: Señalar Ejecución > 1.3 (dato faltante, no se corrige el valor).

        Ejecucion en este pipeline NO es una razón 0-1.3: se almacena en la
        escala propia de cada indicador (porcentual 0-100, conteo bruto, o
        en casos puntuales una razón pequeña como el ID 332). Un capping fijo
        a 1.3 destruía ejecuciones reales como 96.5 → 1.3 o 93505 → 1.3,
        disparando falsos Cumplimiento (hallado en IDs 569, 570, 611, 557,
        208, etc. — ~843 valores afectados). El Cumplimiento/Cumplimiento
        Real YA se capan al tope correspondiente (1.0 o 1.3) en la fórmula
        de la hoja (ver formulas_excel.py); no hace falta capar también el
        valor crudo de Ejecucion. Por eso esta función solo registra cuántos
        valores exceden el umbral, sin reescribirlos.

        Args:
            df: DataFrame con columna Ejecucion
            column: Nombre de columna (default "Ejecucion")

        Returns:
            Tuple (df_sin_cambios, cantidad_valores_excedidos)
        """
        df_copy = df.copy()

        if column not in df_copy.columns:
            logger.warning(f"Columna '{column}' no encontrada en DataFrame")
            return df_copy, 0

        mask_excedida = (df_copy[column].notna()) & (df_copy[column] > AGENT5Corrections.EJECUCION_MAX)
        cantidad = mask_excedida.sum()

        if cantidad > 0:
            logger.info(
                f"ℹ️  {cantidad} valores de {column} > {AGENT5Corrections.EJECUCION_MAX} "
                "(no se capan: son ejecuciones reales en su propia escala)"
            )

        return df_copy, cantidad

    @staticmethod
    def validate_meta(df: pd.DataFrame, column: str = "Meta") -> Tuple[pd.DataFrame, int, int]:
        """
        CORRECCIÓN 2: Validar Meta = 0/NULL (dato faltante, no se corrige el valor).

        Meta en este pipeline NO es una razón 0-1: se almacena en escala
        porcentual (0-100, ej. Meta=100) o como conteo bruto (ej. 274, 14,
        matrículas). Un capping fijo a 1.0 destruía metas legítimas como
        Meta=100 → 1, disparando falsos Cumplimiento de miles por ciento
        (hallado en IDs 551-555 y ~78 indicadores más). Por eso esta función
        solo señala Meta=0/NULL (dato faltante real); no reescribe valores.

        Meta=0 es un valor legítimo (no dato faltante) en indicadores de
        Sentido="Negativo" tipo SST (ej. 106 Mortalidad, 127 Incidencia
        Enfermedad Laboral): la meta institucional es cero accidentes/casos,
        por lo que Meta=0 NO se señala para ellos. Meta=NULL (sin dato) sí
        se sigue señalando en cualquier Sentido.

        Args:
            df: DataFrame con columna Meta
            column: Nombre de columna (default "Meta")

        Returns:
            Tuple (df_validado, cantidad_metas_cero, cantidad_metas_excedidas)
        """
        df_copy = df.copy()

        if column not in df_copy.columns:
            logger.warning(f"Columna '{column}' no encontrada en DataFrame")
            return df_copy, 0, 0

        if "Sentido" in df_copy.columns:
            es_negativo = df_copy["Sentido"].astype(str).str.strip().str.lower() == "negativo"
        else:
            es_negativo = pd.Series(False, index=df_copy.index)

        # VALIDACIÓN: Meta = NULL (siempre) o Meta = 0 (salvo Sentido=Negativo)
        mask_meta_cero = df_copy[column].isna() | ((df_copy[column] == 0) & ~es_negativo)
        cantidad_cero = mask_meta_cero.sum()

        if cantidad_cero > 0:
            logger.warning(
                f"🔴 CRÍTICO: {cantidad_cero} valores de {column} = 0 o NULL. Requiere revisión..."
            )

            # Obtener IDs afectados para auditoría
            if "Id" in df_copy.columns:
                ids_afectados = df_copy.loc[mask_meta_cero, "Id"].unique()
                logger.warning(f"   IDs afectados: {ids_afectados[:5].tolist()}")
                logger.warning(f"   RECOMENDACIÓN: Revisar meta de estos indicadores")
            else:
                logger.warning(f"   RECOMENDACIÓN: Revisar metas en consolidado")

        return df_copy, cantidad_cero, 0

    @staticmethod
    def apply_all_corrections(df: pd.DataFrame, verbose: bool = True) -> Tuple[pd.DataFrame, dict]:
        """
        Aplicar TODAS las correcciones de AGENT 5.

        Args:
            df: DataFrame a corregir
            verbose: Loguear detalles (default True)

        Returns:
            Tuple (df_corregido, reporte_correcciones)
        """
        df_result = df.copy()
        reporte = {
            "ejecucion_excedidas": 0,
            "meta_cero": 0,
            "meta_excedidas": 0,
            "total_correcciones": 0
        }

        if verbose:
            logger.info("╔════════════════════════════════════════════════════════════════╗")
            logger.info("║  APLICANDO CORRECCIONES DE AGENT 5                             ║")
            logger.info("║  Hallazgos Críticos: Ejecución y Meta                          ║")
            logger.info("╚════════════════════════════════════════════════════════════════╝")

        # Aplicar Corrección 1: Ejecución (solo señala > 1.3, no reescribe)
        if "Ejecucion" in df_result.columns:
            if verbose:
                logger.info("\n✓ CORRECCIÓN 1: Señalar Ejecucion > 1.3 (sin capping)")
            df_result, cantidad_exec = AGENT5Corrections.apply_ejecucion_capping(df_result)
            reporte["ejecucion_excedidas"] = cantidad_exec

        # Aplicar Corrección 2: Meta validación (solo señala Meta=0/NULL)
        if "Meta" in df_result.columns:
            if verbose:
                logger.info("\n✓ CORRECCIÓN 2: Validar Meta = 0/NULL")
            df_result, meta_cero, meta_excedida = AGENT5Corrections.validate_meta(df_result)
            reporte["meta_cero"] = meta_cero
            reporte["meta_excedidas"] = meta_excedida

        reporte["total_correcciones"] = reporte["meta_cero"]

        if verbose:
            logger.info("\n" + "="*70)
            logger.info("RESUMEN DE CORRECCIONES")
            logger.info("="*70)
            logger.info(f"ℹ️  Ejecucion > 1.3 (sin tocar): {reporte['ejecucion_excedidas']}")
            logger.info(f"⚠️  Meta = 0 detectados: {reporte['meta_cero']}")
            logger.info(f"📊 TOTAL CORRECCIONES: {reporte['total_correcciones']}")
            logger.info("="*70)

        return df_result, reporte

    @staticmethod
    def validate_post_corrections(df: pd.DataFrame) -> bool:
        """
        Validar que todas las correcciones se aplicaron correctamente.

        Returns:
            True si todas las validaciones pasaron, False si hay problemas.
        """
        all_ok = True

        # Ejecucion > 1.3 es válido en este pipeline (escala propia por
        # indicador) — solo se informa, no se marca como fallo.
        if "Ejecucion" in df.columns:
            valores_excedidos = df[(df["Ejecucion"].notna()) & (df["Ejecucion"] > AGENT5Corrections.EJECUCION_MAX)]
            if len(valores_excedidos) > 0:
                logger.info(f"ℹ️  {len(valores_excedidos)} Ejecucion > {AGENT5Corrections.EJECUCION_MAX} (válido, no se capa)")
            else:
                logger.info("✅ Ejecucion ≤ 1.3 en todos los registros")

        # Validar Meta
        if "Meta" in df.columns:
            meta_cero = df[(df["Meta"].isna()) | (df["Meta"] == 0)]
            if len(meta_cero) > 0:
                logger.warning(f"⚠️  VALIDACIÓN INCOMPLETA: {len(meta_cero)} Meta = 0 o NULL (revisar manualmente)")
                all_ok = False
            else:
                logger.info("✅ VALIDACIÓN OK: Meta > 0")

        return all_ok


def apply_agent5_corrections_to_consolidado(
    input_file: str,
    output_file: Optional[str] = None
) -> Tuple[str, dict]:
    """
    Aplicar correcciones de AGENT 5 a archivo consolidado Excel.

    Args:
        input_file: Ruta a Consolidado_API_Kawak.xlsx
        output_file: Ruta de salida (default: reemplaza input)

    Returns:
        Tuple (archivo_salida, reporte_correcciones)
    """
    logger.info(f"📂 Cargando: {input_file}")
    df = pd.read_excel(input_file, sheet_name=0)
    logger.info(f"   ✓ {len(df)} registros cargados")

    # Aplicar correcciones
    df_corregido, reporte = AGENT5Corrections.apply_all_corrections(df)

    # Guardar
    if output_file is None:
        output_file = input_file

    logger.info(f"\n📝 Guardando: {output_file}")
    df_corregido.to_excel(output_file, sheet_name="Sheet1", index=False)
    logger.info(f"   ✓ Archivo guardado")

    # Validar post-correcciones
    logger.info("\n🔍 Validando correcciones...")
    validation_ok = AGENT5Corrections.validate_post_corrections(df_corregido)

    if validation_ok:
        logger.info("\n✅ TODAS LAS CORRECCIONES APLICADAS Y VALIDADAS")
    else:
        logger.warning("\n⚠️  ALGUNAS CORRECCIONES REQUIEREN REVISIÓN MANUAL")

    return output_file, reporte


if __name__ == "__main__":
    # Ejemplo de uso
    consolidado_file = "data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx"
    apply_agent5_corrections_to_consolidado(consolidado_file)
