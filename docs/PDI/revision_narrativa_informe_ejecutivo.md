# Revisión de textos — Informe Ejecutivo / Estratégico PDI (Cierre 2022-2025)

> Fuente: `backend/scripts/generar_narrativa_estrategica.py` (autoría directa, no LLM).
> Todas las cifras entre paréntesis ya están corregidas con el fix de topes/exclusión Stand-by/rango de fechas 2021-2025 (commit `ae7a20c`).

> **Actualización 2026-09-29 — refresco de datos del Centro de Proyectos PMO:** el archivo fuente `centroDeProyectos_PMO_2026.xlsx` cambió (los % de avance subieron en casi todas las líneas) mientras se trabajaba en este documento. Se regeneraron todas las cifras de "Proyectos" y "Consolidado" de las 6 líneas con los datos nuevos. Sumado a la eliminación de SNIES (ver más abajo), el global pasó de **98,8% a 100,8%**.

> **Cambio de arquitectura 2026-09-30 (confirmado con negocio, revierte la decisión del 2026-09-27):** las CIFRAS de proyectos (Meta/Ejecución/Cumplimiento) SIEMPRE deben venir de **Resultados Consolidados**, nunca del Centro de Proyectos PMO — el PMO solo aporta **fechas** (para el Gantt) y **cualitativo** (objetivo/entregables/impactos). Se detectó que una migración renombró los proyectos a Ids "PRY-XX" en el catálogo sin propagar el cambio a las hojas de cierre, por lo que el cruce anterior por Id fallaba en silencio (ej. Expansión aparecía con 0 proyectos). Se reconstruyó el cruce por **nombre** entre catálogo (Id PRY-1..44, el universo oficial de **44 proyectos**), "Cierre PDI", "Consolidado Cierres" y el PMO — ver `ProyectosOficialesService`. 5 nombres no coincidían textualmente y se resolvieron a mano con el usuario (Id 10.1 para PRY-11, Id 901 para PRY-17 confirmado Stand by sin cifra, y overrides confirmados para PRY-33/43/44). Cobertura final: **43 de 44 proyectos con cifra real** (antes: 0 en Expansión). El global vuelve a moverse: de 100,8% a **100,7%**.

> ⚠️ **Nota importante:** con este cambio, **Expansión ahora tiene solo 2 proyectos oficiales** (Pricing, Proyecto Silver) — "Implementación de HubSpot Eduvida" no es parte de los 44 oficiales (Id > PRY-44). De igual forma, Experiencia pasa de 7 a **6** proyectos (sale "Remodelaciones bloque I y C") y Transformación Organizacional de 16 a **15** (sale "Automatización y Optimización proceso contractual"). Estos proyectos "extra" existen en el PMO pero no en el catálogo oficial del ciclo 2022-2025 — quedan fuera de las tablas y promedios del PDF, aunque el texto de "Pendientes" puede seguir mencionándolos como iniciativas emergentes de cara al PDI 2026-2030.

---

## Consolidado general

### Resumen ejecutivo

*(Reescrito 2026-09-27 a pedido explícito: enfoque en logros e impactos, no en cifras. La acreditación CNA se describe como ya otorgada — confirmado contigo: mayo 2026, 6 años.)*

*(Corrección 2026-09-28: Eduvida/ETDH no "nunca se activó" — ejecutó su Fase I, y está pendiente de definiciones para continuar, no en pausa desde el origen.)*

El Politécnico Grancolombiano cierra el ciclo del PDI 2022-2026 con su logro más significativo del periodo: la acreditación institucional en alta calidad por 6 años, otorgada por el CNA en mayo de 2026, que reconoce una formación que va más allá de lo académico e incluye acompañamiento, innovación y oportunidades reales para su comunidad. Ese reconocimiento externo confirma una transformación que ya se percibía al interior de la institución, con una experiencia estudiantil que mejoró de forma sostenida (NPS +25,4 puntos) y una cultura organizacional que avanzó por encima de lo esperado, certificada por Great Place to Work. Esa transformación se apalancó en una arquitectura tecnológica y de datos consolidada (Banner, Data Lake, HubSpot, POLISIGS certificado ISO 9001:2015), que hoy permite decisiones más ágiles y basadas en evidencia en toda la institución. La ejecución estratégica respalda estos logros: las seis líneas del PDI cerraron el ciclo con un desempeño sólido y equilibrado entre sí. Sostenibilidad se destacó con una ejecución de proyectos ejemplar y una gestión financiera responsable. El principal pendiente del ciclo está en Educación para toda la vida: sus proyectos de incursión en Educación Media y ETDH ya ejecutaron su Fase I, pero están a la espera de las definiciones necesarias para continuar. Resolver esas definiciones es la tarea prioritaria para completar la apuesta de acceso y cobertura del PDI en el próximo ciclo.

### Logros (consolidado)

*(Ajustado para no contradecir al resumen ejecutivo: la acreditación ya no se describe como "en avance" sino como otorgada.)*

