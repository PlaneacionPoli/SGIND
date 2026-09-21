# Recomendaciones de gobierno de datos (marco DAMA-DMBOK)

> Basado en los hallazgos de la auditoría de código (`02-core-del-sistema.md`,
> `03-modelo-de-datos.md`, `09-gaps-y-riesgos.md`) y en las 11 áreas de
> conocimiento del DAMA-DMBOK. No son cambios de código propuestos — son
> recomendaciones de **gestión y gobierno** que preceden o acompañan las
> oportunidades técnicas ya listadas en `10-oportunidades-de-mejora.md`.

## Diagnóstico rápido: qué tan maduro es SGING v2 frente a DAMA-DMBOK

| Área DAMA | Estado actual (evidencia) | Nivel de madurez |
|---|---|---|
| Gobierno de datos | No hay dueño de dato formal, ni comité, ni política de cambios sobre reglas de negocio críticas (umbrales de semáforo) | Inicial |
| Arquitectura de datos | Dos silos desacoplados (Postgres/Excel) sin arquitectura de integración decidida (G-01) | Inicial |
| Modelado y diseño | Esquema Postgres con 3/7 tablas huérfanas; esquema Excel implícito, solo documentado en código de rename | Repetible |
| Almacenamiento y operaciones | Backups y versionado del Excel sí existen (`VersionManager`, rollback automático) — punto fuerte | Gestionado (parcial) |
| Seguridad de datos | RBAC consistente en el backend; hueco puntual en `dev-token` (G-04) | Gestionado (con hueco) |
| Integración e interoperabilidad (ETL) | Pipeline real y con gates de validación (bueno), pero manual, no automatizado, no integrado al backend (G-01) | Repetible |
| Documentos y contenido | Excel como sistema de registro sin política de retención — archivos residuales sin limpieza (G-… "- copia", "revvv.xlsx") | Inicial |
| Datos de referencia y maestros | Umbrales/reglas de semáforo duplicados en 8 lugares en vez de un maestro único (G-03) | Inicial |
| Data warehousing / BI | No hay modelo dimensional; el dashboard se construye directo sobre Excel plano | Inicial |
| Metadatos | No había catálogo de metadatos ni linaje antes de esta auditoría — el grafo en `docs/graph/` es el primer artefacto de este tipo | Inicial → recién iniciado |
| Calidad de datos | Hay validaciones reales en el pipeline (gates, AGENT5) pero sin marco formal de dimensiones de calidad ni SLA visible al usuario | Repetible |

## Recomendaciones por área

### 1. Gobierno de datos (Data Governance)

- **Nombrar un dueño de dato (data owner) por dominio**: Indicadores
  (dueño natural: quien opera `scripts/actualizar_consolidado.py`), OM
  (Calidad/Desempeño, ya tienen el rol de negocio), Plan de Mejoramiento
  (equipo de acreditación/CNA).
- **Formalizar el glosario de negocio** ya iniciado en
  `docs/funcional/04-glosario.md` como la fuente única de verdad de
  definiciones (Indicador vs. Métrica, Cumplimiento, Tendencia) — hoy vive
  solo en comentarios de código dispersos.
- **Política de cambio para reglas críticas**: cualquier cambio a
  `domain/categorization.py` o a los umbrales de `domain/constants.py`
  debería requerir aprobación del dueño de dato de Indicadores, no solo un
  PR técnico — porque afecta reportes institucionales (CNA, directivos).
- **Comité ligero de gobierno de datos** (no necesita ser pesado): una
  reunión mensual que revise gaps abiertos (`09-gaps-y-riesgos.md`) y decida
  prioridad, en vez de que queden solo como hallazgos de auditoría sin dueño.

### 2. Arquitectura de datos (Data Architecture)

- **Decidir formalmente la arquitectura del pipeline** (M-07 en
  `10-oportunidades-de-mejora.md`): ¿el pipeline de indicadores pasa a ser
  un job del backend, una función programada, o se mantiene como proceso
  externo pero con automatización real? Hoy es una decisión pendiente, no
  tomada — bloquea cualquier cutover futuro.
- **Documentar la arquitectura objetivo, no solo la actual**: esta
  auditoría documentó el estado real (`01-arquitectura.md`); falta el
  siguiente paso DAMA — un ADR que declare la arquitectura de datos
  *objetivo* (¿Excel se retira eventualmente? ¿Postgres se convierte en el
  único sistema de registro?).

