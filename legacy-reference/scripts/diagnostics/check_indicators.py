import pandas as pd

# Cargar consolidado API
df_api = pd.read_excel('data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx')
print('=== Consolidado API Kawak ===')
print(f'Total registros: {len(df_api)}')
print(f'IDs unicos: {df_api["ID"].nunique()}')
print(f'Primeros 10 IDs: {sorted(df_api["ID"].unique())[:10]}')

# Cargar catálogo Kawak
df_kawak = pd.read_excel('data/raw/Fuentes Consolidadas/Indicadores Kawak.xlsx')
print('\n=== Indicadores Kawak ===')
print(f'Total registros: {len(df_kawak)}')
print(f'IDs unicos: {df_kawak["Id"].nunique()}')
print(f'Columnas: {list(df_kawak.columns)}')

# Verificar si hay otros archivos de indicadores
import os
raw_path = 'data/raw'
for root, dirs, files in os.walk(raw_path):
    for f in files:
        if 'indicador' in f.lower() or 'cmi' in f.lower():
            print(f'\nArchivo encontrado: {os.path.join(root, f)}')