*(Ampliado a pedido explícito: se agregan logros financieros, sostenibilidad social y ambiental, becas, nuevos programas y crecimiento de estudiantes — todos con soporte en el CMI real: EBITDA/Utilidad Neta sobrecumplidos, ISO 14001:2015 ampliada a Medellín, Ecosistema E3, Estudiantes con Becas 5,43% vs meta 5%, 26 nuevos programas presenciales+virtuales, crecimiento por encima de meta en los 4 segmentos de población estudiantil.)*

*(Corrección: "Caja" no es el indicador financiero más relevante para un resumen ejecutivo — es liquidez, no rentabilidad. Se reemplaza por EBITDA (117,5% de cumplimiento) y Utilidad Neta (130%), los indicadores de rentabilidad reales del CMI de Sostenibilidad.)*

*(Agregado: % de crecimiento de la población total 2022 vs. 2025 — Total Población, Id 14: 50.241 (2022) → 56.807 (2025, cierre oficial "Cierre PDI") = **+13,1%**. Cierre con tono más positivo a pedido explícito.)*

Los logros transformacionales del ciclo, ordenados según las líneas estratégicas, parten de Calidad, con la acreditación institucional en alta calidad que el CNA otorgó a la Sede Bogotá por seis años. En Expansión, la institución puso en marcha 26 nuevos programas entre presenciales y virtuales, y la población estudiantil aumentó 13,1% frente a 2022, al pasar de 50.241 a 56.807 estudiantes, por encima de la meta en los cuatro segmentos: presencial, virtual, pregrado y posgrado. En Experiencia, la comunidad Poli percibió una mejora medible en su relación con la institución, reflejo del trabajo hecho sobre el servicio y el acompañamiento a estudiantes. En Transformación Organizacional, se consolidó la arquitectura tecnológica y de datos institucional, se registró una mejora medible en la cultura del talento humano, y la gestión financiera se mantuvo sólida, con EBITDA y utilidad neta muy por encima de sus metas. En Sostenibilidad, la certificación ISO 14001:2015 se extendió a la sede de Medellín, el Ecosistema E3 abrió una ruta formal de empleabilidad y emprendimiento para los graduados, y la proporción de estudiantes becados superó lo proyectado.

### Retos priorizados (consolidado)

*(Reescrito 2026-09-28 a pedido explícito: foco en Centro de Analítica, Expansión y programas de Eduvida, grounded en indicadores Prov- catalogados — Prov-10/11/12/14/15/16 (Transformación Organizacional: gobierno de TI, microservicios, Smart Assistant, Centro de Excelencia Analítica, madurez analítica, modelos IA) y Prov-5/Prov-7 (Educación para toda la vida: microcertificaciones, matrícula IEDTH). SNIES se retira de aquí porque fue cancelado, no cerrado — ver nota abajo.)*

Los retos priorizados para el PDI 2026-2030 se concentran en tres frentes: consolidar el Centro de Excelencia Analítica y la madurez analítica institucional —gobierno de TI, arquitectura de microservicios y modelos de inteligencia artificial— como palanca de decisiones basadas en datos para toda la institución; sostener el ritmo de expansión que definió este ciclo, ampliando los mecanismos de diferenciación comercial y diversificación de mercado ya validados en Pricing y Proyecto Silver; y definir la ruta a seguir para los programas de Eduvida, cuya Fase I ya fue ejecutada y hoy está a la espera de las definiciones necesarias para continuar. En conjunto, esta es la agenda de continuidad estratégica que el cierre 2022-2025 deja formulada para el siguiente ciclo de planeación.

> **Correcciones 2026-09-28:**
> 1. **SNIES es un indicador cancelado**, no cerrado/completado — corregido en el texto de Transformación Organizacional (ya no dice "se cerró", dice "fue cancelado" y ya no implica que la base de datos quedó depurada). El CMI vigente todavía muestra este indicador con meta=100%, ejecución=57%, cumplimiento=56,8%, nivel Peligro — si ya está cancelado, hay que pedir que se retire o se marque como tal en el cierre oficial para que la tabla CMI y la Hoja de Ruta del PDF dejen de mostrarlo como crítico.
> 2. **Eduvida/ETDH**: el Gantt de proyectos del PDF (`report.html`) y el timeline del frontend (`ProyectosPmoTimeline.tsx`) **ya muestran correctamente "Stand by"** para estos 3 proyectos, no un "0%" — verificado en el código (ambos ocultan el % y muestran el badge gris cuando `stand_by=true`). Mi nota anterior sobre esto era incorrecta y quedó corregida.

---

## 1. Calidad

**Cifras:** Retos 97,8% · Proyectos 86,3% (n=15) · Indicadores 106,4% · **Consolidado 96,8%**

### Logros — Retos
El desempeño de los retos institucionales asociados a Calidad cierra en 97,8% de cumplimiento, con una ejecución sostenida y sin sobresaltos a lo largo del ciclo 2022-2025 — evidencia de que el despliegue operativo de la línea estuvo alineado con la meta desde el inicio, sin picos de recuperación de último momento.

