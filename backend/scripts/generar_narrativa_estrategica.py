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

TARJETAS_CONSOLIDADO = {
    "balance": {
        "logros_destacados": [
            {"label": "Acreditación CNA", "valor": "Otorgada 6 Años"},
            {"label": "Expansión Matrícula", "valor": "+13,1% vs. 2022"},
            {"label": "Sostenibilidad ISO", "valor": "Norma 14001:2015"},
        ],
        "auditoria": "Auditoría Interna OK",
    },
    "cifras": [
        {
            "titulo": "Estudiantes POLI",
            "valor": "56.807",
            "detalle": "+13,1% vs. 2022",
        },
        {
            "titulo": "Satisfacción NPS",
            "valor": "+25,4 pts",
            "detalle": "Mejora sostenida",
        },
        {
            "titulo": "Nuevos Programas",
            "valor": "26",
            "detalle": "Presenciales y virtuales",
        },
        {
            "titulo": "Clima Laboral",
            "valor": "GPTW",
            "detalle": "Certificado",
        },
    ],
    "retos_priorizados": [
        {
            "codigo": "P1",
            "titulo": "Centro de Excelencia Analítica",
            "detalle": (
                "Gobierno de TI, arquitectura de microservicios y modelos de IA "
                "como palanca de decisiones basadas en datos"
            ),
        },
        {
            "codigo": "P2",
            "titulo": "Sostener el ritmo de expansión",
            "detalle": (
                "Escalar los mecanismos de diferenciación comercial y "
                "diversificación de mercado validados en Pricing y Proyecto Silver"
            ),
        },
        {
            "codigo": "P3",
            "titulo": "Definir el camino de Eduvida",
            "detalle": "Fase I ya ejecutada; a la espera de las definiciones necesarias para continuar",
        },
    ],
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
            "La prioridad inmediata de la línea es poner en marcha el Sistema de Medición de "
            "Resultados de Aprendizaje, hoy en fase de planeación y pieza clave para sostener la "
            "mejora continua curricular lograda en este ciclo. Dos indicadores requieren "
            "seguimiento cercano: productos de investigación, innovación y creación (94,2%) y "
            "relación estudiante-docente de tiempo completo (97,8%). Aunque ambos están cerca de "
            "la meta, señalan la tensión entre el crecimiento de la oferta académica y la "
            "capacidad de la planta docente e investigativa para sostenerlo. Para el PDI "
            "2026-2030 la línea se enfoca en tres frentes: implementar el Sistema de Medición de "
            "Resultados de Aprendizaje como habilitador de la siguiente etapa de calidad, "
            "ejecutar la reforma curricular de los programas académicos que sostenga la "
            "acreditación recién obtenida, y diseñar una estrategia propia de fortalecimiento de "
            "investigación y planta docente, que crezca al mismo ritmo que la oferta académica."
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
            "Expansión cierra el ciclo sin proyectos por cerrar ni indicadores en zona crítica, "
            "lo que la posiciona como la línea de mayor estabilidad del portafolio. La "
            "prioridad para el PDI 2026-2030 no es de contención sino de escalamiento: llevar a "
            "implementación plena las hipótesis validadas por Pricing y Proyecto Silver, hoy en "
            "fase de diseño estratégico, y evaluar nuevos segmentos de crecimiento, como el "
            "relacionamiento empresa-Estado y la internacionalización, que sostengan el ritmo "
            "alcanzado una vez se agote el margen de crecimiento del modelo actual."
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
                "El CMI promedia 101,6% de cumplimiento, con logros en los tres objetivos de la "
                "línea. En el frente humano, el indicador más visible del cambio cultural es el "
                "Great Place to Work, con una ejecución de 81,0 puntos frente a una meta de 68,7 "
                "(117,9% de cumplimiento), acompañado de una satisfacción con los servicios "
                "prestados de 85% y una reducción del índice de rotación a 0,89 frente a una "
                "meta de 1,2 — evidencia de que la transformación cultural fue medible, no solo "
                "declarada. En arquitectura tecnológica, la disponibilidad de servicios "
                "tecnológicos llegó a 97,7%, por encima de la meta. Y en gestión por procesos y "
                "datos, la cobertura de recolección de variables para analítica (ADA) alcanzó "
                "100% de la información solicitada por el SNIES, la base sobre la que se "
                "construirá el Centro de Excelencia Analítica del próximo ciclo."
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
            "Tres iniciativas —automatización del proceso contractual, homologaciones con IA "
            "en Ilumno y la reforma curricular tecnológica— ya iniciaron ejecución en el ciclo "
            "y continúan en desarrollo. Para el PDI 2026-2030 el foco de esta línea es doble: "
            "implementar el proyecto de Gobierno de Datos, hoy apenas en 5% de avance, como "
            "base de calidad de dato para el Centro de Excelencia Analítica, y llevar a cierre "
            "las tres iniciativas en desarrollo antes de comprometer presupuesto del siguiente "
            "ciclo."
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
                "El CMI promedia 103,4% de cumplimiento, con las cuatro dimensiones de la "
                "experiencia estudiantil por encima de su meta. El NPS subió 25,4 puntos en el "
                "ciclo (de 32,2 a 58,6) y el Índice de Satisfacción del Estudiante llegó a 90%, "
                "evidencia de un vínculo cada vez más sólido con la comunidad estudiantil. Ese "
                "vínculo se sostiene en la operación: el Acuerdo de Nivel de Servicio se cumplió "
                "en 95% y la permanencia intersemestral alcanzó el 86% proyectado, señal de que "
                "la mejora en percepción vino acompañada de una gestión operativa consistente."
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
            "Tres iniciativas de analítica avanzada para retención (modelo predictivo de "
            "deserción basado en scoring, IA de voz e IA de WhatsApp para recuperación de "
            "estudiantes) están en fase de planeación, sin que ningún indicador en zona crítica "
            "obligue a acelerarlas. Esto abre una oportunidad de escalamiento más que una "
            "alerta. La prioridad para el PDI 2026-2030 es llevar estas tres iniciativas de "
            "datos a producción, para extender el modelo KITUS, que ya demostró resultados "
            "medibles en grupos piloto, hacia una cobertura institucional completa del "
            "acompañamiento estudiantil."
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
                "En proyectos, la línea completó la Fase I de sus tres iniciativas: el "
                "Instituto de Educación para el Trabajo y el Desarrollo Humano (IETDH), el "
                "Colegio Virtual y el Centro de Idiomas POLI. Los dos primeros avanzan de la "
                "mano de CAFAM como aliado estratégico, con la etapa legal ya resuelta: los "
                "análisis de viabilidad quedaron listos en ambos casos, y en IETDH también se "
                "cerró el análisis del contexto regulatorio. El siguiente paso es definir el "
                "modelo pedagógico y regulatorio del Colegio Virtual, y el portafolio de "
                "programas y el modelo de operación de IETDH, dejando a los tres proyectos "
                "listos para escalar a su siguiente fase en el próximo ciclo del PDI."
            ),
            "indicadores": (
                "El CMI promedia 107,8% de cumplimiento, resultado impulsado principalmente por "
                "el frente de educación continua: los ingresos B2B crecieron muy por encima de "
                "la meta, con un cumplimiento de 130%, lo que confirma que el relacionamiento "
                "con el sector empresarial logró tracción comercial real en el ciclo. El segundo "
                "objetivo de la línea aún no arrancó y será foco de atención en el próximo "
                "ciclo."
            ),
            "consolidado": (
                "El balance consolidado (retos 94,7%, indicadores 107,8%; proyectos N/A) "
                "promedia 101,2%, revela dos velocidades marcadamente distintas. El frente de "
                "educación continua (B2B/B2G) funciona y genera resultados comerciales reales, "
                "mientras la incursión en Educación Media y ETDH —comprometida en el PDI "
                "2022-2026 con metas explícitas— ejecutó su Fase I pero sus 3 proyectos están "
                "en stand by a la espera de definiciones para continuar. Es la línea que más "
                "requiere una decisión estratégica explícita antes de iniciar el PDI 2026-2030."
            ),
        },
        "pendientes": (
            "El principal foco estratégico de la línea es la incursión en Educación Media y "
            "ETDH, comprometida en el PDI 2022-2026 con metas explícitas: 10 programas ETDH con "
            "750 estudiantes cada uno, y un colegio virtual de 100 estudiantes al 2026. La Fase "
            "I ya se completó, pero los tres proyectos siguen en pausa a la espera de las "
            "definiciones necesarias para continuar. Resolver esas definiciones es la decisión "
            "estratégica central para el PDI 2026-2030: avanzar a la siguiente fase con el caso "
            "de negocio ya validado, redefinir su alcance, o descontinuar formalmente esta "
            "apuesta en favor de profundizar el frente de educación continua B2B/B2G, que sí "
            "demostró tracción. A esto se suman dos indicadores por seguir de cerca: ingresos "
            "B2G (97,4%) y otros ingresos por cursos y opciones de grado (96%), ambos "
            "levemente por debajo de meta."
        ),
    },
}


def main() -> None:
    settings = get_settings()
    excel = ExcelReaderService(settings)
    svc = ResumenService(excel)
    data = ensamblar_narrativa(svc, TEXTOS_LINEAS, TEXTOS_CONSOLIDADO, TARJETAS_CONSOLIDADO)
    path = guardar(data)
    print(f"Narrativa estratégica guardada en: {path}")


if __name__ == "__main__":
    main()
