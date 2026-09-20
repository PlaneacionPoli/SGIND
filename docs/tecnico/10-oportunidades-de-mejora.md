# Oportunidades de mejora priorizadas

| ID | Oportunidad | Problema actual | Beneficio | Esfuerzo | Riesgo | Prioridad |
|---|---|---|---|---|---|---|
| M-01 | ✅ **Hecho (Oleada 0, 2026-09-20)** — Arreglar el entorno de pruebas del backend | Era un falso negativo: `.venv312` ya existía y funcionaba, solo faltaba usarlo. Ver `08-testing.md` | Permite verificar cualquier otra afirmación de calidad | — | — | — |
| M-02 | ✅ **Hecho (Oleada 0)** — Nuevo flag `ENABLE_DEV_AUTH` (default `false`), reemplaza la comparación `environment=="production"` | Cerraba riesgo de auto-escalada de privilegios en staging/QA (G-04) | Cierra un hueco de seguridad real | — | — | — |
| M-03 | ✅ **Hecho (Oleada 0)** — Corregidas ambas rutas rotas en `PRIMARY_EXCEL_FILES` (`Consolidado_API_Kawak.xlsx` y `CMI.xlsx`) | Rutas declaradas no existían (G-05) | Evita fallos silenciosos | — | — | — |
| M-04 | ✅ **Hecho (Oleada 0)** — Corregidos 14 errores de `ruff check` + 13 archivos sin formatear de `ruff format --check` | Lint no estaba realmente limpio (más errores de los reportados inicialmente) | Alinea el código con lo que documenta STATUS.md; CI de lint pasa limpio | — | — | — |
| M-05 | Actualizar `STATUS.md`/`ROADMAP.md` para reflejar la estructura real (`backend/`/`frontend/` en raíz, no `sgind-v2/`) y las cifras de tests reales | Documentación con rutas inexistentes (G-08) | Evita que cualquier persona nueva se pierda siguiendo la doc | Bajo | Ninguno | **Quick win** |
| M-06 | ✅ **Hecho (Oleada 2, 2026-09-20)** — Consolidada la semaforización: 6 implementaciones divergentes en backend y 3 copias de paleta en frontend ahora delegan a `categorizar_cumplimiento`/`COLOR_CATEGORIA` y `design-tokens.ts::SEMAFORO` respectivamente. Paleta oficial confirmada con negocio: Peligro `#D32F2F`, Alerta `#f59e0b`, Cumplimiento `#22c55e`, Sobrecumplimiento `#3b82f6`. Nuevo parámetro `regimen` en `categorizar_cumplimiento` para que Retos/Proyectos usen Plan Anual (95/100) incondicionalmente por tipo | Riesgo crítico de inconsistencia visual entre pantallas (G-03) | Elimina la causa raíz de una clase entera de bugs de UI | — | — | — |
| M-07 | Diseñar la arquitectura de integración del pipeline ETL con el backend (job programado, función serverless, o automatización explícita del cron ya declarado en `config/settings.toml`) | Pipeline 100% manual y desacoplado (G-01) | Elimina el riesgo de datos congelados sin aviso | Alto (requiere decisión de infraestructura, no solo código) | Alto si no se hace | **Cambio arquitectónico — máxima prioridad de negocio** |
| M-08 | ✅ **Hecho (Oleada 1)** — Pie de página `DataFreshnessFooter` en cada pantalla de datos del dashboard (Resumen General, CMI Estratégico, CMI Procesos, Informe por Procesos, Plan de Mejoramiento, Seguimiento Operativo), con fecha real de `Resultados Consolidados.xlsx` vía `/dashboard/excel-files` y alerta visual si pasan >35 días. No se muestra en Gestión OM (Postgres, no depende de este archivo) ni en Diagnóstico (herramienta interna) | Hoy no hay forma de que el usuario final sepa si los datos están desactualizados (consecuencia de G-01) | Mitiga el riesgo de G-01 mientras se implementa M-07 | — | — | — |
| M-09 | Conectar o retirar formalmente `PDI/Acreditación` y `Diagnóstico` del menú de navegación | Funcionalidad completa pero invisible (G-16) | Aprovecha trabajo ya hecho o evita mantenerlo sin uso | Bajo | Bajo | **Quick win** |
| M-10 | Eliminar o corregir `IndicatorsTable.tsx`/`YoYTable.tsx` (código muerto con bug de escala) | G-07 | Evita reintroducir un bug si se reconectan sin revisión | Bajo | Bajo | **Quick win** |
| M-11 | Decidir el destino de `audit_log`, `ai_configs`, `ai_prompts` (implementar su consumo o retirarlas del esquema) | Tablas huérfanas (G-10) | Reduce superficie de mantenimiento de BD sin propósito | Bajo-medio | Bajo | **Refactorización** |
| M-12 | Confirmar con el equipo el estado de `scripts/backup_sqlite.py`, `panel_monitoreo.py`, `ingesta_plantillas.py`, `scripts/analytics/*` antes de tocarlos | Estado incierto (no verificable solo con código) | Evita romper algo en uso fuera del repo | Bajo | Medio si se asume incorrectamente que están muertos | **Antes de cualquier limpieza de scripts/** |
| M-13 | ✅ **Hecho (Oleada 0)** — `.env.staging` sacado del índice de git y agregado a `.gitignore` | Contradicción documental, criticidad baja hoy (G-15) | Cierra un hábito de riesgo antes de que contenga un valor real | — | — | — |
| M-14 | Definir convención de cuándo usar Plotly vs. Recharts, o migrar a una sola librería | G-14 | Reduce peso de bundle y superficie de mantenimiento | Medio | Bajo | **Evolución futura** |
| M-15 | Corregir el texto fijo de estado de auth en Diagnóstico para que refleje el modo real en tiempo de ejecución | G-17 | Evita que el panel de diagnóstico mienta sobre su propio propósito | Bajo | Bajo | **Quick win** |

## Orden recomendado de ejecución

1. **Quick wins de bajo riesgo** (M-01 a M-05, M-08 a M-10, M-13, M-15) —
   se pueden hacer en paralelo, no requieren decisión de negocio.
2. **M-07** (arquitectura del pipeline ETL) — es la única que bloquea la
   viabilidad de cualquier cutover futuro; requiere decisión de
   infraestructura antes de escribir código.
3. **M-06** (consolidación de semaforización) — mejora estructural que se
   beneficia de tener M-01/M-04 resueltos primero (para poder escribir
   tests de regresión antes de tocar las 4 implementaciones divergentes).
4. **M-11, M-12, M-14** — refactorizaciones/evolución sin urgencia, mejor
   después de estabilizar lo anterior.
