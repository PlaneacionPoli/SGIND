import pandas as pd

# Cargar Ficha Técnica (fusionada 2026-07-13 en 'Ficha Tecnica Detalle')
df_ficha = pd.read_excel('data/raw/Catalogo de Indicadores.xlsx', sheet_name='Ficha Tecnica Detalle')
print('=== Ficha Técnica Indicadores ===')
print(f'Total registros: {len(df_ficha)}')
print(f'\nColumnas relevantes:')
print(f'  - Id Ind: {df_ficha["Id Ind"].nunique()} valores únicos')
print(f'  - ID Kawak: {df_ficha["ID Kawak"].nunique()} valores únicos')

# Verificar cuántos tienen datos válidos
print(f'\n=== Calidad de Datos ===')
for col in ["Id Ind", "ID Kawak", "Nombre del indicador", "Formula", "Responsable del calculo"]:
    if col in df_ficha.columns:
        valid = df_ficha[col].notna().sum()
        print(f'  {col}: {valid} de {len(df_ficha)} ({valid/len(df_ficha)*100:.1f}%)')

# Mostrar algunos ejemplos
print(f'\n=== Primeros 5 registros ===')
print(df_ficha[["Id Ind", "ID Kawak", "Nombre del indicador"]].head())

# Verificar IDs únicos
all_ids = set()
if "Id Ind" in df_ficha.columns:
    all_ids.update(df_ficha["Id Ind"].dropna().unique())
if "ID Kawak" in df_ficha.columns:
    all_ids.update(df_ficha["ID Kawak"].dropna().unique())
print(f'\nTotal IDs únicos combinados: {len(all_ids)}')