### 3. Modelado y diseño de datos

- ✅ **Tablas huérfanas resueltas (G-10, Oleada 4):** `ai_configs` y
  `ai_prompts` se eliminaron (migración 003); `audit_log` se conserva como
  registro de auditoría de consulta manual. Pendiente: política de retención
  para `audit_log` (crece sin purga) y decidir el destino de `acciones`
  (tabla sin consumidor tras retirar el modelo `Accion`).
- **Publicar un diccionario de datos formal** por tabla Postgres y por hoja
  Excel relevante (columnas, tipo, obligatoriedad, regla de negocio
  asociada) — más allá de los `rename_map` dispersos en el código. Ya hay
  una base para esto en `03-modelo-de-datos.md`; el siguiente paso es
  mantenerlo versionado junto al esquema, no solo como documentación
  descriptiva.
- **Contratos de esquema Excel explícitos**: el pipeline ya valida entrada
  con "Gate 1" (`scripts/etl/validation_gate.py`) — formalizar esa
  validación como un contrato de datos versionado (ej. con `pandera` o
  JSON Schema) en vez de una validación ad hoc, para que un cambio de
  columna en el Excel fuente falle de forma explícita y temprana.

### 4. Integración de datos / ETL

- **Puntos fuertes a preservar** (no son gaps, son buenas prácticas ya
  presentes): idempotencia vía `marker_col`/`marker_value`, backup +
  rollback automático (`VersionManager`), gates de validación en 3 puntos
  del pipeline, notificaciones de fallo (`etl/notifications.py`).
- **Automatizar la orquestación** (hoy 100% manual, G-01): un scheduler
  real (cron del backend, GitHub Action, o similar) que ejecute
  `run_pipeline.py` con la cadencia que el negocio necesite, con el
  cron ya declarado en `config/settings.toml [schedule]` finalmente
  implementado.
- **Cerrar el ciclo de observabilidad**: `generar_reporte.py` ya calcula
  métricas de calidad del run (filas, IDs únicos, cumplimiento promedio,
  nulos) pero el resultado (`artifacts/reporte_*.json`) no llega a ningún
  dashboard visible — conectarlo a un panel de salud del pipeline (podría
  vivir en el módulo "Diagnóstico" ya existente, ver `02-modulos.md`).
- **Trazabilidad de linaje**: el grafo de datos publicado
  (`docs/graph/data-nodes.json`/`data-relationships.json`) es el primer
  artefacto de linaje del sistema — mantenerlo actualizado con cada cambio
  de fuente/destino de datos, en vez de dejarlo como una foto única de esta
  auditoría.

### 5. Datos de referencia y maestros (Reference & Master Data)

- **Este es el hallazgo más crítico desde la óptica DAMA**: los umbrales de
  semaforización (Peligro/Alerta/Cumplimiento/Sobrecumplimiento) son,
  conceptualmente, **datos de referencia maestros** — deberían vivir en un
  solo lugar versionado y ser consumidos por referencia, no
  reimplementados. Hoy están duplicados en 8 sitios (RN-03 a RN-07, RN-13
  a RN-15 en `05-reglas-de-negocio.md`) con valores divergentes entre sí.
  **Recomendación concreta**: mover los umbrales a una tabla de referencia
  (Postgres, ya que existe la infraestructura) versionada, con endpoint que
  la sirva, y que tanto backend como frontend consuman por API en vez de
  hardcodearla — esto resuelve a la vez el gap técnico (M-06) y el
  problema de gobierno (una sola fuente de verdad auditable).
- El catálogo de indicadores (`Catalogo Indicadores`, `Catalogo_Indicadores_Plan_Mejoramiento.xlsx`)
  también es dato maestro de facto — hoy vive en Excel con revisión manual
  fila por fila (`build_catalogo_indicadores.py`, "borrador heurístico" sin
  validar). Un catálogo de indicadores institucional debería tener el mismo
  nivel de gobierno que cualquier tabla maestra: dueño, proceso de
  aprobación de cambios, historial de versiones.

### 6. Calidad de datos (Data Quality)

