"""Script para integrar y normalizar el archivo de Resultados Consolidados.

Genera:
- data/output/analytics/resultados_consolidados_timeseries.csv  (series completas)
- data/output/artifacts/resultados_consolidados_latest.csv     (último registro por indicador)

Uso:
    python scripts/integrate_consolidado.py
"""
from pathlib import Path
import pandas as pd


def main():
    root = Path(__file__).resolve().parents[1]
    xlsx = root / 'data' / 'output' / 'Resultados Consolidados.xlsx'
    if not xlsx.exists():
        print('Archivo de consolidados no encontrado:', xlsx)
        return

    xl = pd.ExcelFile(xlsx)
    # prefer sheet named 'Consolidado Historico' else first
    sheet = 'Consolidado Historico' if 'Consolidado Historico' in xl.sheet_names else xl.sheet_names[0]
    df = xl.parse(sheet)

    # Normalizar nombres
    df.columns = [c.strip() for c in df.columns]
    # Asegurar columnas mínimas
    required = ['Id', 'Indicador', 'Fecha', 'Cumplimiento', 'Proceso']
    for r in required:
        if r not in df.columns:
            print(f'Columna requerida no encontrada: {r}')
    # Parse fecha y cumplimiento
    if 'Fecha' in df.columns:
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    if 'Cumplimiento' in df.columns:
        df['Cumplimiento'] = pd.to_numeric(df['Cumplimiento'], errors='coerce')

    # Crear carpetas de salida
    out_analytics = root / 'data' / 'output' / 'analytics'
    out_artifacts = root / 'data' / 'output' / 'artifacts'
    out_analytics.mkdir(parents=True, exist_ok=True)
    out_artifacts.mkdir(parents=True, exist_ok=True)

    # Guardar series completas
    timeseries_file = out_analytics / 'resultados_consolidados_timeseries.csv'
    df.to_csv(timeseries_file, index=False)
    print('Saved timeseries to', timeseries_file)

    # Obtener último registro por Id (por Fecha más reciente)
    if 'Fecha' in df.columns:
        idx = df.groupby('Id')['Fecha'].idxmax()
        latest = df.loc[idx].copy()
    else:
        latest = df.drop_duplicates(subset=['Id']).copy()

    latest_file = out_artifacts / 'resultados_consolidados_latest.csv'
    latest.to_csv(latest_file, index=False)
    print('Saved latest per Id to', latest_file)


if __name__ == '__main__':
    main()
