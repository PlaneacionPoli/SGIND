# 📋 Guía de Prompts IA — CMI Estratégico
**Sistema de Indicadores · Politécnica Grancolombiana**
**Corte: Diciembre 2023 | Versión: 1.0**

---

> **Cómo usar esta guía**
> Cada sección corresponde a una vista o componente del dashboard CMI Estratégico.
> Copia el prompt completo, pégalo en tu IA preferida (Claude, ChatGPT, Gemini, etc.),
> reemplaza los valores entre `[corchetes]` con los datos reales del período a analizar,
> y obtendrás el análisis, texto o contenido listo para integrar al dashboard o informes.

---

## 🗂️ Índice de Secciones

1. [Resumen Ejecutivo General](#1-resumen-ejecutivo-general)
2. [Ficha de Indicador Individual](#2-ficha-de-indicador-individual)
3. [Análisis por Línea Estratégica](#3-análisis-por-línea-estratégica)
4. [Análisis de Alertas y Riesgos](#4-análisis-de-alertas-y-riesgos)
5. [Comparativo entre Líneas](#5-comparativo-entre-líneas)
6. [Análisis de Tendencia y Proyección](#6-análisis-de-tendencia-y-proyección)
7. [Narrativa para Informe de Junta o Consejo](#7-narrativa-para-informe-de-junta-o-consejo)
8. [Recomendaciones Estratégicas por Línea](#8-recomendaciones-estratégicas-por-línea)
9. [Resumen para Comunicación Interna](#9-resumen-para-comunicación-interna)
10. [Generación de Objetivos del Próximo Período](#10-generación-de-objetivos-del-próximo-período)

---

## 1. Resumen Ejecutivo General

> **Uso:** Vista "📊 Resumen" del dashboard — tarjetas KPI y síntesis global.

```
Actúa como analista institucional de la Politécnica Grancolombiana.

Con base en los siguientes datos del CMI Estratégico, corte [MES AÑO]:

- Total de indicadores PDI: [N]
- Indicadores con cumplimiento reportado: [N]
- Promedio general de cumplimiento: [X]%
- Distribución por nivel:
  * Sobrecumplimiento (≥100%): [N] indicadores ([X]%)
  * Cumplimiento (90%-99%): [N] indicadores ([X]%)
  * Alerta (75%-89%): [N] indicadores ([X]%)
  * Riesgo (<75%): [N] indicadores ([X]%)
- Línea con mayor cumplimiento: [NOMBRE] con [X]%
- Línea con menor cumplimiento: [NOMBRE] con [X]%

Genera:
1. Un párrafo de RESUMEN EJECUTIVO (máx. 120 palabras) para presentar al Rector
   y al Consejo Directivo. Tono formal, enfocado en logros y situaciones críticas.

2. Tres HALLAZGOS CLAVE en formato de viñetas cortas (máx. 20 palabras cada una).

3. Un SEMÁFORO narrativo: ¿cuál es el estado general de la institución?
   Usa una de estas categorías: 🟢 Favorable / 🟡 En seguimiento / 🔴 Crítico.
   Justifica en 2-3 frases.

Usa lenguaje institucional colombiano, evita tecnicismos excesivos.
```

---

## 2. Ficha de Indicador Individual

> **Uso:** Modal "Ver ficha" del dashboard — análisis profundo de un indicador específico.

```
Actúa como experto en planeación estratégica universitaria.

Analiza el siguiente indicador del Plan de Desarrollo Institucional (PDI):

- Nombre del indicador: [NOMBRE COMPLETO]
- Línea estratégica: [LÍNEA]
- Objetivo estratégico: [OBJETIVO]
- Meta del período: [META]
- Ejecución real: [EJECUCIÓN]
- Porcentaje de cumplimiento: [X]%
- Nivel: [Sobrecumplimiento / Cumplimiento / Alerta / Riesgo]
- Contexto adicional (opcional): [DESCRIPCIÓN O NOTAS DEL RESPONSABLE]

Genera los siguientes bloques de análisis:

**A. INTERPRETACIÓN DEL RESULTADO** (60-80 palabras)
Explica qué significa este resultado en el contexto institucional.
¿Es relevante la brecha o el excedente? ¿Qué lo puede explicar?

**B. FACTORES QUE INCIDEN**
Lista 3-4 posibles factores internos y/o externos que explican el resultado.
Formato: "• [Factor]: [breve explicación]"

**C. RECOMENDACIÓN DE ACCIÓN** (según nivel)
- Si Sobrecumplimiento: cómo consolidar y documentar la buena práctica.
- Si Cumplimiento: cómo sostener y prevenir caída.
- Si Alerta: plan de acción prioritario en los próximos 30-60 días.
- Si Riesgo: acciones urgentes, responsables sugeridos y métricas de seguimiento.

**D. MENSAJE PARA EL RESPONSABLE** (2-3 frases)
Redacta un mensaje motivador y orientador, listo para enviar al líder del proceso.
```

---

## 3. Análisis por Línea Estratégica

> **Uso:** Vista "📋 Por Línea" — pestaña "Análisis" de cada línea estratégica.

```
Actúa como analista del CMI Estratégico de la Politécnica Grancolombiana.

Analiza la siguiente línea estratégica, corte [MES AÑO]:

**Línea: [NOMBRE DE LA LÍNEA]**
Color institucional: [COLOR]

Objetivos e indicadores:
[Copia aquí la tabla de indicadores de la línea con sus metas, ejecuciones y % cumplimiento]

Ejemplo de formato:
| Indicador | Meta | Ejecución | Cumplimiento | Nivel |
|-----------|------|-----------|--------------|-------|
| [nombre]  | [X]  | [Y]       | [Z]%         | [nivel] |

Genera:

**1. DIAGNÓSTICO DE LA LÍNEA** (100-130 palabras)
Evalúa el comportamiento general de la línea. ¿Está alineada con la estrategia institucional?
¿Cuáles objetivos jalan más y cuáles presentan rezago?

**2. INDICADORES DESTACADOS**
- 🏆 El de mejor desempeño: [por qué es significativo]
- ⚠️ El de mayor preocupación: [impacto estratégico de no resolverse]

**3. ANÁLISIS DE COHERENCIA INTERNA**
¿Los indicadores de esta línea son consistentes entre sí?
¿Hay tensiones o contradicciones (ej. un indicador sube pero otro relacionado baja)?

**4. PRÓXIMOS PASOS RECOMENDADOS**
3 acciones concretas ordenadas por prioridad para el siguiente período.
Formato: "1. [Acción] — Responsable sugerido: [área] — Plazo: [X semanas/meses]"

Usa tono técnico-gerencial. Máximo 350 palabras en total.
```

---

## 4. Análisis de Alertas y Riesgos

> **Uso:** Vista "⚠️ Alertas" del dashboard — narrativa de riesgo institucional.

```
Actúa como director de planeación institucional de una universidad colombiana.

Los siguientes indicadores del CMI Estratégico presentan niveles críticos en el corte [MES AÑO]:

**INDICADORES EN RIESGO (<75% cumplimiento):**
[Lista cada uno con: nombre, línea, meta, ejecución, % cumplimiento]

**INDICADORES EN ALERTA (75%-89% cumplimiento):**
[Lista cada uno con: nombre, línea, meta, ejecución, % cumplimiento]

Genera:

**A. ANÁLISIS DE RIESGO INSTITUCIONAL**
¿Qué tan grave es la situación global? ¿Hay concentración de riesgos en alguna línea?
¿Podría haber efectos encadenados entre indicadores críticos? (90-120 palabras)

**B. FICHA DE RIESGO POR INDICADOR CRÍTICO**
Para cada indicador en RIESGO, genera:
- Descripción del riesgo: qué pasa si no mejora
- Probabilidad de recuperación al cierre del año: Alta / Media / Baja
- Impacto estratégico: Alto / Medio / Bajo
- Acción inmediata recomendada (1 frase)

**C. PLAN DE CONTINGENCIA RESUMIDO**
Un párrafo (60-80 palabras) con las medidas transversales que debería tomar
la alta dirección para gestionar estos riesgos antes del próximo corte.

**D. MENSAJE DE ALERTA PARA CORREO EJECUTIVO**
Redacta un correo corto (150 palabras máx.) del Director de Planeación
al Rector, informando sobre los indicadores críticos y solicitando reunión
de seguimiento urgente. Tono directo pero profesional.
```

---

## 5. Comparativo entre Líneas

> **Uso:** Vista de comparación — benchmark interno entre las 6 líneas del PDI.

```
Actúa como analista estratégico con experiencia en cuadros de mando integral (CMI/BSC).

Compara el desempeño de las siguientes líneas estratégicas del PDI,
corte [MES AÑO], Politécnica Grancolombiana:

| Línea | # Indicadores | Cumplimiento Promedio | SB | CU | AL | RI |
|-------|---------------|----------------------|----|----|----|-----|
| Expansión | [N] | [X]% | [N] | [N] | [N] | [N] |
| Calidad | [N] | [X]% | [N] | [N] | [N] | [N] |
| Experiencia | [N] | [X]% | [N] | [N] | [N] | [N] |
| Sostenibilidad | [N] | [X]% | [N] | [N] | [N] | [N] |
| Educación para toda la vida | [N] | [X]% | [N] | [N] | [N] | [N] |
| Transformación Organizacional | [N] | [X]% | [N] | [N] | [N] | [N] |

(SB=Sobrecumplimiento, CU=Cumplimiento, AL=Alerta, RI=Riesgo)

Genera:

**1. RANKING DE LÍNEAS** con justificación de por qué cada una ocupa su posición.

**2. ANÁLISIS DE BRECHAS**
¿Cuántos puntos porcentuales separan la mejor de la peor línea?
¿Es una brecha preocupante para la gestión institucional?

**3. PATRONES IDENTIFICADOS**
¿Hay alguna línea sistemáticamente fuerte o débil?
¿Qué dice esto sobre la capacidad institucional por área?

**4. TABLA SEMÁFORO NARRATIVA**
Para cada línea, una frase de diagnóstico + emoji de estado:
🟢 Fortaleza institucional / 🟡 Monitoreo activo / 🔴 Intervención requerida

**5. RECOMENDACIÓN DE PRIORIZACIÓN**
¿En cuál línea debería concentrarse el mayor esfuerzo en el próximo período?
Argumenta con base en impacto estratégico y viabilidad de mejora.
```

---

## 6. Análisis de Tendencia y Proyección

> **Uso:** Para análisis histórico cuando se dispone de datos de cortes anteriores.

```
Actúa como analista de datos institucionales con experiencia en planeación universitaria.

Tienes los siguientes datos históricos del indicador [NOMBRE DEL INDICADOR]
de la Politécnica Grancolombiana:

| Período | Meta | Ejecución | Cumplimiento |
|---------|------|-----------|--------------|
| [Período 1] | [X] | [Y] | [Z]% |
| [Período 2] | [X] | [Y] | [Z]% |
| [Período 3] | [X] | [Y] | [Z]% |
| [Período actual] | [X] | [Y] | [Z]% |

Genera:

**A. ANÁLISIS DE TENDENCIA**
¿El indicador muestra comportamiento creciente, decreciente o estable?
¿La brecha respecto a la meta se amplía o se reduce? (60-80 palabras)

**B. PROYECCIÓN AL CIERRE DEL AÑO**
Con base en la tendencia observada:
- Escenario optimista: [X]% de cumplimiento
- Escenario base: [X]% de cumplimiento
- Escenario pesimista: [X]% de cumplimiento
Explica brevemente el supuesto de cada escenario.

**C. PUNTO DE INFLEXIÓN**
¿Hubo algún período donde el comportamiento cambió drásticamente?
¿Qué lo pudo haber provocado?

**D. ALERTA TEMPRANA**
¿Debería activarse alguna alerta para el próximo corte?
¿Qué valor mínimo de ejecución en el siguiente período
indicaría que el indicador está en riesgo de incumplimiento al cierre?
```

---

## 7. Narrativa para Informe de Junta o Consejo

> **Uso:** Generación de texto formal para informes de gobierno institucional.

```
Actúa como Secretario General o Director de Planeación de una institución de educación
superior colombiana, redactando el capítulo de resultados estratégicos para
presentar ante el Consejo Directivo / Junta Directiva.

Datos del CMI Estratégico, corte [MES AÑO]:
[Pega aquí el resumen completo de todas las líneas con sus indicadores y cumplimientos]

Redacta el capítulo siguiendo esta estructura:

**1. PRESENTACIÓN DEL PERÍODO** (1 párrafo, 60 palabras)
Contextualiza el corte de evaluación y lo que representa en el ciclo del PDI.

**2. RESULTADOS GENERALES** (2 párrafos, 150 palabras)
Presenta los resultados globales con tono objetivo.
Destaca logros institucionales y reconoce las áreas de mejora
sin minimizar los riesgos.

**3. ANÁLISIS POR LÍNEA ESTRATÉGICA** (1 párrafo por línea)
Para cada línea: 2-3 frases que capturen lo más relevante.
Usa datos concretos (porcentajes, metas, nombres de indicadores).

**4. CONCLUSIÓN Y COMPROMISO** (1 párrafo, 80 palabras)
Cierra con el compromiso institucional de cara al próximo período.
¿Qué decisiones o acciones se derivan de estos resultados?

Formato: prosa corrida, sin viñetas. Lenguaje formal institucional colombiano.
Evita superlativos vacíos. Usa cifras reales. Longitud total: 500-600 palabras.
```

---

## 8. Recomendaciones Estratégicas por Línea

> **Uso:** Pestaña "Análisis" de cada línea — sección de recomendaciones accionables.

```
Actúa como consultor estratégico especializado en gestión universitaria.

Basándote en los resultados de la línea [NOMBRE DE LÍNEA] del CMI Estratégico
de la Politécnica Grancolombiana, corte [MES AÑO]:

Cumplimiento promedio de la línea: [X]%
Indicadores en Sobrecumplimiento: [N]
Indicadores en Alerta o Riesgo: [N]
Indicador con peor desempeño: [NOMBRE] — [X]% de cumplimiento

Genera un plan de recomendaciones con el siguiente formato:

---
### 🎯 Recomendación 1 — [TÍTULO CORTO]
**Tipo:** Correctiva / Preventiva / Mejora continua
**Indicador(es) relacionado(s):** [nombre(s)]
**Descripción:** (40-60 palabras) Qué se debe hacer y por qué.
**Responsable sugerido:** [Área o cargo]
**Recursos requeridos:** [Humanos / Tecnológicos / Financieros / Ninguno adicional]
**Plazo:** [Inmediato <30 días / Corto plazo 1-3 meses / Mediano plazo 3-6 meses]
**Indicador de éxito:** Cómo sabremos que funcionó.
---

Genera mínimo 3 y máximo 5 recomendaciones, ordenadas por prioridad.
La primera debe ser la más urgente.
No repitas recomendaciones genéricas. Sé específico al contexto institucional.
```

---

## 9. Resumen para Comunicación Interna

> **Uso:** Comunicación a líderes de proceso, boletín interno, correos de seguimiento.

```
Actúa como responsable de comunicaciones institucionales de una universidad colombiana.

El CMI Estratégico del corte [MES AÑO] muestra los siguientes resultados:

[Pega aquí el resumen de resultados de la línea o del global según el caso]

Genera los siguientes formatos de comunicación:

**A. MENSAJE PARA WHATSAPP / TEAMS** (máx. 3 párrafos cortos)
Tono cercano pero profesional. Usa emojis con moderación (máx. 3).
Para comunicar el estado del CMI a los líderes de proceso.

**B. ASUNTO Y CUERPO DE CORREO ELECTRÓNICO**
- Asunto: [máx. 60 caracteres, llamativo y claro]
- Cuerpo: 150-200 palabras. Incluye: contexto, resultados clave,
  reconocimiento a equipos con buen desempeño, y llamado a la acción
  para quienes tienen indicadores en alerta/riesgo.

**C. FRASE PARA CARTELERA O PANTALLA DIGITAL** (máx. 20 palabras)
Inspiradora, que resuma el período de forma positiva
sin ocultar los retos.

**D. RESUMEN PARA INFORME DE GESTIÓN** (3 viñetas)
Cada viñeta: máx. 25 palabras. Listo para copiar en un informe mensual.
```

---

## 10. Generación de Objetivos del Próximo Período

> **Uso:** Planeación del siguiente ciclo basada en el desempeño actual.

```
Actúa como experto en planeación estratégica y gestión por resultados
en instituciones de educación superior colombianas.

Con base en los resultados del CMI Estratégico, corte [MES AÑO]:

Línea: [NOMBRE]
Indicadores con bajo desempeño: [lista]
Indicadores con excelente desempeño: [lista]
Contexto institucional: [agrega aquí cualquier información relevante:
cambios de rector, nuevas directrices del MEN, restricciones presupuestales, etc.]

Propón los siguientes elementos para el próximo período de seguimiento:

**A. AJUSTE DE METAS**
Para los indicadores que superaron ampliamente la meta: ¿debería subir la meta?
¿En cuánto? Argumenta brevemente.
Para los indicadores en riesgo: ¿es realista mantener la meta o debe revisarse?

**B. NUEVOS INDICADORES SUGERIDOS** (opcional, si aplica)
¿Hay aspectos estratégicos de esta línea que no están siendo medidos
y deberían estarlo? Propón máximo 2 indicadores nuevos con:
- Nombre del indicador
- Fórmula de cálculo sugerida
- Meta inicial sugerida
- Frecuencia de medición

**C. OBJETIVOS OPERATIVOS PARA EL SIGUIENTE CORTE**
Lista 3 objetivos SMART (Específicos, Medibles, Alcanzables, Relevantes, con Tiempo)
que contribuyan directamente a mejorar los indicadores con menor cumplimiento.

**D. RIESGOS A MONITOREAR**
¿Qué factores externos o internos podrían afectar el desempeño de esta línea
en el próximo período? Menciona 3 con nivel de probabilidad (Alto/Medio/Bajo).
```

---

## ⚙️ Instrucciones de Uso Avanzado

### Combinación de prompts

Para análisis más ricos, puedes encadenar prompts:

1. Ejecuta primero el **Prompt 3** (análisis por línea)
2. Pasa el resultado como contexto al **Prompt 8** (recomendaciones)
3. Usa ambos resultados para alimentar el **Prompt 7** (narrativa para junta)

### Personalización de tono

Agrega al final de cualquier prompt una de estas instrucciones según el destinatario:

| Audiencia | Instrucción adicional |
|-----------|----------------------|
| Rector / Junta Directiva | `Tono: formal ejecutivo. Máximo tecnicismo moderado.` |
| Líderes de proceso | `Tono: directo y orientado a la acción. Usa ejemplos concretos.` |
| Comunidad universitaria | `Tono: cercano e inspirador. Evita jerga técnica.` |
| Entes externos (MEN, etc.) | `Tono: técnico-normativo. Referencia a indicadores de calidad.` |

### Variables de contexto recomendadas

Incluye siempre en tus prompts:

```
Contexto adicional:
- Nombre de la institución: Politécnica Grancolombiana (POLI)
- Tipo de institución: Institución Universitaria de carácter privado
- País: Colombia
- Marco normativo: Ley 30 de 1992, lineamientos CNA
- Documento rector: Plan de Desarrollo Institucional (PDI) vigente
- Período del PDI: [AÑOS]
```

---

*Documento generado para uso interno del Sistema de Indicadores · Gerencia de Planeación y Gestión Institucional*
*Actualizar con los datos del período correspondiente antes de ejecutar cada prompt.*
