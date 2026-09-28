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
        "El Politécnico Grancolombiano cierra el ciclo del PDI 2022-2026 con su logro más "
        "significativo del periodo: la acreditación institucional en alta calidad por 6 años, "
        "otorgada por el CNA en mayo de 2026, que reconoce una formación que va más allá de lo "
        "académico e incluye acompañamiento, innovación y oportunidades reales para su comunidad. "
        "Ese reconocimiento externo confirma una transformación que ya se sentía puertas "
        "adentro, con una experiencia estudiantil que mejoró de forma sostenida (NPS +25,4 "
        "puntos) y una cultura organizacional que avanzó por encima de lo esperado, certificada "
        "por Great Place to Work. Esa transformación se apalancó en una arquitectura tecnológica "
        "y de datos consolidada "
        "(Banner, Data Lake, HubSpot, POLISIGS certificado ISO 9001:2015), que hoy permite "
        "decisiones más ágiles y basadas en evidencia en toda la institución. La ejecución "
        "estratégica respalda estos logros: las seis líneas del PDI cerraron el ciclo con un "
        "desempeño sólido y equilibrado entre sí. Sostenibilidad se destacó con una ejecución de "
        "proyectos ejemplar y una gestión financiera responsable. El principal pendiente del "
        "ciclo está en Educación para toda la vida: sus proyectos de incursión en Educación Media "
        "y ETDH ya ejecutaron su Fase I, pero están a la espera de las definiciones necesarias "
        "para continuar. Resolver esas definiciones es la tarea prioritaria para completar la "
        "apuesta de acceso y cobertura del PDI en el próximo ciclo."
    ),
    "logros": (
        "Los logros transformacionales del ciclo, ordenados según las líneas estratégicas, "
        "parten de Calidad, con la acreditación institucional en alta calidad que el CNA otorgó "
        "a la Sede Bogotá por seis años. En Expansión, la institución lanzó 26 nuevos programas "
        "entre presenciales y virtuales, y la población estudiantil aumentó 13,1% frente a 2022, "
        "al pasar de 50.241 a 56.807 estudiantes, por encima de la meta en los cuatro segmentos: "
        "presencial, virtual, pregrado y posgrado. En Experiencia, la comunidad POLI percibió "
        "una mejora medible en su relación con la institución, reflejo del trabajo hecho sobre "
        "el servicio y el acompañamiento a estudiantes. En Transformación Organizacional, se "
        "consolidó la arquitectura tecnológica y de datos institucional, se registró una mejora "
        "medible en la cultura del talento humano, y la gestión financiera se mantuvo sólida, "
        "con EBITDA y utilidad neta muy por encima de sus metas. Y en Sostenibilidad, la "
        "certificación ISO 14001:2015 se extendió a la sede de Medellín, el Ecosistema E3 abrió "
        "una ruta formal de empleabilidad y emprendimiento para los graduados, y la proporción "
        "de estudiantes becados superó lo proyectado."
    ),
    "retos_priorizados": (
        "Los retos priorizados para el PDI 2026-2030 se concentran en tres frentes: consolidar "
        "el Centro de Excelencia Analítica y la madurez analítica institucional —gobierno de TI, "
        "arquitectura de microservicios y modelos de inteligencia artificial— como palanca de "
        "decisiones basadas en datos para toda la institución; sostener el ritmo de expansión "
        "que definió este ciclo, llevando a escala los mecanismos de diferenciación comercial y "
        "diversificación de mercado validados en Pricing y Proyecto Silver; y definir el camino a "
        "seguir para los programas de Eduvida, cuya Fase I ya fue ejecutada y hoy está a la "
        "espera de las definiciones necesarias para continuar. En conjunto, esta es la agenda de "
        "continuidad estratégica que el cierre 2022-2025 deja formulada para el siguiente ciclo "
        "de planeación."
    ),
}

