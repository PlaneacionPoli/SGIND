from typing import List
import pandas as pd

def compute_expected_ids_for_period(year: int, month: int, mapping: pd.DataFrame) -> List[str]:
    if mapping is None or mapping.empty:
        return []
    if 'Id' in mapping.columns:
        return mapping['Id'].astype(str).tolist()
    return []


def compute_reporting_status(latest_df: pd.DataFrame, expected_ids: List[str], window_months: int = 1) -> pd.DataFrame:
    # latest_df expected to contain columns: Id, Fecha
    import pandas as pd
    df = pd.DataFrame({'Id': [str(i) for i in expected_ids]})
    if latest_df is None or latest_df.empty:
        df['ÚltimaFecha'] = pd.NaT
        df['Estado'] = 'Pendiente'
        return df

    lng = latest_df.copy()
    if 'Id' in lng.columns:
        lng['Id'] = lng['Id'].astype(str)
    if 'Fecha' in lng.columns:
        lng['Fecha'] = pd.to_datetime(lng['Fecha'], errors='coerce')
    last = lng.groupby('Id', as_index=False).agg({'Fecha': 'max'}).rename(columns={'Fecha': 'ÚltimaFecha'})
    df = df.merge(last, on='Id', how='left')
    # Determine status: if ÚltimaFecha within window_months -> Actualizado, else Pendiente
    now = pd.Timestamp.now()
    def status_row(r):
        if pd.isna(r['ÚltimaFecha']):
            return 'Pendiente'
        months = (now.year - r['ÚltimaFecha'].year) * 12 + (now.month - r['ÚltimaFecha'].month)
        return 'Actualizado' if months <= window_months else 'Pendiente'

    df['Estado'] = df.apply(status_row, axis=1)
    return df
