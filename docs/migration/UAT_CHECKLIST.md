# UAT Checklist — SGIND v2

**Fase:** 11 — Validación con Usuarios  
**Fecha inicio UAT:** ___________  
**Versión en Staging:** ___________  
**URL Staging:** ___________  
**Coordinador UAT:** ___________

---

## Instrucciones de Uso

- Marcar cada ítem con: `✅ Aprobado` | `❌ Falla` | `⚠️ Observación` | `⏭️ No aplica`
- Registrar cualquier falla o observación en `UAT_BUGS.md`
- Completar la columna **Validado por** en cada sección
- Se requieren mínimo **2 rondas de validación** antes de aprobar la fase

---

## Módulo 0 — Acceso y Autenticación

| # | Criterio | Estado | Validado por | Nota |
|---|----------|--------|--------------|------|
| 0.1 | Redirección automática a `/login` si no autenticado | | | |
| 0.2 | Botón "Iniciar sesión con Microsoft" visible | | | |
| 0.3 | Login con cuenta institucional `@poligran.edu.co` exitoso | | | |
| 0.4 | Nombre y rol del usuario visible en header después de login | | | |
| 0.5 | Sesión persiste al recargar la página | | | |
| 0.6 | Cierre de sesión regresa a `/login` | | | |
| 0.7 | Acceso denegado a rutas no autorizadas según rol | | | |

**Resultado Módulo 0:** ___________  
**Bugs registrados:** ___________

---

## Módulo 1 — Resumen General

**URL:** `/resumen-general`  
**Usuarios validadores:**  

| # | Criterio | Estado | Validado por | Nota |
|---|----------|--------|--------------|------|
| 1.1 | Página carga en < 5 segundos | | | |
| 1.2 | KPIs visibles: total indicadores, % cumplimiento, % alerta, % peligro | | | |
| 1.3 | Semáforo de colores correcto (verde/amarillo/rojo/azul) según umbrales | | | |
| 1.4 | Filtro por año cambia los datos correctamente | | | |
| 1.5 | Filtro por corte (semestral/cierre) cambia los datos | | | |
| 1.6 | Gráfico de tendencia muestra evolución histórica | | | |
| 1.7 | Tabla de indicadores con columnas: código, nombre, meta, ejecución, cumplimiento | | | |
| 1.8 | Tabla permite búsqueda / filtrado | | | |
| 1.9 | Botón "Descargar PDF" genera PDF con KPIs y colores correctos | | | |
| 1.10 | Los números coinciden con el sistema Streamlit legacy (±0.01%) | | | |
| 1.11 | Mensaje de error visible si la API falla (no pantalla en blanco) | | | |
| 1.12 | Skeleton de carga visible mientras se obtienen datos | | | |

**Resultado Módulo 1:** ___________  
**Bugs registrados:** ___________

---

## Módulo 2 — CMI Estratégico

**URL:** `/cmi-estrategico`  
**Usuarios validadores:**  

| # | Criterio | Estado | Validado por | Nota |
|---|----------|--------|--------------|------|
| 2.1 | Página carga correctamente | | | |
| 2.2 | Indicadores PDI agrupados por línea estratégica | | | |
| 2.3 | Indicadores PDI agrupados por objetivo estratégico | | | |
| 2.4 | Jerarquía visual Macro → Meso → Micro presente | | | |
| 2.5 | Filtro por año funciona | | | |
| 2.6 | Filtro por corte funciona | | | |
| 2.7 | Semaforización correcta por indicador | | | |
| 2.8 | Porcentajes de cumplimiento coinciden con Streamlit (±0.01%) | | | |
| 2.9 | Treemap / gráfico de distribución muestra proporciones correctas | | | |
| 2.10 | Benchmark y brechas calculados correctamente | | | |
| 2.11 | Tabla de indicadores completa con todos los campos | | | |

**Resultado Módulo 2:** ___________  
**Bugs registrados:** ___________

---

## Módulo 3 — CMI Procesos

**URL:** `/cmi-procesos`  
**Usuarios validadores:**  