### Logros — Proyectos
En proyectos, la línea alcanza un avance promedio de 86,3% sobre 15 iniciativas, con el hito central del ciclo ya materializado: la acreditación institucional en alta calidad de la Sede Bogotá fue otorgada por el CNA en mayo de 2026 por 6 años, tras el informe de autoevaluación radicado, la visita de pares académicos de octubre de 2025 con concepto altamente positivo, y el Plan de Mejoramiento Institucional aprobado por el Consejo Directivo. En paralelo cerraron proyectos de transformación curricular y de experiencia formativa —Innovación Curricular, Cultura de una Buena Docencia, CREA y el Catálogo de Recursos Virtuales—, que sostienen la calidad académica más allá del hito puntual de acreditación. Dos iniciativas siguen en fase de planeación sin ejecución iniciada: el Sistema de Medición de Resultados de Aprendizaje y el Fortalecimiento del proceso de visibilidad nacional e internacional.

### Logros — Indicadores
El CMI de la línea promedia 106,4% de cumplimiento. La relación estudiante-docente de tiempo completo se ubica en 83 estudiantes por docente frente a una meta de 81 (97,8% de cumplimiento), una tensión leve pero real entre el crecimiento de matrícula y la capacidad de la planta docente. A esto se suma que el 100% de los programas académicos ya cuenta con resultados de aprendizaje implementados, la base técnica que sostiene la acreditación.

### Logros — Consolidado
En conjunto, Calidad consolida su objetivo estratégico central —asegurar la acreditación institucional en alta calidad— con un desempeño equilibrado en las tres dimensiones (retos 97,8%, proyectos 86,3%, indicadores 106,4%): la ejecución operativa fue estable, la acreditación fue efectivamente otorgada por el CNA, y los indicadores estructurales (planta docente, resultados de aprendizaje) confirman que el resultado es una maduración real de los procesos académicos institucionales, no solo el cumplimiento de un hito puntual.

### Pendientes y prioridades
*(Ampliado 2026-09-28 a pedido explícito: se agrega la implementación de la reforma curricular de programas académicos como tercera prioridad.)*

La prioridad inmediata de la línea es poner en marcha dos proyectos que siguen en fase de planeación: el Sistema de Medición de Resultados de Aprendizaje, pieza clave para sostener la mejora continua curricular lograda en este ciclo, y el Fortalecimiento del proceso de visibilidad nacional e internacional. Dos indicadores requieren seguimiento cercano: productos de investigación, innovación y creación (94,2%) y relación estudiante-docente de tiempo completo (97,8%). Aunque ambos están cerca de la meta, señalan la tensión entre el crecimiento de la oferta académica y la capacidad de la planta docente e investigativa para sostenerlo. Para el PDI 2026-2030 la línea se enfoca en tres frentes: implementar el Sistema de Medición de Resultados de Aprendizaje como habilitador de la siguiente etapa de calidad, ejecutar la reforma curricular de los programas académicos que sostenga la acreditación recién obtenida, y diseñar una estrategia propia de fortalecimiento de investigación y planta docente, que crezca al mismo ritmo que la oferta académica.

---

## 2. Expansión

**Cifras:** Retos 98,9% · Proyectos 100,0% (n=2) · Indicadores 107,5% · **Consolidado 102,1%**

### Logros — Retos
Los retos de Expansión cierran en 98,9% de cumplimiento, el más alto del portafolio en esta dimensión, reflejo de una ejecución consistente del crecimiento planeado de matrícula a lo largo de los cuatro años del ciclo.

### Logros — Proyectos
En proyectos, la línea cierra sus 2 iniciativas al 100%: Pricing, que construyó una estrategia de precios institucional basada en el análisis de elasticidad de demanda por programa y en la diferenciación de descuentos como política comercial; y Proyecto Silver, que estructuró una oferta institucional dirigida a la población mayor de 50 años, ampliando el mercado más allá del segmento tradicional.

### Logros — Indicadores
El CMI promedia 107,5% de cumplimiento, con sobrecumplimiento marcado en los indicadores de posicionamiento de marca: el valor de marca llegó a 125,8% de la meta y el conocimiento espontáneo de la institución a 122,2%. Estos resultados acompañan el crecimiento de población estudiantil, que superó la meta en todos sus segmentos (presencial, virtual, pregrado y posgrado).

### Logros — Consolidado
El resultado consolidado de Expansión (retos 98,9%, proyectos 100%, indicadores 107,5%) muestra una línea que ya no depende únicamente del crecimiento inercial de la matrícula: sus dos proyectos, ya cerrados (Pricing, Proyecto Silver), instalan mecanismos deliberados de diferenciación comercial y diversificación de mercado, mientras los indicadores confirman que el posicionamiento de marca se fortaleció en paralelo al crecimiento. Es la línea con mejor desempeño equilibrado entre las tres dimensiones del ciclo.

