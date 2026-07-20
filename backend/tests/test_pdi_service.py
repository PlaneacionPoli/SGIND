import pandas as pd
import pytest

from app.domain.categorization import categorizar_cumplimiento
from app.services.pdi_service import _classify_estado


@pytest.mark.parametrize(
    ("cumpl_pct", "id_indicador"),
    [
        (110.0, None),
        (102.0, None),
        (95.0, None),
        (70.0, None),
        (None, None),
        (96.0, "373"),  # id de plan anual: escala de umbrales distinta
        (90.0, "373"),
    ],
)
def test_classify_estado_matches_categorizar_cumplimiento(cumpl_pct, id_indicador):
    esperado = categorizar_cumplimiento(
        cumpl_pct / 100 if pd.notna(cumpl_pct) else cumpl_pct,
        id_indicador=id_indicador,
    )
    assert _classify_estado(cumpl_pct, id_indicador) == esperado


def test_classify_estado_sin_dato_para_nan():
    assert _classify_estado(float("nan")) == "Sin dato"
