from typing import List
import pandas as pd
from .data import load_ingesta_artifacts


def aggregate_qc() -> pd.DataFrame:
    artifacts = load_ingesta_artifacts()
    rows = []
    for a in artifacts:
        plantilla = a.get('plantilla') or a.get('template') or 'unknown'
        errores = a.get('errores') or a.get('errors') or []
        if isinstance(errores, dict):
            for k, v in errores.items():
                rows.append({'plantilla': plantilla, 'tipo': k, 'count': int(v or 0)})
        elif isinstance(errores, list):
            for e in errores:
                rows.append({'plantilla': plantilla, 'tipo': str(e), 'count': 1})
        else:
            # no structured errors
            rows.append({'plantilla': plantilla, 'tipo': 'unknown', 'count': 0})
    if not rows:
        return pd.DataFrame(columns=['plantilla', 'tipo', 'count'])
    df = pd.DataFrame(rows)
    return df.groupby(['plantilla','tipo'], as_index=False).sum()


def qc_for_artifact(artifact_id: str):
    artifacts = load_ingesta_artifacts()
    for a in artifacts:
        if a.get('archivo') == artifact_id or a.get('file') == artifact_id:
            return a.get('errores') or a.get('errors') or {}
    return {}