### Prioridades para el próximo ciclo
Expansión cierra el ciclo sin proyectos por cerrar ni indicadores en zona crítica, lo que la posiciona como la línea de mayor estabilidad del portafolio. La prioridad para el PDI 2026-2030 no es de contención sino de escalamiento: llevar a implementación plena las hipótesis validadas por Pricing y Proyecto Silver, hoy en fase de diseño estratégico, y evaluar nuevos segmentos de crecimiento, como el relacionamiento empresa-Estado y la internacionalización, que sostengan el ritmo alcanzado una vez se agote el margen de crecimiento del modelo actual.

---

## 3. Educación para toda la vida

**Cifras:** Retos 94,7% · Proyectos **N/A** (3 proyectos en stand by, excluidos) · Indicadores 107,8% · **Consolidado 101,2%** (promedio de solo 2 dimensiones)

### Logros — Retos
Los retos de Educación para toda la vida cierran en 94,7% de cumplimiento, el más bajo del portafolio.

### Logros — Proyectos
*(Corregido 2026-09-28: la Fase I sí se ejecutó — ahora con el detalle de la alianza con CAFAM. Estado "Stand by" ya se muestra correctamente en el Gantt del PDF, sin mostrar 0% — ver corrección en "Retos priorizados".)*

En proyectos, la línea completó la Fase I de sus tres iniciativas: el Instituto de Educación para el Trabajo y el Desarrollo Humano (IETDH), el Colegio Virtual y el Centro de Idiomas Poli. Los dos primeros avanzan de la mano de CAFAM como aliado estratégico, con la etapa legal ya resuelta: los análisis de viabilidad quedaron listos en ambos casos, y en IETDH también se cerró el análisis del contexto regulatorio. El siguiente paso es definir el modelo pedagógico y regulatorio del Colegio Virtual, y el portafolio de programas y el modelo de operación de IETDH, dejando a los tres proyectos listos para avanzar a su siguiente fase en el próximo ciclo del PDI.

### Logros — Indicadores
*(Actualizado 2026-09-29: se agrega el indicador agregado "Ingresos totales de educación para la vida" — ver nota ⚠️ abajo, mismo patrón que Cumplimiento de Ingresos de Sostenibilidad.)*

El CMI promedia 107,8% de cumplimiento, resultado impulsado principalmente por el frente de educación continua: los ingresos B2B crecieron muy por encima de la meta, con un cumplimiento de 130%, lo que confirma que el relacionamiento con el sector empresarial logró resultados comerciales concretos en el ciclo. El indicador agregado de ingresos totales de educación para la vida cerró 2025 en 108,9% (meta $17.058, ejecución $18.570), consistente con el buen desempeño de sus componentes B2B, B2G y otros ingresos. El segundo objetivo de la línea aún no arrancó y será foco de atención en el próximo ciclo.

> ⚠️ **Hallazgo de calidad de dato:** "Ingresos totales de educación para la vida" (Id 385) tiene valores reales en "Consolidado Cierres" (108,9% en el cierre 2025: meta $17.058, ejecución $18.570) pero la hoja oficial "Cierre PDI" tiene esa fila vacía — mismo patrón exacto que "Cumplimiento de Ingresos" (Id 203, Sostenibilidad). Mientras "Cierre PDI" no se actualice, sigue sin contar en el total oficial de 48 indicadores (49 antes de retirar SNIES) ni aparece en la tabla CMI, solo en el texto. Revisé también el tercer indicador "sin medición" ("Nivel de empleabilidad del graduado", Id 331): ese es un caso distinto — no tiene Meta en ninguna hoja (ni Cierre PDI ni Consolidado Cierres), solo ejecución (81-83%), así que no hay cumplimiento que calcular en ningún lado.

### Logros — Consolidado
El balance consolidado (retos 94,7%, indicadores 107,8%; proyectos N/A) promedia 101,2%, revela dos velocidades marcadamente distintas. El frente de educación continua (B2B/B2G) funciona y genera resultados comerciales reales, mientras la incursión en Educación Media y ETDH —comprometida en el PDI 2022-2026 con metas explícitas— ejecutó su Fase I pero sus 3 proyectos están en stand by a la espera de definiciones para continuar. Es la línea que más requiere una decisión estratégica explícita antes de iniciar el PDI 2026-2030.

### Pendientes y prioridades
El principal foco estratégico de la línea es la incursión en Educación Media y ETDH, comprometida en el PDI 2022-2026 con metas explícitas: 10 programas ETDH con 750 estudiantes cada uno, y un colegio virtual de 100 estudiantes al 2026. La Fase I ya se completó, pero los tres proyectos siguen en pausa a la espera de las definiciones necesarias para continuar. Resolver esas definiciones es la decisión estratégica central para el PDI 2026-2030: avanzar a la siguiente fase con la viabilidad ya validada, redefinir su alcance, o descontinuar formalmente esta apuesta en favor de profundizar el frente de educación continua B2B/B2G, que sí demostró resultados comerciales. A esto se suman dos indicadores por seguir de cerca: ingresos B2G (97,4%) y otros ingresos por cursos y opciones de grado (96%), ambos levemente por debajo de meta.
---

