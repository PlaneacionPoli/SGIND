#!/usr/bin/env python
"""Verificación final: Proyectos cargan desde Consolidado Cierres actualizado"""

from services.strategic_indicators import load_proyectos_consolidados
from services.cmi_filters import load_cmi_worksheet
import pandas as pd

print("="*70)
print("VERIFICACIÓN FINAL: CARGA DE PROYECTOS")
print("="*70)

# 1. Cargar IDs de proyectos del CMI
cmi = load_cmi_worksheet()
proy_cmi = cmi[cmi['Proyecto'] == 1]
proy_ids = set(str(int(x)) if isinstance(x, float) else str(x) for x in proy_cmi['Id'].dropna())

print(f"\n1. PROYECTOS DEL CMI:")
print(f"   Total: {len(proy_cmi)}")
print(f"   IDs: {sorted(proy_ids)}")

# 2. Cargar Consolidado Cierres (nueva función)
print(f"\n2. CARGAR CONSOLIDADO CIERRES:")
consolidado = load_proyectos_consolidados()
print(f"   Total registros: {len(consolidado)}")
print(f"   Columnas: {consolidado.columns.tolist()[:10]}...")

# 3. Filtrar por proyectos
if not consolidado.empty and "Id" in consolidado.columns:
    consolidado["Id"] = consolidado["Id"].astype(str)
    proyectos_data = consolidado[consolidado["Id"].isin(proy_ids)].copy()
    
    print(f"\n3. PROYECTOS CON DATOS EN CONSOLIDADO CIERRES:")
    print(f"   Total registros encontrados: {len(proyectos_data)}")
    print(f"   IDs únicos: {proyectos_data['Id'].nunique()}")
    
    if len(proyectos_data) > 0:
        print(f"\n4. MUESTRA DE DATOS (primeros 10 registros):")
        cols_muestra = ['Id', 'Indicador', 'Meta', 'Ejecucion', 'cumplimiento_pct', 'Linea', 'Objetivo']
        cols_available = [c for c in cols_muestra if c in proyectos_data.columns]
        print(proyectos_data[cols_available].head(10).to_string())
        
        # Estadísticas
        print(f"\n5. ESTADÍSTICAS DE CUMPLIMIENTO:")
        print(f"   Promedio cumplimiento: {proyectos_data['cumplimiento_pct'].mean():.2f}%")
        print(f"   Mínimo: {proyectos_data['cumplimiento_pct'].min():.2f}%")
        print(f"   Máximo: {proyectos_data['cumplimiento_pct'].max():.2f}%")
        
        print(f"\n6. DISTRIBUCIÓN POR LÍNEA:")
        if 'Linea' in proyectos_data.columns:
            lineas = proyectos_data.groupby('Linea')['Id'].nunique()
            print(lineas.to_string())
        
        print(f"\n✅ ÉXITO: {len(proyectos_data)} registros de proyectos listos para dashboard")
    else:
        print("   ❌ No hay datos")
else:
    print("   ❌ Error al cargar consolidado")

print("\n" + "="*70)
