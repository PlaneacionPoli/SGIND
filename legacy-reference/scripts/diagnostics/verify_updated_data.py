#!/usr/bin/env python
from services.strategic_indicators import load_cierres
from services.cmi_filters import load_cmi_worksheet
import pandas as pd

print("="*70)
print("VERIFICACIÓN DE DATOS ACTUALIZADOS EN CIERRES")
print("="*70)

# Cargar datos
cierres = load_cierres()
cmi = load_cmi_worksheet()

# Proyectos del CMI
proy_cmi = cmi[cmi['Proyecto'] == 1]
proy_cmi_ids = set(str(int(x)) if isinstance(x, float) else str(x) for x in proy_cmi['Id'].dropna())

print(f"\n📊 TABLA CIERRES:")
print(f"  - Total registros: {len(cierres)}")
print(f"  - IDs únicos: {cierres['Id'].nunique()}")
print(f"  - Rango de años: {cierres['Anio'].min()}-{cierres['Anio'].max()}")
print(f"  - Columnas: {cierres.columns.tolist()}")

# Todos los IDs en cierres
all_ids_cierres = sorted(cierres['Id'].unique())
print(f"\n📋 PRIMEROS 50 IDs EN CIERRES:")
print(f"  {all_ids_cierres[:50]}")

print(f"\n🎯 PROYECTOS DEL CMI:")
print(f"  - Total proyectos: {len(proy_cmi)}")
print(f"  - IDs: {sorted(proy_cmi_ids)}")

# Buscar coincidencias
coincidencias = set(all_ids_cierres) & proy_cmi_ids
print(f"\n✅ COINCIDENCIAS:")
print(f"  - Proyectos que tienen datos en cierres: {len(coincidencias)}")
if coincidencias:
    print(f"  - IDs coincidentes: {sorted(coincidencias)}")
    
    # Ver datos de esos proyectos
    cierres_proy = cierres[cierres['Id'].isin(coincidencias)]
    print(f"\n📈 DATOS DE PROYECTOS EN CIERRES:")
    print(f"  - Total registros: {len(cierres_proy)}")
    print(f"  - Proyectos con datos: {cierres_proy['Id'].nunique()}")
    print(f"\n  Muestra de datos:")
    print(cierres_proy[['Id', 'Indicador', 'Anio', 'Meta', 'Ejecucion', 'cumplimiento_pct']].head(10))
else:
    print("  ⚠️  NO hay coincidencias entre proyectos CMI e IDs en cierres")
    
    # Buscar si hay IDs que empiecen igual
    print(f"\n  Intentando match parcial...")
    partial_matches = []
    for p_id in proy_cmi_ids:
        for c_id in all_ids_cierres:
            if str(p_id) in str(c_id) or str(c_id) in str(p_id):
                partial_matches.append((p_id, c_id))
    
    if partial_matches:
        print(f"  - Matches parciales encontrados: {len(partial_matches)}")
        print(f"  - Ejemplos: {partial_matches[:10]}")
    else:
        print("  - No hay matches parciales")