TEXTOS_LINEAS = {
    "calidad": {
        "logros": {
            "retos": (
                "El desempeño de los retos institucionales asociados a Calidad cierra en 97,8% "
                "de cumplimiento, con una ejecución sostenida y sin sobresaltos a lo largo del "
                "ciclo 2022-2025 — evidencia de que el despliegue operativo de la línea estuvo "
                "alineado con la meta desde el inicio, sin picos de recuperación de último "
                "momento."
            ),
            "proyectos": (
                "En proyectos, la línea alcanza un avance promedio de 88,5% sobre 15 "
                "iniciativas, con el hito central del ciclo ya materializado: la acreditación "
                "institucional en alta calidad de la Sede Bogotá fue otorgada por el CNA en "
                "mayo de 2026 por 6 años, tras el informe de autoevaluación radicado, la visita "
                "de pares académicos de octubre de 2025 con concepto altamente positivo, y el "
                "Plan de Mejoramiento Institucional aprobado por el Consejo Directivo. En "
                "paralelo cerraron proyectos de transformación curricular y de experiencia "
                "formativa —Innovación Curricular, Cultura de una Buena Docencia, CREA y el "
                "Catálogo de Recursos Virtuales—, que sostienen la calidad académica más allá "
                "del hito puntual de acreditación."
            ),
            "indicadores": (
                "El CMI de la línea promedia 106,4% de cumplimiento. La relación "
                "estudiante-docente de tiempo completo se ubica en 83 estudiantes por docente "
                "frente a una meta de 81 (97,8% de cumplimiento), una tensión leve pero real "
                "entre el crecimiento de matrícula y la capacidad de la planta docente. A esto "
                "se suma que el 100% de los programas académicos ya cuenta con resultados de "
                "aprendizaje implementados, la base técnica que sostiene la acreditación."
            ),
            "consolidado": (
                "En conjunto, Calidad consolida su objetivo estratégico central —asegurar la "
                "acreditación institucional en alta calidad— con un desempeño equilibrado en "
                "las tres dimensiones (retos 97,8%, proyectos 88,5%, indicadores 106,4%): la "
                "ejecución operativa fue estable, la acreditación fue efectivamente otorgada "
                "por el CNA, y los indicadores estructurales (planta docente, resultados de "
                "aprendizaje) confirman que el resultado es una maduración real de los procesos "
                "académicos institucionales, no solo el cumplimiento de un hito puntual."
            ),
        },
        "pendientes": (
            "El principal pendiente de la línea es el Sistema de Medición de Resultados de "
            "Aprendizaje, aún en fase de planeación, cuya puesta en marcha es condición para "
            "sostener la mejora continua curricular lograda en el ciclo. Persisten además dos "
            "indicadores en zona de alerta —productos de investigación, innovación y creación "
            "(94,2%) y relación estudiante-docente de tiempo completo (97,8%)— que, aunque "
            "cercanos a meta, evidencian una tensión estructural entre el crecimiento de la "
            "oferta académica y la capacidad de la planta docente e investigativa para "
            "sostenerlo. Para el PDI 2026-2030 esto se traduce en tres prioridades: cerrar el "
            "sistema de medición de aprendizajes como habilitador de la siguiente etapa de "
            "calidad, implementar la reforma curricular de los programas académicos que "
            "sostenga la acreditación recién obtenida, y definir una estrategia diferenciada de "
            "fortalecimiento de investigación y planta docente que no dependa exclusivamente "
            "del crecimiento vegetativo alcanzado en este ciclo."
        ),
    },
    "expansion": {
        "logros": {
            "retos": (
                "Los retos de Expansión cierran en 98,9% de cumplimiento, el más alto del "
                "portafolio en esta dimensión, reflejo de una ejecución consistente del "
                "crecimiento planeado de matrícula a lo largo de los cuatro años del ciclo."
            ),
            "proyectos": (
                "En proyectos, la línea registra un avance promedio de 89,0% sobre 3 "
                "iniciativas. Dos ya cerraron al 100%: Pricing, que construyó una estrategia de "
                "precios institucional basada en el análisis de elasticidad de demanda por "
                "programa y en la diferenciación de descuentos como política comercial; y "
                "Proyecto Silver, que estructuró una línea de negocio dirigida a población mayor "
                "de 50 años, ampliando el mercado más allá del segmento tradicional. La tercera, "
                "implementación de HubSpot Eduvida, sigue en ejecución (67%) y es la base "
                "tecnológica del crecimiento futuro en captación."
            ),
            "indicadores": (
                "El CMI promedia 107,5% de cumplimiento, con sobrecumplimiento marcado en los "
                "indicadores de posicionamiento de marca: brand equity llegó a 125,8% de la "
                "meta y el conocimiento espontáneo de la institución a 122,2%. Estos resultados "
                "acompañan el crecimiento de población estudiantil, que superó la meta en "
                "todos sus segmentos (presencial, virtual, pregrado y posgrado)."
            ),
            "consolidado": (
                "El resultado consolidado de Expansión (retos 98,9%, proyectos 89,0%, "
                "indicadores 107,5%) muestra una línea que ya no depende solo del crecimiento "
                "vegetativo de matrícula: los proyectos cerrados (Pricing, Proyecto Silver) "
                "instalan mecanismos deliberados de diferenciación comercial y diversificación "
                "de mercado, mientras los indicadores confirman que el posicionamiento de "
                "marca se fortaleció en paralelo al crecimiento. Es la línea con mejor "
                "desempeño equilibrado entre las tres dimensiones del ciclo."
            ),
        },
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
        "logros": {
            "retos": (
                "Los retos de Transformación Organizacional cierran en 97,5% de cumplimiento, "
                "estable durante todo el ciclo, pese a ser la línea con la agenda de ejecución "
                "más densa del portafolio."
            ),
            "proyectos": (
                "Con 16 proyectos activos en el rango 2021-2025, es la línea con mayor densidad "
                "de iniciativas del ciclo, y su avance promedio (81,4%) refleja tanto la "
                "magnitud del esfuerzo como el hecho de que 11 de ellos ya cerraron. En el "
                "frente tecnológico: la migración "
                "del ecosistema académico Banner a su versión más reciente sobre Oracle Cloud, "
                "la centralización de datos institucionales en un Data Lake bajo metodología "
                "Data Vault, la integración Banner-HubSpot-FDI para la gestión de aspirantes y "
                "estudiantes, y la certificación ISO 9001:2015 del nuevo POLISIGS (con "
                "ampliación de alcance auditada por ICONTEC). En el frente humano, el Plan "
                "Talento y el nuevo Portal Web Universitario completan el cierre."
            ),
            "indicadores": (
                "El CMI promedia 101,6% de cumplimiento. El indicador más visible del cambio "
                "cultural es el Great Place to Work, con una ejecución de 81,0 puntos frente a "
                "una meta de 68,7 (117,9% de cumplimiento) — evidencia de que la transformación "
                "cultural fue medible, no solo declarada."
            ),
            "consolidado": (
                "El balance consolidado (retos 97,5%, proyectos 81,4% sobre 16 iniciativas, "
                "indicadores 101,6%) confirma que la transformación organizacional del ciclo "
                "operó en dos frentes simultáneos y complementarios: una arquitectura "
                "tecnológica y de datos que pasó de fragmentada a gobernada, y una cultura "
                "organizacional con mejoras medibles en clima laboral. Es la combinación de "
                "ambos frentes la que constituye la transformación de fondo que el PDI "
                "2022-2026 se propuso para esta línea."
            ),
        },
        "pendientes": (
            "Quedan tres iniciativas en fase de planeación —automatización del proceso "
            "contractual, homologaciones con IA en Ilumno y la reforma curricular tecnológica— "
            "que no alcanzaron a iniciar ejecución en el ciclo. La depuración del histórico "
            "SNIES, en cambio, ya se cerró en el ciclo, un habilitador de calidad de dato clave "
            "para cualquier estrategia de analítica avanzada del siguiente PDI. Para el PDI "
            "2026-2030 el foco de esta línea es doble: consolidar el Centro de Excelencia "
            "Analítica sobre esa base de datos ya depurada, y decidir explícitamente si las tres "
            "iniciativas en planeación se ejecutan, se rediseñan o se descontinúan antes de "
            "comprometer presupuesto del siguiente ciclo."
        ),
    },
    "experiencia": {
        "logros": {
            "retos": (
                "Los retos de Experiencia cierran en 98,1% de cumplimiento, con una ejecución "
                "sostenida a lo largo del ciclo."
            ),
            "proyectos": (
                "El avance promedio en proyectos es de 94,7% sobre 7 iniciativas, 6 de ellas ya "
                "cerradas al 100%. El hito central es la implementación en tres fases del Hub de "
                "Experiencia y Agilismo (HEYA), que rediseñó la gestión de la experiencia "
                "institucional a partir de journey maps y metodologías ágiles. En paralelo, el "
                "Centro Gastronómico redujo en 80% el costo anual de prácticas del programa de "
                "Hotelería y Gastronomía al eliminar la dependencia de terceros, y el Proyecto de "
                "Permanencia Institucional desplegó el modelo KITUS de acompañamiento "
                "segmentado con resultados diferenciados en los grupos de mayor riesgo de "
                "deserción. La única iniciativa aún en ejecución es la remodelación de los "
                "bloques I y C (63%)."
            ),
            "indicadores": (
                "El CMI promedia 103,4% de cumplimiento. El NPS de estudiantes subió 25,4 "
                "puntos en el ciclo (de 32,2 a 58,6), el Índice de Satisfacción del Estudiante "
                "llegó a 90%, y la permanencia intersemestral alcanzó 86,2% — los tres por "
                "encima de sus metas respectivas."
            ),
            "consolidado": (
                "El resultado consolidado (retos 98,1%, proyectos 94,7%, indicadores 103,4%) "
                "muestra una línea que migró de una gestión reactiva de la experiencia a una "
                "arquitectura de journey maps y agilismo institucionalizados, con resultados ya "
                "visibles en satisfacción y permanencia estudiantil, y con la mayoría de sus "
                "proyectos estructurales ya cerrados."
            ),
        },
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
        "logros": {
            "retos": (
                "Los retos de Sostenibilidad cierran en 97,9% de cumplimiento, con ejecución "
                "estable en el ciclo."
            ),
            "proyectos": (
                "Es la línea con mejor ejecución de proyectos del portafolio: 100% de avance "
                "promedio, con los 3 proyectos de la línea cerrados por completo. La "
                "certificación ISO 14001:2015 se amplió a la sede Los Colores en Medellín, con "
                "reducciones verificadas de 18,9% en consumo eléctrico y 26% en consumo de "
                "agua per cápita; el Ecosistema E3 dio a los graduados una plataforma formal "
                "de empleabilidad y emprendimiento; y la política institucional de equidad de "
                "género quedó aprobada con líneas base definidas por vicerrectoría."
            ),
            "indicadores": (
                "El CMI promedia 112,6% de cumplimiento, el más alto del portafolio, "
                "apalancado en la ejecución financiera: EBITDA, Utilidad Neta y Cumplimiento de "
                "Ingresos sobrecumplieron meta (117,5%, 130% y 111,3% respectivamente). El "
                "componente social, en cambio, avanza más lento: el impacto de actividades de "
                "responsabilidad social llegó a 84,4% y la participación en voluntariados a "
                "86,8%."
            ),
            "consolidado": (
                "El balance consolidado (retos 97,9%, proyectos 100%, indicadores 112,6%) "
                "confirma que Sostenibilidad es, junto con Expansión, la línea de mejor "
                "desempeño integral del ciclo, con una ejecución de proyectos ejemplar y una "
                "gestión financiera sólida — con la salvedad de que el componente de "
                "proyección social y voluntariado avanza a un ritmo menor que el ambiental y "
                "el financiero, y debe fortalecerse en el siguiente ciclo."
            ),
        },
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
        "logros": {
            "retos": (
                "Los retos de Educación para toda la vida cierran en 94,7% de cumplimiento, el "
                "más bajo del portafolio."
            ),
            "proyectos": (
                "La perspectiva de proyectos es N/A para esta línea: los 3 proyectos "
                "—Instituto de Educación para el Trabajo y el Desarrollo Humano (IETDH), "
                "Colegio Virtual y Centro de Idiomas POLI— ya ejecutaron su Fase I, pero hoy "
                "están en pausa (stand by) a la espera de las definiciones necesarias para "
                "continuar a la siguiente fase, y por eso no se promedian (metodología del "
                "informe: un proyecto en stand by no resta ni suma)."
            ),
            "indicadores": (
                "El CMI, en cambio, promedia 107,8% de cumplimiento, apalancado casi "
                "exclusivamente en el frente de educación continua: los ingresos B2B "
                "crecieron muy por encima de la meta (130% de cumplimiento), evidencia de que "
                "el relacionamiento con el sector empresarial sí logró tracción comercial real "
                "en el ciclo, aun cuando el segundo objetivo de la línea no avanzó."
            ),
            "consolidado": (
                "El balance consolidado (retos 94,7%, indicadores 107,8%; proyectos N/A) "
                "promedia 101,2%, pero esa cifra descansa en solo dos de las tres dimensiones y "
                "no debe leerse como una línea sólida: revela dos velocidades marcadamente "
                "distintas. El frente de educación continua (B2B/B2G) funciona y genera "
                "resultados comerciales reales, mientras la incursión en Educación Media y "
                "ETDH —comprometida en el PDI 2022-2026 con metas explícitas— ejecutó su Fase I "
                "pero sus 3 proyectos están en stand by a la espera de definiciones para "
                "continuar. Es la línea que más requiere una decisión estratégica explícita "
                "antes de iniciar el PDI 2026-2030."
            ),
        },
        "pendientes": (
            "El pendiente estructural de la línea es la incursión en Educación Media y ETDH, "
            "comprometida en el PDI 2022-2026 con metas explícitas (10 programas ETDH con 750 "
            "estudiantes cada uno y un colegio virtual de 100 estudiantes al 2026). La Fase I ya "
            "se ejecutó, pero los tres proyectos están en stand by a la espera de las "
            "definiciones necesarias para continuar. Resolver esas definiciones es la principal "
            "decisión estratégica pendiente para el PDI 2026-2030: si se avanza a la siguiente "
            "fase con el caso de negocio ya validado, se redefine su alcance, o se descontinúa "
            "formalmente en favor de profundizar el frente de educación continua B2B/B2G, que sí "
            "demostró tracción. Los ingresos B2G (97,4%) y otros ingresos por cursos y opciones "
            "de grado (96%) también quedan levemente por debajo de meta y deben monitorearse "
            "junto con esta decisión."
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
