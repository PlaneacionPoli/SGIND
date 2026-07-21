import pandas as pd
import re

# Cargar Ficha Técnica (fusionada 2026-07-13 en 'Ficha Tecnica Detalle')
df_ficha = pd.read_excel('data/raw/Catalogo de Indicadores.xlsx', sheet_name='Ficha Tecnica Detalle')
print('=== Análisis de IDs en Ficha Técnica ===')
print(f'Total registros: {len(df_ficha)}')

# Obtener todos los IDs
all_ids = df_ficha["Id Ind"].astype(str).tolist()

# Identificar sub-indicadores (contienen punto)
subindicadores = [id for id in all_ids if '.' in id]
principales = [id for id in all_ids if '.' not in id]

print(f'\nIndicadores con punto: {len(subindicadores)}')
print(f'Indicadores sin punto: {len(principales)}')

# Mostrar ejemplos de sub-indicadores
print(f'\n=== Ejemplos de sub-indicadores ===')
for id in sorted(subindicadores)[:20]:
    print(f'  {id}')

# Verificar patrones
print(f'\n=== Análisis de patrones ===')
pattern1 = [id for id in all_ids if re.match(r'^\d+\.\d+$', id)]  # 521.1
pattern2 = [id for id in all_ids if re.match(r'^\d+\.\d+\.\d+$', id)]  # 521.1.1
pattern3 = [id for id in all_ids if re.match(r'^\d+-\d+$', id)]  # 521-1
pattern4 = [id for id in all_ids if re.match(r'^\d+[A-Za-z]$', id)]  # 521A

print(f'Patrón XXX.Y: {len(pattern1)}')
print(f'Patrón XXX.Y.Z: {len(pattern2)}')
print(f'Patrón XXX-Y: {len(pattern3)}')
print(f'Patrón XXXA: {len(pattern4)}')

# Verificar Catalogo Indicadores (fusionado 2026-07-13, antes 'Indicadores por CMI.xlsx')
df_cmi = pd.read_excel('data/raw/Catalogo de Indicadores.xlsx', sheet_name='Catalogo Indicadores')
print(f'\n=== Análisis de IDs en CMI ===')
print(f'Total registros: {len(df_cmi)}')

all_ids_cmi = df_cmi["Id"].astype(str).tolist()
subindicadores_cmi = [id for id in all_ids_cmi if '.' in id]
principales_cmi = [id for id in all_ids_cmi if '.' not in id]

print(f'Indicadores con punto: {len(subindicadores_cmi)}')
print(f'Indicadores sin punto: {len(principales_cmi)}')

# Mostrar ejemplos
print(f'\n=== Ejemplos de sub-indicadores en CMI ===')
for id in sorted(subindicadores_cmi)[:20]:
    print(f'  {id}')
