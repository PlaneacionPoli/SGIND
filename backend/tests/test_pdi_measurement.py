"""Casos de prueba del prompt de auditoría del Informe Ejecutivo (2026-09-27)."""

from app.domain.pdi_measurement import (
    IndicadorInput,
    ProyectoInput,
    calcular_consolidado_linea,
    calcular_global,
    calcular_perspectiva_indicadores,
    calcular_perspectiva_proyectos,
    clasificar_semaforo,
)
from app.domain.pdi_validation import (
    validar_consolidados_linea,
    validar_global,
    validar_proyectos_crudo,
)


def test_educacion_tres_proyectos_stand_by_consolidado_dos_perspectivas():
    proyectos = [
        ProyectoInput("P1", "educacion", "Stand by", 100.0),
        ProyectoInput("P2", "educacion", "Stand by", 40.0),
        ProyectoInput("P3", "educacion", "Stand by", 0.0),
    ]
    indicadores = [IndicadorInput("I1", "educacion", 1, 1, cumplimiento_pct=107.8)]
    resultado = calcular_consolidado_linea(
        "educacion", retos_cumplimiento=94.7, proyectos=proyectos, indicadores=indicadores
    )
    assert resultado.proyectos.disponible is False
    assert resultado.proyectos.n_excluidos == 3
    assert resultado.consolidado == round((94.7 + 107.8) / 2, 2)


def test_expansion_regresion_100_100_67_21():
    proyectos = [
        ProyectoInput("A", "expansion", "Cerrado", 100.0),
        ProyectoInput("B", "expansion", "En ejecución", 100.0),
        ProyectoInput("C", "expansion", "En ejecución", 67.0),
        ProyectoInput("D", "expansion", "Planeación", 21.0),
    ]
    res = calcular_perspectiva_proyectos(proyectos)
    assert res.promedio == 72.0


def test_proyecto_112_se_topa_a_100():
    proyectos = [ProyectoInput("A", "calidad", "Cerrado", 112.0)]
    res = calcular_perspectiva_proyectos(proyectos)
    assert res.promedio == 100.0
    assert "A" in res.tope_aplicado_a


def test_promedio_proyectos_100_100_112_50_topado_es_87_5():
    proyectos = [
        ProyectoInput("A", "calidad", "Cerrado", 100.0),
        ProyectoInput("B", "calidad", "Cerrado", 100.0),
        ProyectoInput("C", "calidad", "Cerrado", 112.0),
        ProyectoInput("D", "calidad", "En ejecución", 50.0),
    ]
    res = calcular_perspectiva_proyectos(proyectos)
    assert res.promedio == 87.5
    assert "C" in res.tope_aplicado_a


def test_proyecto_standby_con_avance_100_excluido_v5_prima():
    proyectos = [
        ProyectoInput("A", "calidad", "Stand by", 100.0),
        ProyectoInput("B", "calidad", "Cerrado", 80.0),
    ]
    res = calcular_perspectiva_proyectos(proyectos)
    assert res.n_incluidos == 1
    assert res.promedio == 80.0
    assert "A" in res.excluidos_detalle


def test_indicador_sin_meta_excluido_y_contado_aparte():
    indicadores = [
        IndicadorInput("I1", "calidad", meta=None, ejecucion=None, cumplimiento_pct=None),
        IndicadorInput("I2", "calidad", meta=100, ejecucion=90, cumplimiento_pct=90.0),
    ]
    res = calcular_perspectiva_indicadores(indicadores)
    assert res.n_incluidos == 1
    assert res.n_excluidos == 1
    assert "I1" in res.excluidos_detalle
    assert res.promedio == 90.0


def test_greenmetric_menor_mejor_con_tope():
    # meta 25, ejecucion 13 (menor es mejor) -> cumplimiento ya resuelto
    # aguas arriba como 25/13*100 = 192.3, el módulo solo aplica el tope 130.
    indicador = IndicadorInput(
        "GreenMetric", "sostenibilidad", meta=25, ejecucion=13, direccion="menor_mejor",
        cumplimiento_pct=round(25 / 13 * 100, 1),
    )
    res = calcular_perspectiva_indicadores([indicador])
    assert res.promedio == 130.0
    assert "GreenMetric" in res.tope_aplicado_a


def test_global_portada_106_9_sin_formula_configurada_falla_v2():
    consolidados = [97.6, 92.8, 67.5, 89.3, 90.5, 103.5]
    esperado = calcular_global(consolidados)
    hallazgos = validar_global(106.9, consolidados)
    assert len(hallazgos) == 1
    assert hallazgos[0].regla == "V2"
    assert hallazgos[0].valor_b == esperado


def test_global_correcto_no_genera_hallazgo():
    consolidados = [97.6, 92.8, 67.5, 89.3, 90.5, 103.5]
    esperado = calcular_global(consolidados)
    assert validar_global(esperado, consolidados) == []


def test_v1_consolidado_incorrecto_genera_hallazgo():
    proyectos = [ProyectoInput("A", "calidad", "Cerrado", 100.0)]
    indicadores = [IndicadorInput("I1", "calidad", 1, 1, cumplimiento_pct=100.0)]
    resultado = calcular_consolidado_linea(
        "calidad", retos_cumplimiento=97.8, proyectos=proyectos, indicadores=indicadores
    )
    # Simula que alguien sobreescribió el consolidado con el valor viejo (solo retos)
    resultado.consolidado = 97.8
    hallazgos = validar_consolidados_linea([resultado])
    assert len(hallazgos) == 1
    assert hallazgos[0].regla == "V1"


def test_v11_v12_proyectos_crudo():
    raw = [
        {"nombre": "P1", "linea": "calidad", "estado": "Cerrado", "avance_pct": 112.0},
        {"nombre": "P2", "linea": "calidad", "estado": "Cerrado", "avance_pct": 80.0},
        {"nombre": "P3", "linea": "calidad", "estado": "En ejecución", "avance_pct": 100.0},
    ]
    hallazgos = validar_proyectos_crudo(raw)
    reglas = {h.regla for h in hallazgos}
    assert "V11" in reglas  # P1 > 100
    assert "V12" in reglas  # P2 cerrado con 80% Y P3 100% no cerrado


def test_clasificar_semaforo():
    assert clasificar_semaforo(105) == "Cumplido"
    assert clasificar_semaforo(95) == "En progreso"
    assert clasificar_semaforo(50) == "Atención"
    assert clasificar_semaforo(None) == "Sin medición"
