from pathlib import Path
import json
from datetime import datetime
from typing import Optional, List, Dict

ROOT = Path(__file__).resolve().parents[2]
OM_DIR = ROOT / 'data' / 'output' / 'artifacts' / 'om'
OM_DIR.mkdir(parents=True, exist_ok=True)


def _om_path(om_id: str) -> Path:
    return OM_DIR / f"om_{om_id}.json"


def list_oms() -> List[Dict]:
    res = []
    for p in sorted(OM_DIR.glob('om_*.json')):
        try:
            with open(p, 'r', encoding='utf-8') as f:
                res.append(json.load(f))
        except Exception:
            continue
    return res


def create_om(indicador_id: str, titulo: str, descripcion: str, responsable: str, fecha_compromiso: Optional[str] = None) -> Dict:
    now = datetime.utcnow().isoformat()
    om_id = f"{int(datetime.utcnow().timestamp())}"
    obj = {
        'id_om': om_id,
        'indicador_id': str(indicador_id),
        'titulo': titulo,
        'descripcion': descripcion,
        'responsable': responsable,
        'estado': 'Abierto',
        'fecha_creacion': now,
        'fecha_compromiso': fecha_compromiso,
        'fecha_cierre': None,
    }
    p = _om_path(om_id)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return obj


def update_om(om_id: str, **changes) -> Optional[Dict]:
    p = _om_path(om_id)
    if not p.exists():
        return None
    with open(p, 'r', encoding='utf-8') as f:
        obj = json.load(f)
    obj.update(changes)
    # if estado changed to Cerrado and no fecha_cierre, set now
    if obj.get('estado') == 'Cerrado' and not obj.get('fecha_cierre'):
        obj['fecha_cierre'] = datetime.utcnow().isoformat()
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return obj


def get_om(om_id: str) -> Optional[Dict]:
    p = _om_path(om_id)
    if not p.exists():
        return None
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)