| # | Criterio | Estado | Validado por | Nota |
|---|----------|--------|--------------|------|
| 3.1 | Página carga correctamente | | | |
| 3.2 | Indicadores agrupados por proceso | | | |
| 3.3 | Indicadores agrupados por subproceso | | | |
| 3.4 | Jerarquía visual Macro → Meso → Micro presente | | | |
| 3.5 | Filtro por año funciona | | | |
| 3.6 | Filtro por proceso filtra correctamente | | | |
| 3.7 | Semaforización correcta por indicador | | | |
| 3.8 | Porcentajes coinciden con Streamlit (±0.01%) | | | |
| 3.9 | Vista resumen por proceso muestra KPIs globales | | | |
| 3.10 | Botón "Descargar PDF" genera informe de proceso correcto | | | |

**Resultado Módulo 3:** ___________  
**Bugs registrados:** ___________

---

## Módulo 4 — Gestión OM (Oportunidades de Mejora)

**URL:** `/gestion-om`  
**Usuarios validadores:**  

### 4A — Lectura

| # | Criterio | Estado | Validado por | Nota |
|---|----------|--------|--------------|------|
| 4.1 | Lista de OMs visible con: código, descripción, proceso, estado, fecha | | | |
| 4.2 | Filtro por proceso funciona | | | |
| 4.3 | Filtro por estado (abierta/cerrada) funciona | | | |
| 4.4 | Filtro por año funciona | | | |
| 4.5 | Conteo de OMs abiertas vs. cerradas correcto | | | |

### 4B — Creación

| # | Criterio | Estado | Validado por | Nota |
|---|----------|--------|--------------|------|
| 4.6 | Botón "Nueva OM" abre formulario | | | |
| 4.7 | Formulario tiene todos los campos requeridos | | | |
| 4.8 | Validaciones de campos obligatorios (no guardar si vacíos) | | | |
| 4.9 | OM creada aparece en la lista inmediatamente | | | |
| 4.10 | Mensaje de confirmación al crear | | | |

### 4C — Edición

| # | Criterio | Estado | Validado por | Nota |
|---|----------|--------|--------------|------|
| 4.11 | Botón "Editar" abre formulario con datos pre-cargados | | | |
| 4.12 | Cambios guardados correctamente | | | |
| 4.13 | Mensaje de confirmación al editar | | | |

### 4D — Cierre

| # | Criterio | Estado | Validado por | Nota |
|---|----------|--------|--------------|------|
| 4.14 | Botón "Cerrar OM" cambia estado a "Cerrada" | | | |
| 4.15 | OM cerrada no puede volver a abrirse desde UI | | | |
| 4.16 | Fecha de cierre registrada correctamente | | | |

**Resultado Módulo 4:** ___________  
**Bugs registrados:** ___________

---

## Módulo 5 — Plan de Mejoramiento (CNA)

**URL:** `/plan-mejoramiento`  
**Usuarios validadores:**  

| # | Criterio | Estado | Validado por | Nota |
|---|----------|--------|--------------|------|
| 5.1 | Página carga correctamente | | | |
| 5.2 | KPIs generales visibles: total acciones, % cumplidas, % en riesgo | | | |
| 5.3 | Filtro por año funciona | | | |
| 5.4 | Filtro por corte funciona | | | |
| 5.5 | Filtro por factor CNA funciona | | | |
| 5.6 | Tabla de acciones CNA con columnas completas | | | |
| 5.7 | Gráficos de cumplimiento por factor | | | |
| 5.8 | Semaforización correcta por acción | | | |
| 5.9 | Datos numéricos coinciden con Streamlit (±0.01%) | | | |
| 5.10 | Estados de carga (skeleton) visibles | | | |

**Resultado Módulo 5:** ___________  
**Bugs registrados:** ___________

---

## Módulo 6 — Seguimiento Operativo

**URL:** `/seguimiento-operativo`  
**Usuarios validadores:**  

