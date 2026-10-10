# Propuesta: sistematizar la recolección del Anexo Estadístico (Autoevaluación)

Fuente analizada: `data/raw/Plan de mejoramiento/Anexo Estadístico Dcto. Autoevaluacion.xlsx`

## 1. Diagnóstico

**Qué es el archivo**: ~165 hojas (una por Tabla / Gráfico / Ilustración) + hoja `Índice Tablas`
(167 filas) que asigna a cada tabla *Factor, Característica, Fuente, Responsable de información y Enlace*.
La hoja oculta `Respaldo` es una copia anterior del índice.

| Hallazgo | Dato |
|---|---|
| Tablas/gráficos | 167 en el índice; ~20 factores/características |
| Responsables de información | ~40 personas distintas; 19 áreas fuente |
| Concentración | 5 responsables cubren 66 tablas (40 %): Diana Baquero 19, Lina Giraldo 14+3+1, Jenny Hernández 14, Raquel Breton 14+1 |
| Formulas | 800 (sumas de totales, % de selección/admisión); **0 vínculos externos** → todo es captura manual |
| Gráficos | 14 gráficos nativos + 1 imagen, dependen de rangos de las hojas |
| Periodicidad | Mezcla: semestral (matrícula, profesores 2019-2 → 2025-1), anual (finanzas, cierre 2024), por convocatoria (Minciencias 957) |

**Problemas detectados**
1. **Responsable ≠ quien carga**: columna "Responsable" (dueño del dato) y "Enlace" (quien lo entrega) son personas distintas; el flujo es por correo/Excel.
2. **Inconsistencias en el índice** que impiden automatizar: la misma área con distintos nombres (`Dirección de Bienestar` con 4 responsables; `Dirección de Docencia` con Lina Giraldo y Andrea Carmona; `Datos y Analítica` con 4 variantes; `Dirección de Graduados` / `Dir Graduados…`), 4 tablas sin fuente/responsable (225, 226, 227, 232), una fuente `****`, y 2 referencias rotas (Tabla 130 sin hoja; "Tabla 197" mal escrita en el índice).
3. **Sin control de versión ni estado**: no se sabe qué tabla está pendiente, entregada, validada. Las notas de actualización ("se actualiza con cierre 2024", "cambió metodología, se recalculan datos") viven en texto libre.
4. **Formato heterogéneo**: cada hoja tiene encabezados propios (año en columnas, semestre en columnas, listas largas tipo Tabla 123/215), lo que hace imposible consolidar sin una plantilla.
5. **Dependencia entre tablas**: totales y gráficos se rompen si alguien inserta una columna.

## 2. Principio de la propuesta

Pasar de *"un Excel que todos editan / envían"* a *"cada responsable carga SU tabla en una plantilla validada → el sistema consolida y regenera el anexo"*. El Excel final pasa a ser una **salida generada**, no el lugar de captura.

```
Catálogo de tablas  ──►  Plantilla por tabla  ──►  Carga (portal / Excel / conexión)
 (responsable,            (columnas, tipos,          │
  fuente, periodicidad)    validaciones)             ▼
                                              Validación automática
                                          (estructura, rangos, vs. periodo anterior)
                                                     │
                      Recordatorios / alertas ◄──────┤
                                                     ▼
                                       Revisión (enlace → responsable → Planeación)
                                                     │
                                                     ▼
                                   Repositorio histórico (tabla larga)
                                                     │
                                                     ▼
                       Generador del Anexo (xlsx + gráficos) y Tablero de avance
```

## 3. Componentes

### 3.1 Catálogo maestro de tablas (base de todo)
Convertir `Índice Tablas` en una tabla normalizada `anexo_tabla`:

`tabla_id, tipo (tabla|gráfico|ilustración), nombre, factor, característica, area_fuente_id, responsable_id, enlace_id, periodicidad (semestral|anual|convocatoria|única), periodo_corte, origen (sistema|manual), sistema_origen, observaciones_metodológicas, activa`

- Normalizar áreas y personas en catálogos (`area`, `persona`), eliminando las variantes de nombre.
- Resolver primero: tablas 225/226/227/232 sin dueño, 130 sin hoja, "Tabla 197" mal referenciada.
- Un script de migración puede poblar esto directamente desde el índice (ya es estructurado).

### 3.2 Clasificar cada tabla por nivel de automatización
Es la decisión que más valor da. Propuesta de clasificación (a confirmar con cada área):

