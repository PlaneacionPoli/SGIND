import pandas as pd
import json
import os

def analyze():
    # Fusionado 2026-07-13: Catalogo_Indicadores y Ficha_Tecnica ahora son hojas
    # de Resultados_Consolidados_Fuente.xlsx (antes 'Indicadores por CMI.xlsx' y
    # 'Ficha_Tecnica_Indicadores.xlsx').
    files = {
        'Dataset_Unificado': ('data/raw/Dataset_Unificado.xlsx', None),
        'Ficha_Tecnica': ('data/raw/Catalogo de Indicadores.xlsx', 'Ficha Tecnica Detalle'),
        'Indicadores_CMI': ('data/raw/Catalogo de Indicadores.xlsx', 'Catalogo Indicadores'),
    }

    info = {}
    for name, (path, sheet) in files.items():
        if os.path.exists(path):
            df = pd.read_excel(path, sheet_name=sheet or 0, nrows=5)
            info[name] = {
                'columns': list(df.columns),
                'sample': df.head(1).to_dict('records')
            }
        else:
            info[name] = 'File not found'
            
    print(json.dumps(info, indent=2, default=str))

if __name__ == '__main__':
    analyze()
