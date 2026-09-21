# Módulos del sistema

## Módulos visibles en el menú

| Módulo | Qué muestra |
|---|---|
| **Resumen General** | Vista panorámica: cuántos indicadores están en cada color de semáforo, tendencia general, y un resumen narrativo automático del periodo. |
| **CMI Estratégico** | El Cuadro de Mando Integral a nivel institucional: cómo va cada línea estratégica y objetivo. |
| **CMI por Procesos** | Lo mismo, pero organizado por proceso (ej. Admisiones, Bienestar, etc.), con opción de exportar a Excel. |
| **Informe por Procesos** | Un informe más detallado por proceso, con pestañas de resumen, indicadores, calidad, auditoría y propuestas. |
| **Plan de Mejoramiento** | Seguimiento a los indicadores y métricas del plan de mejoramiento institucional (el que se reporta a la CNA — Consejo Nacional de Acreditación), con sus metas 2026-2030 y su histórico de cumplimiento. |
| **Seguimiento Operativo** | Vista de alertas y detalle de indicadores en riesgo, con exportación a Excel. |
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

## Quién ve qué

- **Procesos** (el rol por defecto): ve cinco pantallas — Resumen General,
  CMI Estratégico, CMI por Procesos, Informe por Procesos y Plan de
  Mejoramiento. **No** ve Seguimiento Operativo ni Gestión OM: no aparecen
  en su menú y, si intenta entrar por la dirección, el sistema lo devuelve
  al menú.
- **Administrador, Calidad y Desempeño**: ven las siete pantallas y pueden
  editar Oportunidades de Mejora.