| Nivel | Criterio | Ejemplos (por área fuente) | Mecanismo |
|---|---|---|---|
| **A. Automático** | El dato ya sale de un sistema o dataset institucional | Matrícula, graduados, admisión (Datos y Analítica / DAC / SNIES-SPADIES), Talento Humano (nómina), indicadores del propio SGING | Consulta/ETL programado a la fuente → llena la tabla sin intervención; el responsable solo valida |
| **B. Semi-automático** | Existe un archivo recurrente con formato fijo | Finanzas (Tablas 61-77, Planeación Financiera), Investigación (convocatoria 957), Biblioteca (recursos, libros, revistas), Relaciones Internacionales | Plantilla Excel fija + carga por portal; el sistema lee, valida y consolida |
| **C. Manual con formulario** | Listas cualitativas o de baja frecuencia | Proyectos con aliados (T123), listados (T215, T157, T159, T172) | Formulario web / tabla editable con catálogos desplegables |

Los 19 de Planeación Financiera, los 14 de Docencia, Investigación y Relaciones Internacionales (≈ 60 tablas) son los primeros candidatos: pocos responsables, volumen alto.

### 3.2b Estructuras heterogéneas y tablas nuevas (diseño extensible)
Las tablas no comparten estructura (cruces modalidad × nivel × periodo, series por año o semestre, listados de proyectos, tablas con subtotales, etc.) y el número de tablas puede crecer. Por eso **no se programa una pantalla/plantilla por tabla**; cada tabla se describe como *datos* en una **definición de esquema** y un motor único la interpreta:

- `anexo_tabla_esquema` (JSON versionado por tabla): columnas con `nombre, tipo (texto|entero|decimal|porcentaje|fecha|catálogo), obligatoria, rol (dimensión|periodo|métrica)`, eje de periodos (columnas o filas; semestre/año), filas fijas vs. listado libre, **campos calculados** (fórmula declarativa: suma, razón) y reglas de validación.
- Tres **patrones de forma** cubren casi todo: (1) *matriz dimensión × periodo* (matrícula, profesores, finanzas), (2) *listado de registros* (proyectos con aliados, grupos, semilleros), (3) *indicador puntual/serie corta*. Una tabla nueva casi siempre es una instancia de uno de ellos → se da de alta sin desarrollo.
- **Alta de tabla nueva**: Planeación sube un Excel de ejemplo; el sistema **infiere** el esquema (encabezados, tipos, fórmulas existentes como calculadas), lo muestra para ajustar y lo publica. Se asigna responsable/enlace/periodicidad en el catálogo y queda disponible la plantilla, la carga, la validación y el tablero.
- **Almacenamiento genérico** (formato largo clave-valor por celda/registro + `esquema_version`), de modo que agregar o cambiar columnas no requiere migraciones de BD. Los cambios de estructura entre periodos quedan versionados y se advierte al comparar.
- **Salida fiel**: cada esquema guarda también el *layout* de presentación (posición, encabezados combinados, subtotales) para que el generador reproduzca la hoja tal como la usa hoy el anexo.
- Excepciones: tablas muy atípicas se marcan como *"manual con adjunto"* (se sube el bloque ya armado, se versiona y se controla estado/plazo) sin bloquear el resto del flujo.

Primer paso práctico: un script que recorra las ~165 hojas, detecte el patrón de cada una y genere los esquemas borrador; así se mide cuántas caen en cada patrón y cuántas son excepciones.

### 3.3 Plantillas y validación
- Una plantilla por tabla **generada automáticamente desde su esquema (3.2b)**, no diseñada a mano: columnas, tipos y periodos esperados, **con el periodo siguiente ya agregado** (el responsable solo completa lo nuevo).
- Se separan **datos** de **cálculos**: el responsable solo ingresa valores base; totales y porcentajes (`SUM`, `IFERROR(E/D)`) los calcula el sistema.
- Validaciones automáticas al cargar: columnas esperadas, tipos numéricos, periodos continuos, totales cuadran con sumandos, variación vs. periodo anterior > umbral (p. ej. ±30 %) marca "requiere justificación".
- Modelo de almacenamiento en formato largo: `tabla_id, esquema_version, periodo, dimensiones (JSON), métrica, valor, version, estado, cargado_por, fecha`. Evita 165+ esquemas físicos distintos y permite histórico y trazabilidad.
- Campo obligatorio de **nota metodológica** cuando cambia el cálculo (hoy aparece solo en texto libre en tablas 130, 165, 166, 201, 232).

