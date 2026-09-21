"""
scripts/cna_extraction/_factor_utils.py

Helpers puros de parsing de "Factor" ("Factor 3. Desarrollo..." -> 3,
"Desarrollo...") — copia exacta de `_factor_num`/`_factor_nombre` de
services/plan_mejoramiento_loader.py (legacy Streamlit).

Se duplican aquí en vez de importar ese módulo porque
plan_mejoramiento_loader.py depende de `streamlit` (usa `@st.cache_data`)
y no debe arrastrarse esa dependencia al pipeline de extracción, que corre
como script independiente sin la app Streamlit. Mismo patrón exacto ya
usado en backend/app/domain/plan_mejoramiento_builders.py::_factor_num.
"""

from __future__ import annotations

import re

_FACTOR_NUM_RE = re.compile(r"Factor\s+(\d+)", flags=re.IGNORECASE)


def _factor_num(factor_label: str) -> int | None:
    match = _FACTOR_NUM_RE.search(str(factor_label or ""))
    return int(match.group(1)) if match else None


def _factor_nombre(factor_label: str) -> str:
    text = str(factor_label or "")
    return text.split(".", 1)[1].strip() if "." in text else text.strip()
