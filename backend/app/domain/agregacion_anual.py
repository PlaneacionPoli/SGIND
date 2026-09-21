"""Cómo se pasa de periodos semestrales (2024-1, 2024-2) al valor ANUAL de una
métrica del Plan de Mejoramiento.

Por defecto se toma el último semestre del año (correcto para "stocks": profesores,
matrícula, infraestructura, tasas, promedios de evaluación...). Los indicadores de
participación / actividad — personas atendidas, leads, visitas, usos — se REPORTAN
por semestre y el dato del año es la SUMA de los dos; tomar solo el segundo
semestre subestimaba el total (validación de negocio 2026-09-21).

La decisión depende del significado del indicador, no de los datos, así que se
declara por Id de la hoja Metricas (T = tabla, G = gráfico, I = ilustración).
"""

from __future__ import annotations

# Confirmados por negocio.
_CONFIRMADOS = {
    "T32",  # Personal administrativo beneficiado con políticas de estímulos
    "T33",  # Participación de administrativos en formación
    "T36",  # Leads obtenidos año a año por canal
    "T43",  # Uso de los recursos bibliográficos
    "T44",  # Divulgación periódica revistas
}

# Mismo criterio (participación / atención / visitas), detectados por nombre.
_POR_CRITERIO = {
    "T49",  # Visitas MI-Books por país
    "T100",  # Participación de profesores en formación del Modelo Institucional
    "T101",  # Participación de profesores en el plan de cualificación institucional
    "T164",  # Atención Centro de Psicología
    "T165",  # Participación de la comunidad en actividades artísticas y culturales
    "T166",  # Participación de la comunidad en actividades deportivas
    "T167",  # Participación de la comunidad en Moocs
    "T169",  # Participación de la comunidad en programas de prevención de riesgo
    "T170",  # Atención a la comunidad en Enfermería
    "T171",  # Participación en actividades de promoción y cuidado de la salud
}

IDS_SUMA_SEMESTRAL: frozenset[str] = frozenset(_CONFIRMADOS | _POR_CRITERIO)

# Estados financieros con grupos que NO se suman entre sí (Tabla 66: Activos =
# Pasivos + Patrimonio): la fila principal muestra cada grupo, no un total global.
IDS_SIN_TOTAL_GLOBAL: frozenset[str] = frozenset({"T66"})

# Ítems de naturaleza distinta (número de aulas, área en m², PCs, Gb...): aunque todos
# sean ENT, sumarlos no tiene sentido y el total se muestra como "No aplica".
IDS_TOTAL_NO_APLICA: frozenset[str] = frozenset(
    {
        "T55",  # Infraestructura física del Poli
        "T57",  # Infraestructura física
        "T58",  # Infraestructura tecnológica
        "G6",  # Liquidez y capital de trabajo (pesos vs índice)
        "G8",  # Ingresos por extensión vs costos y gestión
    }
)

# Grupos cuyos porcentajes suman 100 dentro de cada grupo (Ilustración 20: cada medio
# de comunicación con sus opciones de respuesta): se muestran los grupos, pero la
# fila principal no suma un grupo con otro y dice "No aplica".
IDS_GRUPOS_SIN_TOTAL: frozenset[str] = frozenset({"I20"})