## 4. Experiencia

**Cifras:** Retos 98,1% · Proyectos 98,8% (n=6) · Indicadores 103,4% · **Consolidado 100,1%**

### Logros — Retos
Los retos de Experiencia cierran en 98,1% de cumplimiento, con una ejecución sostenida a lo largo del ciclo.

### Logros — Proyectos
El avance promedio en proyectos es de 98,8% sobre 6 iniciativas, todas ya cerradas. El hito central es la implementación en tres fases del Hub de Experiencia y Agilismo (HEYA), que rediseñó la gestión de la experiencia institucional a partir de mapas de ruta del estudiante y metodologías ágiles. En paralelo, el Centro Gastronómico redujo en 80% el costo anual de prácticas del programa de Hotelería y Gastronomía al eliminar la dependencia de terceros, y el Proyecto de Permanencia Institucional desplegó el modelo KITUS de acompañamiento segmentado con resultados diferenciados en los grupos de mayor riesgo de deserción.

### Logros — Indicadores
*(Reescrito 2026-09-28 a pedido explícito: mejor redacción, se agrega el 4º indicador que faltaba (ANS) y se corrige permanencia intersemestral a la cifra exacta del CMI — 86% ejec./meta, no 86,2%.)*

El CMI promedia 103,4% de cumplimiento, con las cuatro dimensiones de la experiencia estudiantil por encima de su meta. El NPS subió 25,4 puntos en el ciclo (de 32,2 a 58,6) y el Índice de Satisfacción del Estudiante llegó a 90%, evidencia de un vínculo cada vez más sólido con la comunidad estudiantil. Ese vínculo se sostiene en la operación: el Acuerdo de Nivel de Servicio se cumplió en 95% y la permanencia intersemestral alcanzó el 86% proyectado, señal de que la mejora en percepción vino acompañada de una gestión operativa consistente.

### Logros — Consolidado
El resultado consolidado (retos 98,1%, proyectos 98,8%, indicadores 103,4%) muestra una línea que migró de una gestión reactiva de la experiencia a una arquitectura de mapas de ruta y agilismo institucionalizados, con resultados ya visibles en satisfacción y permanencia estudiantil, y con la mayoría de sus proyectos estructurales ya cerrados.

### Pendientes y prioridades
Tres iniciativas de analítica avanzada para la permanencia (modelo predictivo de deserción basado en puntuación de riesgo, IA de voz e IA de WhatsApp para recuperación de estudiantes) están en fase de planeación, sin que ningún indicador en zona crítica obligue a acelerarlas. Esto abre una oportunidad de ampliación más que una alerta. La prioridad para el PDI 2026-2030 es llevar estas tres iniciativas de datos a producción, para extender el modelo KITUS, que ya demostró resultados medibles en grupos piloto, hacia una cobertura institucional completa del acompañamiento estudiantil.

---

## 5. Transformación Organizacional

**Cifras:** Retos 97,5% · Proyectos 98,7% (n=15) · Indicadores 106,6% (n=9) · **Consolidado 100,9%**

*(Actualizado 2026-09-29: se elimina "% de depuración histórico SNIES" del PDF (indicador cancelado, a pedido explícito) — n indicadores pasa de 10 a 9, indicadores 101,6%→106,6%. Además el Centro de Proyectos PMO se actualizó: proyectos 81,4%→91,7% (Gobierno de Datos pasó de 5% a prácticamente 100%). Consolidado final 93,5%→98,6%. Impacto en cascada: total de indicadores del informe 49→48, atención 2→1, global 98,8%→100,8%.)*

### Logros — Retos
Los retos de Transformación Organizacional cierran en 97,5% de cumplimiento, estable durante todo el ciclo, pese a ser la línea con la agenda de ejecución más densa del portafolio.

### Logros — Proyectos
Con 15 proyectos, es la línea con mayor densidad de iniciativas del ciclo, y su avance promedio (98,7%) refleja una ejecución consistente: 11 de ellos ya cerraron. En el frente tecnológico: la migración del ecosistema académico Banner a su versión más reciente sobre Oracle Cloud, la centralización de datos institucionales en un Data Lake bajo metodología Data Vault, la integración Banner-HubSpot-FDI para la gestión de aspirantes y estudiantes, y la certificación ISO 9001:2015 del nuevo POLISIGS (con ampliación de alcance auditada por ICONTEC). En el frente humano, el Plan Talento y el nuevo Portal Web Universitario completan el cierre.

### Logros — Indicadores
*(Complementado 2026-09-28 a pedido explícito: la línea tiene 3 objetivos y el texto solo cubría el humano/cultural — se agregan indicadores de arquitectura tecnológica y de gestión por procesos/datos.)*

