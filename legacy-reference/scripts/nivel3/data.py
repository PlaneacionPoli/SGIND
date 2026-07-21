from pathlib import Path
import pandas as pd
from typing import Optional, List

ROOT = Path(__file__).resolve().parents[2]
DATA_OUTPUT = ROOT / "data" / "output"
ARTIFACTS = DATA_OUTPUT / "artifacts"


def _csv_path(name: str) -> Path:
    return ARTIFACTS / name


def load_timeseries_csv() -> pd.DataFrame:
    p = DATA_OUTPUT / "analytics" / "resultados_consolidados_timeseries.csv"
    if p.exists():
        df = pd.read_csv(p)
        if 'Fecha' in df.columns:
            df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        return df
    # fallback: try excel
    x = DATA_OUTPUT / 'Resultados Consolidados.xlsx'
    if x.exists():
        df = pd.read_excel(str(x), sheet_name='Consolidado Historico', engine='openpyxl')
        df.columns = [str(c).strip() for c in df.columns]
        if 'Fecha' in df.columns:
            df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        return df
    return pd.DataFrame()


def load_latest_csv() -> pd.DataFrame:
    p = ARTIFACTS / 'resultados_consolidados_latest.csv'
    if p.exists():
        df = pd.read_csv(p)
        if 'Fecha' in df.columns:
            df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        return df
    # fallback derive from timeseries
    ts = load_timeseries_csv()
    if not ts.empty and 'Id' in ts.columns and 'Fecha' in ts.columns:
        idx = ts.groupby('Id')['Fecha'].idxmax()
        return ts.loc[idx][['Id', 'Cumplimiento', 'Fecha']]
    return pd.DataFrame()


def load_mapping() -> pd.DataFrame:
    p = ARTIFACTS / 'indicadores_cmi_mapping_v2.csv'
    if p.exists():
        return pd.read_csv(p)
    return pd.DataFrame()


def load_ingesta_artifacts() -> List[dict]:
    p = ARTIFACTS / 'ingesta_20260406_215409.json'
    if p.exists():
        import json
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f).get('detalle', [])
    return []


def expected_ids_for_period(anio: int, mes: int, mapping: Optional[pd.DataFrame] = None) -> List[str]:
    # Heurística: si mapping provided, tomar todos los Ids; filtro por periodicidad no fiable
    if mapping is None or mapping.empty:
        return []
    if 'Id' in mapping.columns:
        return mapping['Id'].astype(str).tolist()
    return []
