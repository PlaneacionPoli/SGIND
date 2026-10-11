# Módulos del sistema

## Módulos visibles en el menú

| Módulo | Qué muestra |
|---|---|
| **Resumen General** | Vista panorámica: cuántos indicadores están en cada color de semáforo, tendencia general, y un resumen narrativo automático del periodo. |
| **CMI Estratégico** | El Cuadro de Mando Integral a nivel institucional: cómo va cada línea estratégica y objetivo. |
| **CMI por Procesos** | Lo mismo, pero organizado por proceso (ej. Admisiones, Bienestar, etc.), con opción de exportar a Excel. |
| **Informe por Procesos** | Un informe más detallado por proceso, con pestañas de resumen, indicadores, calidad, auditoría y propuestas. |
| **Plan de Mejoramiento** | Seguimiento a los indicadores y métricas del plan de mejoramiento institucional (el que se reporta a la CNA — Consejo Nacional de Acreditación), con sus metas 2026-2030 y su histórico de cumplimiento. |
| **Seguimiento Operativo** | Control del cumplimiento de la **periodicidad de reporte** de cada indicador: por corte (año y mes) muestra cuántos están reportados, pendientes o sin reporte, el cumplimiento por proceso y las alertas de reportes vencidos y por vencer, con exportación a Excel. Muestra la evolución del cumplimiento por corte (con clic para saltar a un corte), un mapa de calor proceso × corte, el avance por frecuencia y los procesos con más pendientes; los filtros quedan en la dirección de la página para poder compartirla. Incluye la sección **Alertas por correo**, que prepara borradores de correo para Outlook (no envía nada) con el consolidado de indicadores que cada proceso debe reportar; mensaje, destinatarios y plazos son parametrizables. No evalúa el valor ni el semáforo del indicador. |
| **Gestión de Oportunidades de Mejora (OM)** | Único módulo donde se **crea, edita y cierra** información directamente en el sistema (no solo se consulta). Solo los roles de Calidad y Desempeño pueden editar; el resto solo puede consultar. |

## Módulos que existen pero no aparecen en el menú

Estos dos módulos están completos y funcionando con datos reales, pero
**no tienen ningún botón o enlace visible** en la aplicación — solo se
puede llegar a ellos si alguien escribe la dirección exacta en el
navegador. Es una funcionalidad terminada que hoy nadie puede descubrir por
sí solo:

- **PDI / Acreditación**: indicadores del Plan de Desarrollo Institucional
  y su relación con acreditación.
- **Diagnóstico**: un panel técnico de auto-chequeo (verifica que la
  conexión con los datos y los distintos módulos estén funcionando) — está
  pensado para soporte técnico, no para un usuario de negocio.

## Quién puede editar qué

Solo el módulo de **Gestión de Oportunidades de Mejora** permite crear o
modificar datos, y solo pueden hacerlo los usuarios con rol
**Administrador**, **Calidad** o **Desempeño**.

### Cómo se usa Gestión OM

1. Abre en el corte más reciente con datos (hoy, septiembre de 2026); cambia el año y el mes si lo necesitas y, si quieres, un proceso, un subproceso o una
   búsqueda por Id, nombre u OM. El enlace de la página conserva esos filtros.
2. Los cuatro indicadores de arriba responden «¿cuánto falta?»: **Sin OM**,
   **En gestión**, **Cerradas** y la **Cobertura** (indicadores en riesgo con
   una OM activa). El gráfico de barras muestra por proceso cuántos tienen y
   cuántos no tienen OM; un clic en una barra filtra la tabla.
3. La tabla abre en **Pendientes de OM**. Cada fila muestra el resultado
   frente a la meta y, si no hay OM, el botón **Registrar OM**. Se abre un
   panel lateral con el contexto del indicador (meta, ejecución e historial de
   los últimos periodos). Para una OM de Kawak el número es obligatorio.
4. Con una OM registrada, el menú «⋯» de la fila permite editar, cerrar o (solo
   Administrador) eliminar, siempre con confirmación. Una OM cerrada puede
   reabrirse editando su registro.

## Quién ve qué

- **Procesos** (el rol por defecto): ve cinco pantallas — Resumen General,
  CMI Estratégico, CMI por Procesos, Informe por Procesos y Plan de
  Mejoramiento. **No** ve Seguimiento Operativo ni Gestión OM: no aparecen
  en su menú y, si intenta entrar por la dirección, el sistema lo devuelve
  al menú.
- **Administrador, Calidad y Desempeño**: ven las siete pantallas y pueden
  editar Oportunidades de Mejora.