| # | Criterio | Estado | Validado por | Nota |
|---|----------|--------|--------------|------|
| 6.1 | Página carga correctamente | | | |
| 6.2 | Alertas de indicadores fuera de umbral visibles | | | |
| 6.3 | Filtros por año, mes y proceso funcionan | | | |
| 6.4 | Barras apiladas muestran distribución de estados | | | |
| 6.5 | Tabla de detalle con indicadores completa | | | |
| 6.6 | Botón "Exportar Excel" descarga archivo con datos correctos | | | |
| 6.7 | Datos numéricos coinciden con Streamlit (±0.01%) | | | |
| 6.8 | Mensaje de error apropiado si API no responde | | | |

**Resultado Módulo 6:** ___________  
**Bugs registrados:** ___________

---

## Módulo 7 — Informe por Procesos

**URL:** `/informe-procesos`  
**Usuarios validadores:**  

| # | Criterio | Estado | Validado por | Nota |
|---|----------|--------|--------------|------|
| 7.1 | Página carga correctamente | | | |
| 7.2 | 6 tabs visibles: Resumen, Indicadores, Calidad, Auditoría, Propuestas, IA | | | |
| 7.3 | Tab Resumen: KPIs del proceso seleccionado | | | |
| 7.4 | Tab Indicadores: listado completo con semáforo | | | |
| 7.5 | Tab Calidad: métricas de calidad por proceso | | | |
| 7.6 | Tab Auditoría: hallazgos y observaciones | | | |
| 7.7 | Tab Propuestas: acciones de mejora relacionadas | | | |
| 7.8 | Tab IA: análisis generado correctamente | | | |
| 7.9 | Filtro por proceso actualiza todas las tabs | | | |
| 7.10 | Botón "Descargar PDF" genera informe landscape correcto | | | |
| 7.11 | Datos numéricos coinciden con Streamlit (±0.01%) | | | |

**Resultado Módulo 7:** ___________  
**Bugs registrados:** ___________

---

## Módulo 8 — Diagnóstico del Sistema

**URL:** `/diagnostico`  
**Usuarios validadores:**  

| # | Criterio | Estado | Validado por | Nota |
|---|----------|--------|--------------|------|
| 8.1 | Página carga correctamente | | | |
| 8.2 | Panel de salud muestra estado de API | | | |
| 8.3 | Panel de salud muestra estado de datos | | | |
| 8.4 | Panel de salud muestra estado de módulos | | | |
| 8.5 | Indicadores en verde cuando todo está OK | | | |

**Resultado Módulo 8:** ___________  
**Bugs registrados:** ___________

---

## Checklist Transversal — UX/Funcionalidad

| # | Criterio | Estado | Nota |
|---|----------|--------|------|
| T.1 | Navegación lateral funciona en todas las páginas | | |
| T.2 | Breadcrumbs / título de página correctos en cada módulo | | |
| T.3 | Responsividad aceptable en pantalla 1280×720 (mínimo) | | |
| T.4 | Ninguna página muestra pantalla en blanco sin mensaje | | |
| T.5 | Tiempos de carga < 8 segundos en todas las páginas | | |
| T.6 | Colores semáforo consistentes en todos los módulos | | |
| T.7 | Tipografía y espaciados uniformes | | |
| T.8 | Sin errores en consola del navegador que afecten funcionalidad | | |
| T.9 | Modo sin datos (sin filtro que devuelva resultados) muestra EmptyState | | |
| T.10 | Toast/mensajes de éxito/error visibles en acciones CRUD | | |

---

## Resumen de Rondas

### Ronda 1

| Fecha | Participantes | Módulos probados | Bugs bloqueantes | Resultado |
|-------|--------------|-----------------|-----------------|-----------|
| | | | | |

### Ronda 2

| Fecha | Participantes | Módulos probados | Bugs bloqueantes | Resultado |
|-------|--------------|-----------------|-----------------|-----------|
| | | | | |

---

## Criterio de Aprobación Fase 11

- [ ] **Cero bugs bloqueantes** abiertos
- [ ] **Todas las secciones** con resultado "Aprobado"
- [ ] **Paridad numérica** validada con script `uat_verify.py`
- [ ] **Mínimo 2 rondas** de validación completadas
- [ ] **Documento de aceptación** (`ACCEPTANCE_DOCUMENT.md`) firmado

**Estado Fase 11:** ⏳ En progreso  
**Fecha objetivo aprobación:** ___________