El CMI promedia 106,6% de cumplimiento (9 indicadores vigentes — la depuración del histórico SNIES fue cancelada en el ciclo y se retira del conteo), con logros en los tres objetivos de la línea. En el frente humano, el indicador más visible del cambio cultural es el Great Place to Work, con una ejecución de 81,0 puntos frente a una meta de 68,7 (117,9% de cumplimiento), acompañado de una satisfacción con los servicios prestados de 85% y una reducción del índice de rotación a 0,89 frente a una meta de 1,2 — evidencia de que la transformación cultural fue medible, no solo declarada. En arquitectura tecnológica, la disponibilidad de servicios tecnológicos llegó a 97,7%, por encima de la meta. Y en gestión por procesos y datos, la cobertura de recolección de variables para analítica (ADA) alcanzó 100% de la información solicitada por el SNIES, la base sobre la que se construirá el Centro de Excelencia Analítica del próximo ciclo.

### Logros — Consolidado
El balance consolidado (retos 97,5%, proyectos 98,7% sobre 15 iniciativas, indicadores 106,6%) confirma que la transformación organizacional del ciclo operó en dos frentes simultáneos y complementarios: una arquitectura tecnológica y de datos que pasó de fragmentada a gobernada, y una cultura organizacional con mejoras medibles en clima laboral. Es la combinación de ambos frentes la que constituye la transformación de fondo que el PDI 2022-2026 se propuso para esta línea.

### Pendientes y prioridades
*(Corregido 2026-09-28: SNIES es un indicador cancelado, no cerrado/completado — ver nota en "Retos priorizados" sobre el desfase con el CMI vigente, que aún muestra 56,8%/Peligro.)*

*(Corrección 2026-09-28: las tres iniciativas ya iniciaron ejecución — dices que no siguen en planeación pura. Ajustado a "ya iniciaron ejecución y continúan en desarrollo".)*

*(Actualizado 2026-09-29: el Centro de Proyectos PMO ahora muestra Gobierno de Datos en ~100%, no 5% — reescrito para reflejar el proyecto prácticamente cerrado, no como pendiente de implementar.)*

El proyecto de Gobierno de Datos cerró el ciclo prácticamente completo, dejando lista la base de calidad de dato para el Centro de Excelencia Analítica del próximo PDI. Persisten dos frentes: la automatización del proceso contractual sigue en planeación, sin ejecución iniciada, mientras las homologaciones con IA en Ilumno y la reforma curricular tecnológica ya avanzan en desarrollo. Para el PDI 2026-2030 el foco de esta línea es doble: consolidar institucionalmente el Centro de Excelencia Analítica sobre la base de datos ya gobernada, y decidir si la automatización contractual se ejecuta, se rediseña o se descontinúa antes de comprometer presupuesto del siguiente ciclo.

> ⚠️ **Nota de consistencia (V15) a revisar:** el Centro de Proyectos (maestro PMO, filtrado 2021-2025) todavía registra "Automatización y Optimización proceso contractual" con estado **Planeación** y 0% de avance, y "homologaciones con IA en Ilumno" / "reforma curricular tecnológica" **no aparecen** en el listado filtrado (puede ser que sus fechas de inicio estén vacías o fuera del rango 2021-2025). El texto ya quedó ajustado a que "ya iniciaron ejecución", pero mientras el maestro PMO no se actualice, la tabla/Gantt de proyectos del PDF va a seguir sin reflejar ese avance — mismo patrón de desfase texto/tabla que SNIES y Eduvida/ETDH.

---

## 6. Sostenibilidad

**Cifras:** Retos 97,9% · Proyectos 99,3% (n=3) · Indicadores 112,6% · **Consolidado 103,3%**

### Logros — Retos
Los retos de Sostenibilidad cierran en 97,9% de cumplimiento, con ejecución estable en el ciclo.

### Logros — Proyectos
Es la línea con mejor ejecución de proyectos del portafolio: 99,3% de avance promedio, con los 3 proyectos de la línea cerrados o prácticamente cerrados. La certificación ISO 14001:2015 se amplió a la sede Los Colores en Medellín, con reducciones verificadas de 18,9% en consumo eléctrico y 26% en consumo de agua per cápita; el Ecosistema E3 dio a los graduados una plataforma formal de empleabilidad y emprendimiento; y la política institucional de equidad de género quedó aprobada con líneas base definidas por vicerrectoría.

### Logros — Indicadores
*(Actualizado: se reemplaza Caja por EBITDA/Utilidad Neta [ya corregido antes] y se agrega Cumplimiento de Ingresos, 111,3%, usando el cierre 2025 de la hoja "Consolidado Cierres" — ver nota ⚠️ abajo.)*

El CMI promedia 112,6% de cumplimiento, el más alto del portafolio, apalancado en la ejecución financiera: EBITDA, Utilidad Neta y Cumplimiento de Ingresos sobrecumplieron meta (117,5%, 130% y 111,3% respectivamente). El componente social, en cambio, avanza más lento: el impacto de actividades de responsabilidad social llegó a 84,4% y la participación en voluntariados a 86,8%.