- **Adoptar formalmente las dimensiones DAMA de calidad** para medir el
  pipeline, en vez de validaciones puntuales dispersas:
  - *Completitud*: % de indicadores con Meta/Ejecución reportada por
    periodo (relacionado con G-19 — hoy "Sin dato" mezcla dos causas
    distintas).
  - *Validez*: gates ya existentes (Gate 1/2/3) — formalizarlos como reglas
    de validez versionadas y con reporte histórico, no solo logs de
    ejecución.
  - *Unicidad*: la clave `UNIQUE(id_indicador, periodo, anio)` en
    `registros_om` es un buen ejemplo a replicar como constraint explícito
    también en las hojas Excel (hoy se controla en código, no en el dato).
  - *Oportunidad (timeliness)*: no hay SLA de frescura de datos — M-08 ya
    propone mostrar "última actualización", que es el primer paso mínimo
    de esta dimensión.
  - *Consistencia*: la duplicación de reglas de semáforo (sección 5) es
    exactamente un problema de consistencia de datos derivados.
- **Publicar un scorecard de calidad** (aprovechando que
  `generar_reporte.py` ya calcula varias de estas métricas) visible para
  el dueño de dato, no solo en un JSON de artefactos técnicos.

### 7. Metadatos (Metadata Management)

- El trabajo de esta auditoría (`docs/tecnico/`, `docs/graph/`) es en sí
  mismo el punto de partida de un catálogo de metadatos — la recomendación
  es institucionalizarlo: mantenerlo vivo (regenerarlo cuando el código
  cambie) en vez de que quede como una fotografía de 2026-09-20 que se
  desactualiza igual que `STATUS.md`.
- Metadatos mínimos a mantener por fuente de datos: dueño, frecuencia de
  actualización esperada, última actualización real, esquema, reglas de
  transformación aplicadas — hoy toda esta información existe pero está
  repartida entre comentarios de código, `config/settings.toml` y la
  memoria del operador que corre el pipeline.

### 8. Seguridad de datos

Ya cubierto en detalle en `07-seguridad.md` — desde la óptica DAMA, se
resume en: **falta una política formal de clasificación de datos**
(¿qué campos son sensibles — correos institucionales, identificación de
usuarios — y qué tratamiento requieren?) más allá del control de acceso
técnico ya implementado (RBAC).

### 9. Documentos y contenido

El uso de Excel como sistema de registro no es en sí un antipatrón (es una
decisión de arquitectura documentada en ADR-001), pero **sí le falta
disciplina de gestión documental**: archivos "- copia", "- copia - copia",
`revvv.xlsx` sin política de retención ni limpieza automatizada (más allá
de `.versiones/`, que sí está bien gestionado por `VersionManager`).
Recomendación: definir una política de retención explícita (cuántas copias
manuales se permiten, cuándo se archivan/eliminan) y aplicarla con
limpieza periódica.

### 10. Data warehousing / BI

A mediano plazo, evaluar si el modelo de "Excel como fuente + lectura
directa por el backend" sigue siendo sostenible frente a un modelo
dimensional real en Postgres (hechos de medición de indicador, dimensiones
de tiempo/proceso/línea estratégica) — esto resolvería de raíz varios gaps
(G-01, G-03, G-19) al mover el cálculo y la semaforización a una capa
gobernada centralmente, en vez de a lógica duplicada en Python/TypeScript.
No es una recomendación de corto plazo — es la evolución natural si la
institución decide invertir en madurez de datos más allá del cutover
actual.

## Priorización sugerida (integrando gobierno + lo técnico ya listado)

1. **Gobierno mínimo viable, ya**: nombrar dueños de dato, adoptar el
   glosario como fuente única, y decidir formalmente quién aprueba cambios
   a reglas de semáforo — esto no tiene costo de desarrollo, es una
   decisión organizacional que además hace más seguro ejecutar M-06.
2. **M-06 + maestro de reglas** (sección 5 de este documento): consolidar
   semaforización en una única fuente versionada — resuelve a la vez deuda
   técnica y gobierno de datos maestros.
3. **M-07 + automatización de orquestación** (sección 4): la decisión de
   arquitectura del pipeline es, de nuevo, tanto técnica como de gobierno —
   requiere que el dueño de dato de Indicadores participe en la decisión,
   no solo el equipo de desarrollo.
4. **Scorecard de calidad + metadatos vivos**: aprovechar lo que el
   pipeline ya calcula (`generar_reporte.py`) y el grafo ya construido,
   convirtiéndolos en artefactos mantenidos, no en resultados de una sola
   auditoría.
