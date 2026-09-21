"""
scripts/etl/config.py
Configuración centralizada del ETL.

Lee desde config/settings.toml (sección [business]) para que el cambio anual
NO requiera editar código Python.

Fallback: core/config.py → valores hardcodeados por defecto.
"""
from __future__ import annotations

import html as _html_mod
import re
import sys
from pathlib import Path
from typing import Dict, FrozenSet

_ROOT = Path(__file__).parent.parent.parent  # raíz del proyecto


# ── Lector de settings.toml ────────────────────────────────────────
def _load_toml(path: Path) -> dict:
    try:
        try:
            import tomllib          # Python 3.11+
        except ImportError:
            import tomli as tomllib  # pip install tomli  (Python 3.8-3.10)
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


_SETTINGS: dict = _load_toml(_ROOT / "config" / "settings.toml")
_BIZ: dict = _SETTINGS.get("business", {})

# ── AÑO_CIERRE_ACTUAL ─────────────────────────────────────────────
AÑO_CIERRE_ACTUAL: int = int(_BIZ.get("año_cierre", 2025))

# ── IDs especiales ────────────────────────────────────────────────
_DEFAULT_PLAN_ANUAL = [
    "373", "390", "414", "415", "416", "417",
    "418", "420", "469", "470", "471",
]
_DEFAULT_TOPE_100 = ["208", "218", "92", "104", "106", "124", "125", "126", "127", "128", "272"]

# Intentar importar desde core/config.py primero (fuente de verdad de la app)
_core_plan: FrozenSet[str] | None = None
_core_tope: FrozenSet[str] | None = None
try:
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
    from core.config import IDS_PLAN_ANUAL as _cp, IDS_TOPE_100 as _ct
    _core_plan = _cp
    _core_tope = _ct
except ImportError:
    pass

if _core_plan is not None:
    IDS_PLAN_ANUAL: FrozenSet[str] = _core_plan
else:
    IDS_PLAN_ANUAL = frozenset(
        str(x) for x in _BIZ.get("ids_plan_anual", _DEFAULT_PLAN_ANUAL)
    )

if _core_tope is not None:
    IDS_TOPE_100: FrozenSet[str] = _core_tope
else:
    IDS_TOPE_100 = frozenset(
        str(x) for x in _BIZ.get("ids_tope_100", _DEFAULT_TOPE_100)
    )

# ── Series → sub-indicadores ──────────────────────────────────────
def _cargar_series_subindicadores() -> Dict[str, str]:
    """Carga config/series_subindicadores.toml → {"420.1": "SGC", ...}"""
    raw = _load_toml(_ROOT / "config" / "series_subindicadores.toml")
    return {str(k): str(v) for k, v in raw.get("subindicadores", {}).items()}


def _normalizar_nombre_serie(nombre: str) -> str:
    """Normaliza serie para comparación resistente a encoding:
    1. Decodifica entidades HTML (&oacute; → ó).
    2. Reemplaza NBSP y caracteres de reemplazo Unicode (U+FFFD).
    3. Descarta caracteres no-ASCII (tildes/acentos → vacío).
    4. Lowercase + colapsa espacios múltiples.
    """
    s = _html_mod.unescape(str(nombre).strip())
    s = s.replace("\xa0", " ").replace("�", "")
    s = s.encode("ascii", errors="ignore").decode("ascii")
    return re.sub(r"\s+", " ", s.lower().strip())


SERIES_SUBINDICADORES_MAP: Dict[str, str] = _cargar_series_subindicadores()

# Índice inverso: parent_id → {nombre_normalizado → sub_id}
_PARENT_SERIES_INDEX: Dict[str, Dict[str, str]] = {}
for _sub_id, _serie_nombre in SERIES_SUBINDICADORES_MAP.items():
    _parent = _sub_id.split(".")[0]
    _PARENT_SERIES_INDEX.setdefault(_parent, {})[
        _normalizar_nombre_serie(_serie_nombre)
    ] = _sub_id


# ── Cronograma de proyectos estratégicos ─────────────────────────
def _cargar_cronograma_proyectos():
    """Carga [cronograma_proyectos] del TOML.
    Retorna:
        padres: {año_int → id_padre_str}   ej. {2025: "509"}
        series: {nombre_serie_norm → id_proyecto_str}
    """
    raw = _load_toml(_ROOT / "config" / "series_subindicadores.toml")
    cp = raw.get("cronograma_proyectos", {})
    padres: Dict[int, str] = {
        int(yr): str(pid) for yr, pid in cp.get("padres", {}).items()
    }
    series: Dict[str, str] = {
        _normalizar_nombre_serie(k): str(v)
        for k, v in cp.get("series", {}).items()
    }
    return padres, series


CRONOGRAMA_PADRES: Dict[int, str]
_CRONOGRAMA_SERIES_FLAT: Dict[str, str]
CRONOGRAMA_PADRES, _CRONOGRAMA_SERIES_FLAT = _cargar_cronograma_proyectos()
# Alias público para uso externo (valores = IDs de proyectos, ej. "910")
CRONOGRAMA_SERIES_FLAT: Dict[str, str] = _CRONOGRAMA_SERIES_FLAT

# ── Rutas ─────────────────────────────────────────────────────────
BASE_PATH = _ROOT / "data" / "raw"
OUTPUT_DIR = _ROOT / "data" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE        = BASE_PATH / "Resultados_Consolidados_Fuente.xlsx"
OUTPUT_FILE       = OUTPUT_DIR / "Resultados Consolidados.xlsx"
KAWAK_CAT_FILE    = BASE_PATH / "Fuentes Consolidadas" / "Indicadores Kawak.xlsx"
CONSOLIDADO_API_KW = BASE_PATH / "Fuentes Consolidadas" / "Consolidado_API_Kawak.xlsx"

# Directorio maestro de indicadores (fusión 2026-07-14): hoja 'Catalogo
# Indicadores' + 'Ficha Tecnica Detalle'. Archivo separado de INPUT_FILE
# (que sigue siendo la fuente de Consolidado Historico/Semestral/Cierres).
CATALOGO_MAESTRO_FILE = BASE_PATH / "Catalogo de Indicadores.xlsx"
