import pandas as pd

# Cargar Catalogo Indicadores (fusionado 2026-07-13, antes 'Indicadores por CMI.xlsx')
try:
    df_cmi = pd.read_excel('data/raw/Catalogo de Indicadores.xlsx', sheet_name='Catalogo Indicadores')
    print('=== Catalogo Indicadores ===')
    print(f'Total registros: {len(df_cmi)}')
    print(f'Columnas: {list(df_cmi.columns)}')
    print(f'Primeras 5 filas:')
    print(df_cmi.head())
except Exception as e:
    print(f'Error cargando Indicadores por CMI: {e}')

print('\n' + '='*60)

# Cargar Ficha Técnica (fusionada 2026-07-13 en 'Ficha Tecnica Detalle')
try:
    df_ficha = pd.read_excel('data/raw/Catalogo de Indicadores.xlsx', sheet_name='Ficha Tecnica Detalle')
    print('=== Ficha Técnica Indicadores ===')
    print(f'Total registros: {len(df_ficha)}')
    print(f'Columnas: {list(df_ficha.columns)}')
    print(f'Primeras 5 filas:')
    print(df_ficha.head())
except Exception as e:
    print(f'Error cargando Ficha Técnica: {e}')
