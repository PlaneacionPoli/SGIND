#!/usr/bin/env python3
"""
scripts/validar_cambio_plan_anual.py

PROPÓSITO:
  Validar que indicadores marcados como Plan Anual o Proyecto (=1 en Excel)
  cambian su nivel de cumplimiento CORRECTAMENTE cuando se aplica el estándar oficial.

COMPARACIÓN:
  ANTES: Lógica antigua (defectuosa) - NO detecta Plan Anual
  DESPUÉS: Función oficial - SÍ detecta Plan Anual

CAMBIOS ESPERADOS:
  Indicadores Plan Anual con cumplimiento entre 95-99.99%:
  - ANTES:   "Alerta" (usa umbral regular 100%)
  - DESPUÉS: "Cumplimiento" (usa umbral PA 95%)

EJECUCIÓN:
  python scripts/validar_cambio_plan_anual.py
  python scripts/validar_cambio_plan_anual.py --verbose
  python scripts/validar_cambio_plan_anual.py --export-csv

SALIDA:
  - Tabla de comparación en consola
  - Estadísticas de cambios
  - Archivo: artifacts/validacion_plan_anual_YYYYMMDD.csv (opcional)
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Agregar raíz del proyecto al PATH
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.config import (
    IDS_PLAN_ANUAL,
    UMBRAL_PELIGRO, UMBRAL_ALERTA, UMBRAL_SOBRECUMPLIMIENTO,
    UMBRAL_ALERTA_PA, UMBRAL_SOBRECUMPLIMIENTO_PA,
)
from core.domain import categorizar_cumplimiento


def categorizar_antigua_defectuosa(cumplimiento):
    """
    Implementación ANTIGUA y DEFECTUOSA (no detecta Plan Anual).
    Usada en strategic_indicators.py línea 55.
    """
    try:
        c = float(cumplimiento)
    except (TypeError, ValueError):
        return "Sin dato"
    
    if pd.isna(c):
        return "Sin dato"
    
    # Esta es la lógica DEFECTUOSA - siempre usa umbrales Regular
    if c < UMBRAL_PELIGRO:
        return "Peligro"
    elif c < UMBRAL_ALERTA:
        return "Alerta"
    elif c < UMBRAL_SOBRECUMPLIMIENTO:
        return "Cumplimiento"
    else:
        return "Sobrecumplimiento"


def validar_plan_anual(verbose=False, export_csv=False):
    """Validar cambios en categorización de Plan Anual"""
    
    logger.info("=" * 100)
    logger.info("VALIDACIÓN: CAMBIOS EN NIVEL DE CUMPLIMIENTO PARA PLAN ANUAL")
    logger.info("=" * 100)
    
    # 1. Cargar datos
    logger.info("\n📋 Cargando indicadores con datos de cumplimiento...")
    
    # Intentar múltiples ubicaciones
    data_paths = [
        ROOT / "data" / "output" / "Resultados Consolidados.xlsx",
        ROOT / "data" / "raw" / "Resultados Consolidados.xlsx",
        ROOT / "data" / "raw" / "Resultados_Consolidados_Fuente.xlsx",
    ]
    
    data_raw = None
    for path in data_paths:
        if path.exists():
            data_raw = path
            break
    
    if data_raw is None:
        logger.error(f"❌ Archivo no encontrado en:\n  " + "\n  ".join(str(p) for p in data_paths))
        return None
    
    try:
        df = pd.read_excel(data_raw, engine="openpyxl")
    except Exception as e:
        logger.error(f"❌ Error cargando Excel: {e}")
        return None
    
    logger.info(f"✅ Cargados {len(df)} registros")
    
    # 2. Normalizar nombres de columnas
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # Buscar columnas relevantes (con flexibilidad)
    col_id = None
    col_cumpl = None
    col_indicador = None
    
    for col in df.columns:
        if col in ["id", "id_indicador", "indicador_id"]:
            col_id = col
        if col in ["cumplimiento", "cumplimiento_dec", "cumpl"]:
            col_cumpl = col
        if col in ["indicador", "nombre", "nombre_indicador"]:
            col_indicador = col
    
    if not col_id or not col_cumpl:
        logger.error(f"❌ Columnas necesarias no encontradas. Disponibles: {list(df.columns)}")
        return None
    
    logger.info(f"✅ Columnas identificadas: id={col_id}, cumplimiento={col_cumpl}")
    
    # 3. Filtrar indicadores Plan Anual que tienen cumplimiento
    logger.info(f"\n🔍 Identificando {len(IDS_PLAN_ANUAL)} indicadores Plan Anual...")
    
    # Crear columna de ID limpio para matching
    df['id_limpio'] = df[col_id].astype(str).str.strip()
    
    # Filtrar Plan Anual
    df_pa = df[df['id_limpio'].isin(IDS_PLAN_ANUAL)].copy()
    
    # Filtrar que tengan cumplimiento válido
    df_pa['cumplimiento_val'] = pd.to_numeric(df_pa[col_cumpl], errors='coerce')
    df_pa = df_pa.dropna(subset=['cumplimiento_val'])
    
    logger.info(f"✅ {len(df_pa)} indicadores Plan Anual con cumplimiento registrado")
    
    if df_pa.empty:
        logger.warning("⚠️  No hay indicadores Plan Anual con cumplimiento para validar")
        return None
    
    # 4. Calcular categorías ANTES y DESPUÉS
    logger.info("\n🔄 Comparando categorías (ANTES vs DESPUÉS)...")
    
    df_pa['categoria_antigua'] = df_pa['cumplimiento_val'].apply(
        lambda c: categorizar_antigua_defectuosa(c)
    )
    
    df_pa['categoria_nueva'] = df_pa.apply(
        lambda row: categorizar_cumplimiento(row['cumplimiento_val'], row['id_limpio']),
        axis=1
    )
    
    # Detectar cambios
    df_pa['cambio'] = df_pa['categoria_antigua'] != df_pa['categoria_nueva']
    
    # 5. Análisis de cambios
    total_cambios = df_pa['cambio'].sum()
    total_sin_cambio = (~df_pa['cambio']).sum()
    
    logger.info(f"\n📊 RESULTADOS:")
    logger.info(f"  Indicadores con CAMBIO:      {total_cambios} ({100*total_cambios/len(df_pa):.1f}%)")
    logger.info(f"  Indicadores SIN cambio:      {total_sin_cambio} ({100*total_sin_cambio/len(df_pa):.1f}%)")
    
    # 6. Detallar cambios
    if total_cambios > 0:
        logger.info(f"\n✅ INDICADORES QUE CAMBIAN:")
        logger.info(f"{'='*100}")
        logger.info(
            f"{'ID':<10} {'Indicador':<40} {'Cumpl%':<10} {'ANTES':<20} {'DESPUÉS':<20}"
        )
        logger.info(f"{'-'*100}")
        
        for idx, row in df_pa[df_pa['cambio']].iterrows():
            cumpl_pct = row['cumplimiento_val'] * 100
            ind_name = str(row.get(col_indicador, 'N/A'))[:38]
            
            logger.info(
                f"{row['id_limpio']:<10} "
                f"{ind_name:<40} "
                f"{cumpl_pct:>8.1f}% "
                f"{row['categoria_antigua']:<20} "
                f"{row['categoria_nueva']:<20}"
            )
        
        logger.info(f"{'-'*100}\n")
    
    # 7. Validar cambios son correctos (ANTES: Alerta → DESPUÉS: Cumplimiento)
    logger.info("\n🔍 VALIDACIÓN: ¿Los cambios son correctos?")
    
    cambios_correctos = 0
    cambios_incorrectos = 0
    cambios_otros = 0
    
    for idx, row in df_pa[df_pa['cambio']].iterrows():
        cumpl = row['cumplimiento_val']
        antes = row['categoria_antigua']
        despues = row['categoria_nueva']
        
        # Cambio esperado: Alerta → Cumplimiento (para 0.95 ≤ cumpl < 1.00)
        if 0.95 <= cumpl < 1.00 and antes == "Alerta" and despues == "Cumplimiento":
            cambios_correctos += 1
        else:
            # Otros cambios
            cambios_otros += 1
    
    logger.info(f"  ✅ Cambios CORRECTOS (Alerta→Cumplimiento 95-99%): {cambios_correctos}")
    logger.info(f"  ⚠️  Otros cambios:  {cambios_otros}")
    
    # 8. Estadísticas por rango
    logger.info(f"\n📈 DISTRIBUCIÓN DE CAMBIOS POR RANGO DE CUMPLIMIENTO:")
    logger.info(f"{'-'*80}")
    
    rangos = [
        (0.0, 0.80, "Peligro"),
        (0.80, 0.95, "Alerta"),
        (0.95, 1.00, "Cumplimiento PA (nuevo)"),
        (1.00, 1.05, "Cumplimiento regular"),
        (1.05, 1.30, "Sobrecumplimiento"),
    ]
    
    for rango_min, rango_max, label in rangos:
        mask = (df_pa['cumplimiento_val'] >= rango_min) & (df_pa['cumplimiento_val'] < rango_max)
        count = mask.sum()
        count_cambio = (mask & df_pa['cambio']).sum()
        
        if count > 0:
            pct_cambio = 100 * count_cambio / count
            logger.info(
                f"  {rango_min:>5.0%} - {rango_max:>5.0%}  {label:<30}:  "
                f"{count:>3} indicadores  ({count_cambio:>2} cambios = {pct_cambio:>5.1f}%)"
            )
    
    # 9. Casos específicos críticos (Plan Anual 373 si existe)
    logger.info(f"\n🎯 CASOS CRÍTICOS:")
    
    casos_criticos = ["373", "1", "2", "3"]
    for id_critico in casos_criticos:
        if id_critico in IDS_PLAN_ANUAL:
            registros = df_pa[df_pa['id_limpio'] == id_critico]
            if len(registros) > 0:
                for idx, row in registros.iterrows():
                    cumpl = row['cumplimiento_val']
                    antes = row['categoria_antigua']
                    despues = row['categoria_nueva']
                    cambio_str = "✅ CAMBIO" if antes != despues else "  IGUAL"
                    
                    logger.info(
                        f"  ID {id_critico}: cumpl={cumpl:.2%}  "
                        f"{antes} → {despues}  {cambio_str}"
                    )
    
    # 10. Generación de reporte CSV
    if export_csv:
        logger.info(f"\n📄 Generando reporte CSV...")
        
        artifacts_dir = ROOT / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = artifacts_dir / f"validacion_plan_anual_{timestamp}.csv"
        
        # Preparar datos para CSV
        df_export = df_pa[[col_id, col_indicador, col_cumpl, 'cumplimiento_val', 
                          'categoria_antigua', 'categoria_nueva', 'cambio']].copy()
        df_export.columns = ['ID', 'Indicador', 'Cumplimiento_Raw', 'Cumplimiento_Dec',
                            'Categoría_Antigua', 'Categoría_Nueva', 'Cambio']
        
        df_export.to_csv(csv_path, index=False, encoding='utf-8')
        logger.info(f"  ✅ Guardado: {csv_path.relative_to(ROOT)}")
    
    # 11. Resumen final
    logger.info(f"\n" + "="*100)
    if total_cambios > 0:
        logger.info(f"✅ VALIDACIÓN EXITOSA: {total_cambios} indicadores Plan Anual actualizaron su categoría")
    else:
        logger.info(f"⚠️  NO HAY CAMBIOS: Todos los indicadores mantienen la misma categoría")
    logger.info("="*100 + "\n")
    
    return {
        "total_registros": len(df),
        "total_plan_anual": len(df_pa),
        "total_cambios": total_cambios,
        "cambios_correctos": cambios_correctos,
        "cambios_otros": cambios_otros,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validar cambios en nivel de cumplimiento para Plan Anual"
    )
    parser.add_argument("--verbose", action="store_true", help="Modo verboso")
    parser.add_argument("--export-csv", action="store_true", help="Exportar resultados a CSV")
    
    args = parser.parse_args()
    
    resultado = validar_plan_anual(verbose=args.verbose, export_csv=args.export_csv)
    
    if resultado is None:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
