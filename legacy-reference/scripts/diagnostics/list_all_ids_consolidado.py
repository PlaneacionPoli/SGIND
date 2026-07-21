#!/usr/bin/env python
"""Ver todos los IDs en Consolidado Cierres"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT_XLSX = ROOT / "data" / "output" / "Resultados Consolidados.xlsx"

df = pd.read_excel(OUT_XLSX, sheet_name="Consolidado Cierres", engine="openpyxl")

print("IDs ACTUALES EN 'Consolidado Cierres':")
print(f"Total IDs únicos: {df['Id'].nunique()}")
print(f"\nRango: {df['Id'].min()} - {df['Id'].max()}")

ids_unicos = sorted(df['Id'].unique())
print(f"\nTodos los IDs ({len(ids_unicos)}):")
print(ids_unicos)

# Verificar si coinciden con CMI
from services.cmi_filters import load_cmi_worksheet
cmi = load_cmi_worksheet()
proy_cmi = cmi[cmi['Proyecto'] == 1]
proy_ids = set(str(int(x)) if isinstance(x, float) else str(x) for x in proy_cmi['Id'].dropna())

consolidado_ids = set(str(x) for x in ids_unicos)
comun = consolidado_ids & proy_ids

print(f"\n¿IDs de proyectos CMI en Consolidado Cierres?")
print(f"Proyectos CMI: {sorted(proy_ids)}")
print(f"Coincidencias: {sorted(comun) if comun else 'NINGUNA'}")
