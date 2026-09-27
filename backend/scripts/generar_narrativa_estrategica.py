"""Genera y guarda la narrativa cualitativa del Informe Estratégico PDI
(Cierre 2022-2025) — corre UNA VEZ (la info es estática) y deja el
resultado en data/derived/narrativa_estrategica_2022_2025.json, que el PDF
y el dashboard consolidado leen sin volver a generarla.

El texto de cada párrafo (TEXTOS_LINEAS / TEXTOS_CONSOLIDADO abajo) es de
autoría directa — redactado a partir de los datos reales del Centro de
Proyectos (Entregables/Impactos Generados por proyecto) y del CMI
(cumplimiento por indicador), NO generado por una plantilla ni por un LLM:
el primer intento (heurístico/Gemini) producía texto operativo (listas de
entregables) impropio para Alta Dirección — feedback explícito 2026-09-27.

Volver a correr este script sobrescribe el JSON — hacerlo cuando cambien
los datos fuente (cierres, Centro de Proyectos) y haya que reescribir el
texto con los nuevos hechos.

Uso (desde backend/, con la venv activa):
    SGIND_DATA_PATH=../data python scripts/generar_narrativa_estrategica.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings  # noqa: E402
from app.services.excel_reader import ExcelReaderService  # noqa: E402
from app.services.narrativa_estrategica_service import ensamblar_narrativa, guardar  # noqa: E402
from app.services.resumen_service import ResumenService  # noqa: E402

TEXTOS_CONSOLIDADO = {
    "resumen_ejecutivo": (
        "El Politécnico Grancolombiano cierra el corte 2022-2025 del PDI 2022-2026 con un "
        "cumplimiento institucional acumulado del 106,9%, resultado que combina un desempeño "
        "uniformemente sólido en cinco de las seis líneas estratégicas (97,5%-98,9%) con una "
        "ejecución más rezagada en Educación para toda la vida (94,7%). Más allá del indicador "
        "agregado, el ciclo deja evidencia de transformación estructural: acreditación "
        "institucional en trámite avanzado ante el CNA, una arquitectura tecnológica y de datos "
        "consolidada (Banner, Data Lake, HubSpot, POLISIGS certificado ISO 9001:2015) y mejoras "
        "medibles en cultura organizacional (Great Place to Work al 172% de la meta) y "
        "experiencia estudiantil (NPS +25,4 puntos). El principal desbalance del ciclo es la "
        "incursión en Educación Media y ETDH, comprometida en el plan original y aún sin activar."
    ),
    "logros": (
        "Los logros transformacionales del ciclo se concentran en tres frentes: la consolidación "
        "de la arquitectura tecnológica y de datos institucional como habilitador transversal de "
        "la estrategia, el avance sustancial del proceso de acreditación institucional en alta "
        "calidad de la Sede Bogotá, y una mejora cultural medible en el talento humano y la "
        "experiencia de la comunidad POLI, evidenciada en indicadores de clima organizacional y "
        "de satisfacción estudiantil que superaron ampliamente sus metas."
    ),
    "retos_priorizados": (
        "Los retos priorizados para el PDI 2026-2030 son: decidir explícitamente el futuro de la "
        "incursión en Educación Media y ETDH, hoy detenida desde su formulación; cerrar la "
        "depuración del histórico SNIES, que compromete la calidad del dato regulatorio "
        "institucional; y fortalecer el componente de proyección social y voluntariado en "
        "Sostenibilidad, la dimensión con menor tracción relativa dentro de una línea por lo "
        "demás sólida. En conjunto, esta es la agenda de continuidad estratégica que el cierre "
        "2022-2025 deja formulada para el siguiente ciclo de planeación."
    ),
}

TEXTOS_LINEAS = {
    "calidad": {
        "logros": (
            "La línea Calidad alcanza un cumplimiento acumulado del 97,8% y consolida su "
            "objetivo estratégico central —asegurar la acreditación institucional en alta "
            "calidad de la Sede Bogotá— con la ejecución completa del proceso ante el CNA: "
            "informe de autoevaluación radicado, visita de pares académicos realizada en "
            "octubre de 2025 con concepto altamente positivo, y Plan de Mejoramiento "
            "Institucional aprobado por el Consejo Directivo. Este hito se apalanca en "
            "transformaciones estructurales de fondo: la relación estudiante-docente de tiempo "
            "completo equivalente mejoró un 33,6% (de 103 a 68,4), el 100% de los programas "
            "académicos ya cuenta con resultados de aprendizaje implementados, y el ecosistema "
            "de recursos educativos digitales (CREA, catálogo virtual) elevó de forma sostenida "
            "la calidad de la experiencia formativa. El resultado consolida una maduración real "
            "de los procesos académicos institucionales, no solo el cumplimiento de un hito de "
            "acreditación puntual."
        ),
        "pendientes": (
            "El principal pendiente de la línea es el Sistema de Medición de Resultados de "
            "Aprendizaje, aún en fase de planeación, cuya puesta en marcha es condición para "
            "sostener la mejora continua curricular lograda en el ciclo. Persisten además dos "
            "indicadores en zona de alerta —productos de investigación, innovación y creación "
            "(94,2%) y relación estudiante-docente de tiempo completo (97,8%)— que, aunque "
            "cercanos a meta, evidencian una tensión estructural entre el crecimiento de la "
            "oferta académica y la capacidad de la planta docente e investigativa para "
            "sostenerlo. Para el PDI 2026-2030 esto se traduce en dos prioridades: cerrar el "
            "sistema de medición de aprendizajes como habilitador de la siguiente etapa de "
            "calidad, y definir una estrategia diferenciada de fortalecimiento de investigación "
            "y planta docente que no dependa exclusivamente del crecimiento vegetativo "
            "alcanzado en este ciclo."
        ),
    },
    "expansion": {
        "logros": (
            "La línea Expansión cierra el ciclo con un cumplimiento del 98,9%, consolidando el "
            "objetivo de crecer con compromiso social mediante un crecimiento sostenido de la "
            "población estudiantil —con sobrecumplimiento en indicadores de posicionamiento de "
            "marca (brand equity al 125,8% y conocimiento espontáneo al 122,2% de la meta)— y "
            "el diseño de nuevas fuentes de crecimiento hacia adelante: una estrategia de "
            "pricing institucional basada en el análisis de elasticidad de demanda por "
            "programa, y la estructuración de Proyecto Silver, una línea de negocio dirigida a "
            "población mayor de 50 años que amplía el mercado más allá del segmento "
            "tradicional. El resultado refleja una expansión que ya no depende solo del "
            "crecimiento vegetativo de matrícula, sino de mecanismos deliberados de "
            "diferenciación comercial y diversificación de mercado."
        ),
        "pendientes": (
            "Expansión cierra el ciclo sin proyectos pendientes ni indicadores en zona crítica "
            "identificados, lo que la posiciona como la línea de mayor estabilidad del "
            "portafolio. La prioridad para el PDI 2026-2030 no es de contención sino de "
            "escalamiento: llevar a implementación plena las hipótesis validadas por Pricing y "
            "Proyecto Silver —hoy en fase de diseño estratégico— y evaluar nuevos segmentos de "
            "crecimiento (relacionamiento empresa-Estado, internacionalización) que sostengan "
            "el ritmo alcanzado una vez se agote el margen de crecimiento del modelo actual."
        ),
    },
    "transformacion organizacional": {
        "logros": (
            "Transformación Organizacional es la línea con mayor densidad de cierres del ciclo "
            "(18 proyectos) y consolida su doble objetivo de arquitectura tecnológica y cultura "
            "organizacional con un cumplimiento del 97,5%. En el frente tecnológico, la "
            "migración del ecosistema Banner, la centralización de datos en Data Lake, la "
            "integración Banner-HubSpot-FDI y la certificación ISO 9001:2015 del POLISIGS "
            "trasladan a la Institución de una operación fragmentada a una arquitectura de "
            "datos y procesos gobernada. En el frente humano, el Plan Talento elevó el índice "
            "Great Place to Work de 76 a 89 puntos (172% de la meta) y el eNPS trece puntos, "
            "evidencia de un cambio cultural medible, no solo declarado. La combinación de "
            "ambos frentes —tecnología y cultura— es la transformación de fondo que el PDI "
            "2022-2026 se propuso para esta línea."
        ),
        "pendientes": (
            "Quedan tres iniciativas en fase de planeación —automatización del proceso "
            "contractual, homologaciones con IA en Ilumno y la reforma curricular tecnológica— "
            "que no alcanzaron a iniciar ejecución en el ciclo, y un riesgo de datos concreto: "
            "la depuración del histórico SNIES está en zona de peligro (56,8% de la meta), lo "
            "que compromete la calidad de la información regulatoria institucional. Para el PDI "
            "2026-2030 esto exige priorizar la depuración de SNIES como prerrequisito de "
            "cualquier estrategia de analítica avanzada, y decidir explícitamente si las tres "
            "iniciativas en planeación se ejecutan, se rediseñan o se descontinúan antes de "
            "comprometer presupuesto del siguiente ciclo."
        ),
    },
    "experiencia": {
        "logros": (
            "Experiencia consolida su objetivo de garantizar valor agregado a la comunidad POLI "
            "con un cumplimiento del 98,1%, apalancado en la implementación del Hub de "
            "Experiencia y Agilismo (HEYA), que elevó el NPS de estudiantes 25,4 puntos (de "
            "32,2 a 58,6) y el Índice de Satisfacción del Estudiante al 90%. El Centro "
            "Gastronómico redujo en 80% el costo anual de prácticas del programa de Hotelería y "
            "Gastronomía al eliminar la dependencia de terceros, y el modelo KITUS de "
            "acompañamiento segmentado elevó la permanencia intersemestral a 86,2%, con "
            "resultados diferenciados en los grupos piloto de mayor riesgo de deserción. El "
            "patrón común es la migración de una gestión reactiva de la experiencia a una "
            "arquitectura de journey maps, analítica predictiva y agilismo institucionalizados."
        ),
        "pendientes": (
            "Tres iniciativas de analítica avanzada para retención —modelo predictivo de "
            "deserción basado en scoring, IA de voz e IA de WhatsApp para recuperación de "
            "estudiantes— permanecen en fase de planeación sin indicadores en zona crítica que "
            "las urjan, lo que sugiere una oportunidad de escalamiento más que una alerta. La "
            "prioridad para el PDI 2026-2030 es llevar estas tres iniciativas de datos a "
            "producción para extender el modelo KITUS, que ya demostró resultados medibles en "
            "grupos piloto, hacia una cobertura institucional completa del acompañamiento "
            "estudiantil."
        ),
    },
    "sostenibilidad": {
        "logros": (
            "Sostenibilidad cierra el ciclo con un cumplimiento del 97,9%, ampliando su alcance "
            "ambiental y social más allá del cumplimiento normativo: la certificación ISO "
            "14001:2015 se extendió a la sede Los Colores en Medellín con reducciones "
            "verificadas de 18,9% en consumo eléctrico y 26% en consumo de agua per cápita, el "
            "Ecosistema E3 dio a los graduados una plataforma formal de empleabilidad y "
            "emprendimiento, y la política institucional de equidad de género quedó aprobada "
            "con líneas base definidas por vicerrectoría. Estos tres frentes —ambiental, de "
            "empleabilidad y de género— consolidan una noción de sostenibilidad integral, no "
            "limitada a la dimensión financiera, coherente con el objetivo estratégico de la "
            "línea."
        ),
        "pendientes": (
            "No hay proyectos pendientes de inicio en esta línea, pero cuatro indicadores "
            "requieren seguimiento gerencial: la ejecución de Opex (110,6%) y CAPEX (107,1%) "
            "supera lo presupuestado, lo que amerita revisar la disciplina de gasto frente a la "
            "planeación financiera, y el impacto de actividades de responsabilidad social "
            "(84,4%) y la participación en voluntariados (86,8%) quedan por debajo de meta, "
            "señal de que el componente de proyección social avanza más lento que el ambiental "
            "y el financiero. Para el PDI 2026-2030 la prioridad es doble: fortalecer el "
            "control de ejecución presupuestal y activar una estrategia específica de "
            "movilización de la comunidad hacia la proyección social, hoy el eslabón más débil "
            "de la línea."
        ),
    },
    "educacion para toda la vida": {
        "logros": (
            "Educación para toda la vida cierra el ciclo con el cumplimiento más bajo del "
            "portafolio (94,7%), aunque con un resultado destacado en su frente de educación "
            "continua: los ingresos B2B crecieron muy por encima de la meta (130% de "
            "cumplimiento), evidencia de que el relacionamiento con el sector empresarial —eje "
            "central del objetivo de impulsar la educación continua— sí logró tracción "
            "comercial real en el ciclo. Sin embargo, el segundo objetivo de la línea, "
            "incursionar en Educación Media y en Educación para el Trabajo y el Desarrollo "
            "Humano, no avanzó: los tres proyectos que le dan forma —Instituto ETDH, Colegio "
            "Virtual y Centro de Idiomas— permanecen en pausa (stand by) desde su formulación, "
            "sin ejecución registrada en el ciclo."
        ),
        "pendientes": (
            "El pendiente estructural de la línea es la incursión en Educación Media y ETDH, "
            "comprometida en el PDI 2022-2026 con metas explícitas (10 programas ETDH con 750 "
            "estudiantes cada uno y un colegio virtual de 100 estudiantes al 2026) que no se "
            "activaron en el ciclo. Esta pausa, sostenida en el tiempo y no puntual, es la "
            "principal decisión estratégica pendiente para el PDI 2026-2030: definir si estos "
            "proyectos se relanzan con un caso de negocio actualizado, se redefinen en alcance, "
            "o se descontinúan formalmente en favor de profundizar el frente de educación "
            "continua B2B/B2G, que sí demostró tracción. Los ingresos B2G (97,4%) y otros "
            "ingresos por cursos y opciones de grado (96%) también quedan levemente por debajo "
            "de meta y deben monitorearse junto con esta decisión."
        ),
    },
}


def main() -> None:
    settings = get_settings()
    excel = ExcelReaderService(settings)
    svc = ResumenService(excel)
    data = ensamblar_narrativa(svc, TEXTOS_LINEAS, TEXTOS_CONSOLIDADO)
    path = guardar(data)
    print(f"Narrativa estratégica guardada en: {path}")


if __name__ == "__main__":
    main()
