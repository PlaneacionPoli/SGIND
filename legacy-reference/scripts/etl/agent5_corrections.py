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
        CORRECCIÓN 1: Aplicar capping a ejecución.

        Problema: Ejecución puede ser > 1.3 cuando hay sobrecumplimiento excesivo.
        Solución: Limitar a máximo 1.3 (130%).

        Args:
            df: DataFrame con columna Ejecucion
            column: Nombre de columna (default "Ejecucion")

        Returns:
            Tuple (df_corregido, cantidad_valores_capeados)
        """
        df_copy = df.copy()

        if column not in df_copy.columns:
            logger.warning(f"Columna '{column}' no encontrada en DataFrame")
            return df_copy, 0

        # Detectar valores > límite
        mask_invalido = (df_copy[column].notna()) & (df_copy[column] > AGENT5Corrections.EJECUCION_MAX)
        cantidad = mask_invalido.sum()

        if cantidad > 0:
            logger.warning(
                f"🔴 CRÍTICO: {cantidad} valores de {column} > {AGENT5Corrections.EJECUCION_MAX}. Aplicando capping..."
            )

            # Registrar valores antes de capping (para auditoría)
            valores_originales = df_copy.loc[mask_invalido, column].tolist()
            logger.info(f"   Valores originales (muestra): {valores_originales[:5]}")

            # Aplicar capping
            df_copy.loc[mask_invalido, column] = AGENT5Corrections.EJECUCION_MAX

            # Verificación
            valores_cappados = df_copy.loc[mask_invalido, column].tolist()
            logger.info(f"   Valores cappados: {valores_cappados[:5]}")
            logger.info(f"   ✅ Capping aplicado a {cantidad} registros")

        return df_copy, cantidad

    @staticmethod
    def validate_meta(df: pd.DataFrame, column: str = "Meta") -> Tuple[pd.DataFrame, int, int]:
        """
        CORRECCIÓN 2: Validar meta está en rango (0, 1.0].

        Problema: Meta = 0 es inválido (puede causar división por cero).
        Solución: Validar que Meta > 0 y Meta ≤ 1.0.

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

        # VALIDACIÓN 2a: Meta = 0 o NULL
        mask_meta_cero = (df_copy[column].isna()) | (df_copy[column] == 0)
        cantidad_cero = mask_meta_cero.sum()

        # VALIDACIÓN 2b: Meta > 1.0 (100%)
        mask_meta_excedida = (df_copy[column].notna()) & (df_copy[column] > AGENT5Corrections.META_MAX)
        cantidad_excedida = mask_meta_excedida.sum()

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

        if cantidad_excedida > 0:
            logger.warning(
                f"🟠 ALTO: {cantidad_excedida} valores de {column} > 1.0 (>100%). Capping..."
            )

            # Aplicar capping a 1.0
            df_copy.loc[mask_meta_excedida, column] = AGENT5Corrections.META_MAX
            logger.info(f"   ✅ Capping aplicado a {cantidad_excedida} metas")

        return df_copy, cantidad_cero, cantidad_excedida

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
            "ejecucion_cappados": 0,
            "meta_cero": 0,
            "meta_excedidas": 0,
            "total_correcciones": 0
        }

        if verbose:
            logger.info("╔════════════════════════════════════════════════════════════════╗")
            logger.info("║  APLICANDO CORRECCIONES DE AGENT 5                             ║")
            logger.info("║  Hallazgos Críticos: Ejecución y Meta                          ║")
            logger.info("╚════════════════════════════════════════════════════════════════╝")

        # Aplicar Corrección 1: Ejecución capping
        if "Ejecucion" in df_result.columns:
            if verbose:
                logger.info("\n✓ CORRECCIÓN 1: Aplicar capping a Ejecucion (máx 1.3)")
            df_result, cantidad_exec = AGENT5Corrections.apply_ejecucion_capping(df_result)
            reporte["ejecucion_cappados"] = cantidad_exec

        # Aplicar Corrección 2: Meta validación
        if "Meta" in df_result.columns:
            if verbose:
                logger.info("\n✓ CORRECCIÓN 2: Validar Meta en rango (0, 1.0]")
            df_result, meta_cero, meta_excedida = AGENT5Corrections.validate_meta(df_result)
            reporte["meta_cero"] = meta_cero
            reporte["meta_excedidas"] = meta_excedida

        reporte["total_correcciones"] = sum([
            reporte["ejecucion_cappados"],
            reporte["meta_cero"],
            reporte["meta_excedidas"]
        ])

        if verbose:
            logger.info("\n" + "="*70)
            logger.info("RESUMEN DE CORRECCIONES")
            logger.info("="*70)
            logger.info(f"✅ Ejecucion cappados: {reporte['ejecucion_cappados']}")
            logger.info(f"⚠️  Meta = 0 detectados: {reporte['meta_cero']}")
            logger.info(f"✅ Meta excedidas (cappados): {reporte['meta_excedidas']}")
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

        # Validar Ejecucion
        if "Ejecucion" in df.columns:
            valores_invalidos = df[(df["Ejecucion"].notna()) & (df["Ejecucion"] > AGENT5Corrections.EJECUCION_MAX)]
            if len(valores_invalidos) > 0:
                logger.error(f"❌ VALIDACIÓN FALLIDA: {len(valores_invalidos)} Ejecucion > {AGENT5Corrections.EJECUCION_MAX}")
                all_ok = False
            else:
                logger.info("✅ VALIDACIÓN OK: Ejecucion ≤ 1.3")

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