> ⚠️ **Hallazgo de calidad de dato:** "Cumplimiento de Ingresos" (Id 203, Sostenibilidad) tiene valores reales en la hoja "Consolidado Cierres" (111,3% en el cierre 2025), pero la hoja oficial **"Cierre PDI"** —de donde el Informe Ejecutivo toma Meta/Ejecución/Cumplimiento— tiene esa fila vacía (Meta/Ejecución en blanco, fecha "Avance" sin resolver). Usé el valor de "Consolidado Cierres" para el texto, pero mientras "Cierre PDI" no se actualice, este indicador **no aparece en el conteo oficial de indicadores del PDF** (el total de 48 indicadores, 49 antes de retirar SNIES / la tabla CMI de la línea no lo incluyen, porque esa tabla sale de un cruce que exige fila en "Cierre PDI"). Si confirman que 111,3% es el cierre correcto, hay que cargarlo también en "Cierre PDI" para que el indicador cuente en el total y aparezca en la tabla, no solo en el texto.

### Logros — Consolidado
El balance consolidado (retos 97,9%, proyectos 99,3%, indicadores 112,6%) confirma que Sostenibilidad es, junto con Expansión, la línea de mejor desempeño integral del ciclo, con una ejecución de proyectos ejemplar y una gestión financiera sólida — con la salvedad de que el componente de proyección social y voluntariado avanza a un ritmo menor que el ambiental y el financiero, y debe fortalecerse en el siguiente ciclo.

### Pendientes y prioridades
No hay proyectos pendientes de inicio en esta línea, pero cuatro indicadores requieren seguimiento gerencial: la ejecución de Opex (110,6%) y CAPEX (107,1%) supera lo presupuestado, lo que amerita revisar la disciplina de gasto frente a la planeación financiera, y el impacto de actividades de responsabilidad social (84,4%) y la participación en voluntariados (86,8%) quedan por debajo de meta, señal de que el componente de proyección social avanza más lento que el ambiental y el financiero. Para el PDI 2026-2030 la prioridad es doble: fortalecer el control de ejecución presupuestal y activar una estrategia específica de movilización de la comunidad hacia la proyección social, hoy el eslabón más débil de la línea.

> ⚠️ **Nota (Opex/CAPEX):** este párrafo trata Opex/CAPEX sobre-ejecutado como algo a "revisar", no como incumplimiento — coherente con tu decisión "mantener como está" (no se definió una regla de "dentro de presupuesto" separada). Señalado por transparencia, no requiere acción.

---

## Corrección adicional (post-revisión): Cumplimiento general de Retos (dashboard)

El chip "Cumplimiento general" de Retos (vista Retos y Consolidado del dashboard, hoja "Areas" del Excel) promediaba los 4 años del rango con el mismo peso (97,575%), sin considerar que el N° de áreas participantes creció fuertemente en el ciclo (33 en 2022 → 84 en 2025). Corregido a un promedio ponderado por N° de áreas de cada año: **97,9%** (`backend/app/services/retos_loaders.py::load_avance_global`). Esta cifra es un **total institucional global** (la hoja "Areas" no tiene columna Línea) — no reemplaza el cumplimiento de Retos por línea (94,7% Educación, 97,8% Calidad, etc.), que sigue viniendo de la hoja "Linea", el único dato con desglose por línea que existe. Confirmado contigo: el alcance de este fix es solo el global.

## Cambios frente a la versión anterior (para tu referencia rápida)

| Línea | Antes (previo al fix) | Ahora (corregido) | Motivo del cambio |
|---|---|---|---|
| Consolidado global | 106,9% (sin trazar) | **98,8%** | Fórmula = promedio de consolidados de línea |
| Calidad | 97,6% | 97,6% | Sin cambio (ningún proyecto Stand by / fuera de rango) |
| Expansión | proy. 72,0% (n=4) → cons. 92,8% | proy. **89,0%** (n=3) → cons. **98,5%** | 1 proyecto fuera del rango 2021-2025 |
| Educación para toda la vida | proy. 0% → cons. 67,5% | proy. **N/A** → cons. **101,2%** | Stand by ya no se promedia como 0% |
| Experiencia | proy. 66,3% (n=10) → cons. 89,3% | proy. **94,7%** (n=7) → cons. **98,7%** | 3 proyectos fuera de rango/planeación sin fecha |
| Transformación Organizacional | proy. 72,3% (n=18) → cons. 90,5% | proy. **81,4%** (n=16) → cons. **93,5%** | 2 proyectos fuera de rango 2021-2025 |
| Sostenibilidad | 103,5% | 103,5% | Sin cambio |
| Great Place to Work (texto) | "76→89, 172% de la meta" (dato inventado) | **meta 68,7 / ejec. 81,0 / 117,9%** | Corrección de dato falso (V4) |
| Relación estudiante-docente (texto) | "103→68,4, mejoró 33,6%" (dato inventado) | **meta 81 / ejec. 83 / 97,8%** | Corrección de dato falso (V4) |

