#!/usr/bin/env python
"""
Diagnóstico para el error: ValueError: The column label 'Id' is not unique

Este script verifica si hay columnas duplicadas en los DataFrames de Proyectos
antes de que lleguen a _compute_trends.
"""

import sys
sys.path.insert(0, r".")

import pandas as pd
from services.strategic_indicators import load_proyectos_consolidados, load_worksheet_flags, preparar_pdi_con_cierre
from services.cmi_filters import load_cmi_worksheet

print("\n" + "="*80)
print("DIAGNÓSTICO: Verificación de columnas duplicadas en Proyectos")
print("="*80)

def _get_proyectos_ids():
    df = load_cmi_worksheet()
    if df.empty or "Proyecto" not in df.columns or "Id" not in df.columns:
        return set()
    return set(str(int(x)) if isinstance(x, float) else str(x).strip() for x in df.loc[df["Proyecto"] == 1, "Id"].dropna())

def _clean_duplicates(df):
    """Elimina TODAS las columnas duplicadas, manteniendo solo la primera."""
    if df.empty or not df.columns.duplicated().any():
        return df
    keep_idx = ~df.columns.duplicated(keep='first')
    return df.iloc[:, keep_idx].copy()

# 1. Verificar load_proyectos_consolidados
print("\n[1] Verificar load_proyectos_consolidados()")
consolidado = load_proyectos_consolidados()
print(f"    Shape: {consolidado.shape}")
print(f"    Columnas: {len(consolidado.columns)}")
print(f"    Duplicadas: {consolidado.columns.duplicated().any()}")
if consolidado.columns.duplicated().any():
    print(f"    DUPLICADOS ENCONTRADOS: {consolidado.columns[consolidado.columns.duplicated()].tolist()}")
    sys.exit(1)

# 2. Verificar filtrado por IDs de proyectos
print("\n[2] Verificar filtrado por IDs de proyectos")
ids_proy = _get_proyectos_ids()
print(f"    IDs de proyectos: {len(ids_proy)}")
consolidado["Id"] = consolidado["Id"].astype(str)
pdi_proy = consolidado[consolidado["Id"].isin(ids_proy)].copy()
print(f"    Después de filtrar: {pdi_proy.shape}")
print(f"    Duplicadas: {pdi_proy.columns.duplicated().any()}")
if pdi_proy.columns.duplicated().any():
    print(f"    DUPLICADOS ENCONTRADOS: {pdi_proy.columns[pdi_proy.columns.duplicated()].tolist()}")
    sys.exit(1)

# 3. Verificar después de merge con Linea/Objetivo
print("\n[3] Verificar después de merge con metadata")
if not pdi_proy.empty and ("Linea" not in pdi_proy.columns or pdi_proy["Linea"].isna().all()):
    base = load_worksheet_flags()
    if not base.empty:
        base_norm = base.copy()
        base_norm["Id"] = base_norm["Id"].astype(str)
        merge_cols = [c for c in ["Linea", "Objetivo"] if c in base_norm.columns]
        if merge_cols:
            base_to_merge = base_norm[["Id"] + merge_cols].drop_duplicates(subset=["Id"])
            pdi_proy = pdi_proy.merge(base_to_merge, on="Id", how="left", suffixes=("", "_cmi"))
            
            # Resolver sufijos
            for col in pdi_proy.columns:
                if col.endswith("_cmi"):
                    base_col = col[:-4]
                    if base_col in pdi_proy.columns:
                        pdi_proy[base_col] = pdi_proy[base_col].fillna(pdi_proy[col])
                    pdi_proy = pdi_proy.drop(col, axis=1)

print(f"    Después de merge: {pdi_proy.shape}")
print(f"    Duplicadas: {pdi_proy.columns.duplicated().any()}")
if pdi_proy.columns.duplicated().any():
    print(f"    DUPLICADOS ENCONTRADOS: {pdi_proy.columns[pdi_proy.columns.duplicated()].tolist()}")
    sys.exit(1)

# 4. Verificar después de deduplicación
print("\n[4] Verificar después de deduplicación")
pdi_proy = pdi_proy.sort_values("Id", na_position="last").drop_duplicates(subset=["Id"], keep="last")
print(f"    Después de dedup: {pdi_proy.shape}")
print(f"    Duplicadas: {pdi_proy.columns.duplicated().any()}")
if pdi_proy.columns.duplicated().any():
    print(f"    DUPLICADOS ENCONTRADOS: {pdi_proy.columns[pdi_proy.columns.duplicated()].tolist()}")
    sys.exit(1)

# 5. Verificar después de limpiar con _clean_duplicates
print("\n[5] Verificar después de limpiar con _clean_duplicates()")
pdi_proy = _clean_duplicates(pdi_proy)
print(f"    Después de _clean_duplicates: {pdi_proy.shape}")
print(f"    Duplicadas: {pdi_proy.columns.duplicated().any()}")
if pdi_proy.columns.duplicated().any():
    print(f"    DUPLICADOS ENCONTRADOS: {pdi_proy.columns[pdi_proy.columns.duplicated()].tolist()}")
    sys.exit(1)

# 6. Verificar datos previos
print("\n[6] Verificar datos previos")
prev_df = preparar_pdi_con_cierre(2024, 12)
print(f"    Prev: {prev_df.shape if prev_df is not None else 'None'}")
if prev_df is not None and not prev_df.empty:
    print(f"    Duplicadas: {prev_df.columns.duplicated().any()}")
    if prev_df.columns.duplicated().any():
        print(f"    DUPLICADOS ENCONTRADOS: {prev_df.columns[prev_df.columns.duplicated()].tolist()}")
    
    # Filtrar por proyectos
    if "Id" in prev_df.columns:
        prev_df = prev_df[prev_df["Id"].astype(str).isin(ids_proy)].copy()
    else:
        prev_df = pd.DataFrame()
    
    prev_df = _clean_duplicates(prev_df)
    print(f"    Prev filtrado: {prev_df.shape}")
    print(f"    Duplicadas: {prev_df.columns.duplicated().any()}")
    if prev_df.columns.duplicated().any():
        print(f"    DUPLICADOS ENCONTRADOS: {prev_df.columns[prev_df.columns.duplicated()].tolist()}")

# 7. Verificar que el merge funcionaría
print("\n[7] Simular merge en _compute_trends")
if not pdi_proy.empty and not prev_df.empty:
    try:
        cols_to_select = ["Id", "Indicador", "cumplimiento_pct"]
        cols_to_select = [c for c in cols_to_select if c in pdi_proy.columns]
        
        cur = pdi_proy[cols_to_select].dropna(subset=["cumplimiento_pct"]).copy()
        print(f"    cur: {cur.shape}")
        print(f"    cur duplicadas: {cur.columns.duplicated().any()}")
        
        prev = prev_df[["Id", "cumplimiento_pct"]].dropna(subset=["cumplimiento_pct"]).copy()
        print(f"    prev: {prev.shape}")
        print(f"    prev duplicadas: {prev.columns.duplicated().any()}")
        
        merged = cur.merge(prev, on="Id", suffixes=("", "_prev"))
        print(f"    Merge OK: {merged.shape}")
    except Exception as e:
        print(f"    ERROR en merge: {e}")
        sys.exit(1)

print("\n" + "="*80)
print("[OK] DIAGNÓSTICO COMPLETADO - NO HAY COLUMNAS DUPLICADAS")
print("="*80 + "\n")
