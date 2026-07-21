from typing import List, Dict
from .data import load_ingesta_artifacts


def list_artifacts_for_id(ind_id: str) -> List[Dict]:
    artifacts = load_ingesta_artifacts()
    res = []
    for a in artifacts:
        # Heurística: buscar campos comunes donde aparecería el Id
        found = False
        if isinstance(a, dict):
            # buscar en keys/values
            for v in a.values():
                try:
                    if isinstance(v, list):
                        for r in v:
                            if isinstance(r, dict) and any(str(r.get(k, '')).strip() == str(ind_id) for k in ('Id','id','ID')):
                                found = True
                                break
                    else:
                        if str(v).strip() == str(ind_id):
                            found = True
                            break
                except Exception:
                    continue
        if found:
            res.append(a)
    return res


def artifact_summary(artifact: Dict) -> Dict:
    # Resumen ligero para la UI
    return {
        'archivo': artifact.get('archivo') or artifact.get('file') or artifact.get('name'),
        'plantilla': artifact.get('plantilla') or artifact.get('template'),
        'registros_leidos': artifact.get('registros_leidos') or artifact.get('records', 0),
        'exitosa': artifact.get('exitosa', True),
    }