## Actualización 2026-09-29 — eliminación de SNIES + refresco del Centro de Proyectos PMO

| Línea | Antes | Ahora | Motivo |
|---|---|---|---|
| Consolidado global | 98,8% | **100,8%** | SNIES retirado (indicador cancelado) + refresco de % de avance en el Centro de Proyectos PMO |
| Calidad | proy. 88,5% → cons. 97,6% | proy. **98,2%** → cons. **100,8%** | Refresco PMO |
| Expansión | proy. 89,0% → cons. 98,5% | proy. **95,2%** → cons. **100,5%** | Refresco PMO (HubSpot Eduvida 67%→86%) |
| Educación para toda la vida | cons. 101,2% | cons. **101,2%** | Sin cambio (proyectos siguen N/A, stand by) |
| Experiencia | proy. 94,7% → cons. 98,7% | proy. **99,6%** → cons. **100,4%** | Refresco PMO (Remodelaciones bloque I y C 63%→98%) |
| Transformación Organizacional | ind. 101,6% (n=10), proy. 81,4% → cons. 93,5% | ind. **106,6%** (n=9), proy. **91,7%** → cons. **98,6%** | SNIES retirado + refresco PMO (Gobierno de Datos 5%→~100%) |
| Sostenibilidad | proy. 100,0% → cons. 103,5% | proy. **99,3%** → cons. **103,3%** | Refresco PMO (Ecosistema E3 100%→98%) |
| Total indicadores del informe | 49 | **48** | SNIES retirado del CMI y de la Hoja de Ruta |
| Indicadores en atención | 2 | **1** | SNIES era uno de los 2 en Peligro |

Todas las cifras se recalculan automáticamente desde los datos (topes ya aplicados: 100% por proyecto, 130% por indicador) — no se editaron a mano.

## Actualización 2026-09-30 — cifras de proyectos vuelven a Resultados Consolidados (ProyectosOficialesService)

Revierte el uso del PMO como fuente de cifras (decisión del 2026-09-27). Universo fijo de **44 proyectos oficiales** (catálogo, Id PRY-1..44), cifras de Resultados Consolidados, fechas/estado del PMO — ver nota de arquitectura al inicio del documento.

| Línea | Antes (PMO como cifra) | Ahora (Resultados Consolidados) | Motivo |
|---|---|---|---|
| Consolidado global | 100,8% | **100,7%** | Cambio de fuente de cifras |
| Calidad | proy. 98,2% (n=15) → cons. 100,8% | proy. **86,3%** (n=15) → cons. **96,8%** | Cifra real de Resultados Consolidados, no el % completado del PMO |
| Expansión | proy. 95,2% (n=3) → cons. 100,5% | proy. **100,0%** (n=2) → cons. **102,1%** | HubSpot Eduvida no es parte de los 44 oficiales (Id > PRY-44); Pricing y Proyecto Silver, ambos 100% |
| Educación para toda la vida | cons. 101,2% | cons. **101,2%** | Sin cambio (proyectos siguen N/A, stand by) |
| Experiencia | proy. 99,6% (n=7) → cons. 100,4% | proy. **98,8%** (n=6) → cons. **100,1%** | Remodelaciones bloque I y C no es parte de los 44 oficiales |
| Transformación Organizacional | proy. 91,7% (n=16) → cons. 98,6% | proy. **98,7%** (n=15) → cons. **100,9%** | Automatización proceso contractual no es parte de los 44 oficiales; cifras reales de Resultados Consolidados |
| Sostenibilidad | proy. 99,3% → cons. 103,3% | proy. **99,3%** → cons. **103,3%** | Sin cambio (coincide por casualidad) |
| Total proyectos (portada y detalle) | 44 (portada) / 47 (detalle PMO) — dos cifras distintas | **44 en ambos** | Universo único: el catálogo oficial |
| Cobertura de cifra real | — | **43 de 44 (98%)** | Solo PRY-17 (Centro de Idiomas Fase I) queda "Sin medición" — confirmado Stand by sin cierre cargado |

Casos resueltos a mano con el usuario (nombres que no coincidían entre hojas por una migración de Ids no propagada):
- **PRY-11** "Acreditación Institucional - Fase I": el dato real está en Cierre PDI bajo el Id **10.1** ("...Sede Bogotá - Fase I"), no bajo PRY-11.
- **PRY-17** "Centro de Idiomas Fase I": existe en Cierre PDI (Id 901) pero sin Meta/Ejecución — confirmado Stand by real, no un vacío de carga.
- **PRY-33** "Ilumno Self Service S&P": sin cierre en ninguna hoja — confirmado Meta 100 / Ejecución 100.
- **PRY-43/PRY-44**: sin cierre en ninguna hoja — confirmado que a cierre de 2025 estaban en Planeación (0% de avance).