### 3.4 Flujo y estados por tabla
`Pendiente → Cargada → En validación → Observada | Aprobada por responsable → Aprobada por Planeación → Publicada`

- Roles: **Enlace** (carga), **Responsable** (aprueba), **Planeación** (consolida/publica). Esto mapea las columnas existentes `Enlace` y `Responsable Información`.
- Cada responsable ve únicamente sus tablas (RBAC por área; SGING ya tiene matriz RBAC).

### 3.5 Recordatorios y seguimiento
- Calendario de corte (por periodicidad) y recordatorios automáticos T-7, T-2, vencido, con escalamiento al responsable y luego a Planeación.
- **Tablero de avance**: % de tablas por estado, por área y por factor; semáforo de atrasos. Es el principal ahorro operativo: hoy Planeación persigue ~40 personas manualmente.
- Esto es reutilizable con el módulo de alertas de seguimiento que ya se está construyendo en SGING (`alertas_service`, calendario), en lugar de crear uno aparte.

### 3.6 Generación del Anexo
- Script que arma el `.xlsx` final desde el repositorio (una hoja por tabla con el mismo formato actual + índice actualizado), regenerando los 14 gráficos.
- Salidas adicionales: versión PDF/Word de las tablas y un *diff* contra la versión anterior (qué cambió, quién y por qué), útil para la narrativa de la autoevaluación.
- Compatible con la regla ya acordada del proyecto: si cambia la data, regenerar narrativa + JSON + PDF + documento de revisión.

## 4. Implementación en SGING (propuesta técnica mínima)

| Pieza | Dónde encaja |
|---|---|
| Tablas `anexo_tabla`, `anexo_carga`, `anexo_dato`, `anexo_estado` | nueva migración en `database/migrations/` |
| Servicio de ingesta/validación | `backend/app/services/anexo_service.py` (patrón similar a `excel_reader.py` / `etl_pipeline.py`) |
| Endpoints (listar mis tablas, descargar plantilla, cargar, aprobar) | `backend/app/api/v1/endpoints/anexo.py` |
| Pantalla "Mis tablas" + tablero de avance | `frontend/src/app/(dashboard)/anexo-estadistico/` |
| Recordatorios | reutilizar módulo de alertas/calendario |
| Generador del Anexo | `backend/app/services/anexo_export_service.py` (openpyxl) |

## 5. Plan por fases

| Fase | Contenido | Resultado |
|---|---|---|
| **0 (1 semana)** | Limpiar índice; catálogos de áreas/personas; resolver 6 tablas con inconsistencias; confirmar nivel A/B/C por tabla con cada responsable; script de detección de patrones y esquemas borrador | Catálogo maestro confiable + mapa de estructuras |
| **1 (2–3 sem.)** | Cargar catálogo en BD + tablero de avance + recordatorios (sin cambiar aún cómo se captura) | Visibilidad y control de plazos inmediatos |
| **2 (3–4 sem.)** | Plantillas + carga y validación para los 5 responsables más cargados (≈ 66 tablas) y repositorio histórico | Mayor reducción de trabajo manual |
| **3 (3–4 sem.)** | Conexión automática de tablas nivel A (matrícula, graduados, admisión, talento humano) | Sin intervención en las tablas de datos institucionales |
| **4 (2 sem.)** | Generador del Anexo + diff + resto de áreas | Anexo producido por el sistema |

Una versión rápida (**Fase 0 + 1**) se puede lograr sin desarrollo grande y ya resuelve el problema principal (saber quién debe qué y cuándo).

## 6. Decisiones que necesitan validar contigo

1. ¿Alcance inicial: **todas** las tablas o solo el ciclo de autoevaluación vigente (corte 2025-1 / cierre 2024)?
2. ¿Los responsables cargarán en el portal SGING o se mantiene el Excel por correo en una primera etapa (Fase 1)?
3. ¿Qué sistemas fuente tienen acceso técnico (SNIES, Datos y Analítica, Talento Humano, Finanzas)? Define cuántas tablas pasan a nivel A.
4. Confirmar dueño de las tablas 225/226/227/232 y la figura de Planeación como aprobador final.

## 7. Riesgos
- **Resistencia al cambio** de ~40 responsables → empezar por tablero y recordatorios, no por exigir un portal nuevo.
- **Cambios de metodología** entre periodos rompen series → campo obligatorio de nota metodológica y versionado.
- **Datos personales** en listados (investigadores, proyectos): aplicar RBAC y no versionar cargas en git (ver AGENTS.md: no commitear dumps de Excel con datos personales).
