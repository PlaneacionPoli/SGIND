#!/usr/bin/env python
"""Cargar hoja Consolidado Cierres desde Resultados Consolidados.xlsx"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT_XLSX = ROOT / "data" / "output" / "Resultados Consolidados.xlsx"

print("="*70)
print("CARGA: CONSOLIDADO CIERRES")
print("="*70)

if not OUT_XLSX.exists():
    print(f"❌ Archivo no existe: {OUT_XLSX}")
else:
    print(f"✓ Archivo encontrado: {OUT_XLSX}")
    
    # Ver hojas disponibles
    xl = pd.ExcelFile(OUT_XLSX, engine="openpyxl")
    print(f"\nHojas disponibles ({len(xl.sheet_names)}):")
    for sheet in xl.sheet_names:
        print(f"  - {sheet}")
    
    # Intentar cargar "Consolidado Cierres"
    target_sheet = "Consolidado Cierres"
    if target_sheet in xl.sheet_names:
        print(f"\n✓ Hoja '{target_sheet}' ENCONTRADA")
        
        df = pd.read_excel(OUT_XLSX, sheet_name=target_sheet, engine="openpyxl")
        print(f"\n📊 Datos de {target_sheet}:")
        print(f"   - Filas: {len(df)}")
        print(f"   - Columnas: {df.shape[1]}")
        print(f"   - Columnas: {df.columns.tolist()}")
        
        # Buscar IDs de proyectos
        if "Id" in df.columns:
            proy_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 900, 901, 902, 903, 904]
            df['Id_str'] = df['Id'].astype(str)
            
            matches = df[df['Id_str'].isin([str(x) for x in proy_ids])]
            print(f"\n🎯 IDs de proyectos encontrados:")
            print(f"   - Total registros: {len(matches)}")
            print(f"   - IDs únicos: {matches['Id'].nunique()}")
            
            if len(matches) > 0:
                print(f"\n   Primeros 10 registros de proyectos:")
                cols_to_show = ['Id', 'Indicador', 'Meta', 'Ejecucion', 'cumplimiento_pct', 'Linea', 'Objetivo']
                cols_available = [c for c in cols_to_show if c in matches.columns]
                print(matches[cols_available].head(10).to_string())
                
                print(f"\n   Distribución de proyectos:")
                print(matches['Id'].value_counts().sort_index().to_string())
            else:
                print("   ⚠️  No hay coincidencias")
        else:
            print("   ⚠️  No hay columna 'Id'")
    else:
        print(f"\n❌ Hoja '{target_sheet}' NO ENCONTRADA")
        
        # Buscar alternativas
        consolidado_sheets = [s for s in xl.sheet_names if "consolidado" in s.lower()]
        if consolidado_sheets:
            print(f"\nHojas similares encontradas:")
            for s in consolidado_sheets:
                print(f"  - {s}")
