# 📋 GOBERNANZA DE DOCUMENTACIÓN - SGIND

> **Fecha:** 22 de abril de 2026  
> **Versión:** 1.0  
> **Estado:** ✅ ACTIVA

---

## 🎯 PROPÓSITO

Este documento establece las políticas y procedimientos para la creación, mantenimiento y eliminación de documentación en el proyecto SGIND.

---

## 📏 PRINCIPIOS FUNDAMENTALES

### 1. Single Source of Truth (SSOT)
**Toda documentación reside en `/docs/`**  
- No existe documentación dispersa en otras carpetas
- El archivo `docs/README.md` es el índice oficial
- Código y configuración tienen sus propios comentarios

### 2. Principio KISS (Keep It Simple, Stupid)
- Cada documento tiene **un solo propósito**
- Sin duplicación de información
- Sin documentos que digan lo mismo de formas diferentes

### 3. Documentación Viva
- La documentación debe **mantenerse sincronizada** con el código
- Si el código cambia, la docs debe actualizarse
- Documentación obsoleta se **elimina**, no se archiva

### 4. Sin "Quizás Por Si Acaso"
- **No conservar documentos por si acaso sirvan**
- **No hacer copias de seguridad de documentación**
- Si no está alineado con el sistema actual → **eliminar**

---

## 📂 ESTRUCTURA DE CARPETAS

```
docs/
├── 00-ESTRATEGIA/        → Visión, diagnóstico, propuesta de valor
├── 00-FUNCIONAL/         → Documentación funcional del negocio
├── 01-ANALISIS/          → Análisis técnicos y de datos
├── 02-CALCULOS/          → Fórmulas y cálculos oficiales
├── 02-MODELO-DATOS/      → Esquemas de base de datos
├── 03-CONFIG/            → Configuraciones técnicas
├── 04-FASE1/             → Documentación FASE 1 (histórico)
├── 05-FASE2/            → Documentación FASE 2 (histórico)
├── 05-AUDITORIA/        → Auditorías técnicas completas
├── 06-FASE3/            → FASE 3: Testing & Validation ✅ ACTUAL
├── 07-INTERFAZ/         → Documentación de UI/UX
├── 08-PROBLEMAS-RESUELTOS/ → Problemas técnicos y soluciones
├── 09-DIAGNOSTICOS/     → Análisis de problemas identificados
├── 10-GUIAS-ESTANDARES/ → Guías de uso y estándares
├── 11-DEPLOYMENT/       → Guías de deployment y operación
└── README.md            → Índice centralizado (ESTE ARCHIVO)
```

---

## 🏷️ TAXONOMÍA DE DOCUMENTOS

### Por TIPO

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| **FUNCIONAL** | Procesos de negocio, flujos | `DOCUMENTACION_FUNCIONAL.md` |
| **TÉCNICO** | Arquitectura, lógica, código | `ARQUITECTURA_TECNICA_DETALLADA.md` |
| **INDICADOR** | Definiciones de métricas | `CUMPLIMIENTO-OFICIAL.md` |
| **OPERATIVO** | Manuales de uso, guías | `GUIA_INSTALACION_EJECUCION.md` |
| **AUDITORÍA** | Validaciones técnicas | `AUDITORIA_COMPLETA_SGIND.md` |
| **ANÁLISIS** | Estudios, diagnósticos | `ANALISIS_ARQUITECTONICO_SGIND.md` |

### Por ESTADO

| Estado | Significado |
|--------|-------------|
| 🟢 **VIGENTE** | Alineado con sistema actual, usado activamente |
| 🟡 **PARCIAL** | Requiere revisión o actualización |
| 🔴 **OBSOLETO** | No refleja el sistema actual, debe eliminarse |
| ⚫ **DUPLICADO** | Información redundant, debe consolidarse |

---

## 🚫 POLÍTICAS DE ELIMINACIÓN

### SE ELIMINA SI:
1. ❌ Documento que describe lógica que **ya no existe**
2. ❌ Documento **duplicado** de otro más completo
3. ❌ Borradores o notas que nunca se completaron
4. ❌ Documentación de **features eliminadas**
5. ❌ Versiones antiguas de documentos actualizados
6. ❌ Documentos marcados como "deprecated" por > 3 meses

### NO SE ELIMINA SI:
1. ✅ Documentación histórica de decisiones importantes
2. ✅ Auditorías que documentan el estado del sistema
3. ✅ Resolución de problemas que pueden recurir

---

## ✅ CHECKLIST DE PUBLICACIÓN

Antes de crear un nuevo documento, verificar:

- [ ] ¿El documento tiene **un solo propósito claro**?
- [ ] ¿La información no existe ya en otro documento?
- [ ] ¿El documento está alineado con el sistema **actual**?
- [ ] ¿Pertenece a una de las carpetas de `docs/`?
- [ ] ¿El documento es **necesario** o es "quizás por si acaso"?

---

## 📊 MATRIZ DE TRAZABILIDAD

| Documento Final | Fuente Original | Transformación | Estado |
|-----------------|------------------|----------------|--------|
| `docs/00-ESTRATEGIA/` | `01-ESTRATEGIA/` | MOVIDO | 🟢 VIGENTE |
| `docs/00-FUNCIONAL/` | `04-FUNCIONAL/` | MOVIDO | 🟢 VIGENTE |
| `docs/01-ANALISIS/` | `docs/01-ANALISIS/` | CONSOLIDADO | 🟢 VIGENTE |
| `docs/02-CALCULOS/` | `docs/02-CALCULOS/` | SIN CAMBIOS | 🟢 VIGENTE |
| `docs/03-CONFIG/` | `03-TECNICA/` + original | MOVIDO + FUSIONADO | 🟢 VIGENTE |
| `docs/05-AUDITORIA/` | `docs/05-AUDITORIA/` | SIN CAMBIOS | 🟢 VIGENTE |
| `docs/06-FASE3/` | `docs/06-FASE3/` | ACTUALIZADO | 🟢 VIGENTE |
| `docs/11-DEPLOYMENT/` | `05-OPERATIVO/` + original | MOVIDO + FUSIONADO | 🟢 VIGENTE |
| ~~`docs/12-ARCHIVOS/`~~ | FASE 1-2 old | ELIMINADO | 🔴 OBSOLETO |
| ~~`docs/exploratory/`~~ | temporal | ELIMINADO | 🔴 OBSOLETO |
| ~~`docs/modelo_datos/`~~ | redundant | ELIMINADO | 🔴 OBSOLETO |
| ~~`MASTER_INDEX.md`~~ | old index | ELIMINADO | 🔴 OBSOLETO |

---

## ⚠️ PROBLEMAS CRÍTICOS DETECTADOS

### 1. DOCUMENTACIÓN CONTRADICTORIA
**Estado:** No detectado ✅  
No hay documentos que contradigan el sistema actual.

### 2. FALTA DE DOCUMENTACIÓN EN PROCESOS CLAVE
**Estado:** ⚠️ PARCIAL  
- ✅ Categorización de cumplimiento: Documentada en `core/semantica.py` + tests
- ⚠️ Pipeline ETL: Parcialmente documentado en comentarios de código
- ⚠️ Dashboard pages: Solo comentarios básicos

### 3. CONOCIMIENTO TÁCITO
**Estado:** ⚠️ IDENTIFICADO  
Algunos conocimientos aún no documentados:
- Detalles de normalización de datos en `services/data_loader.py`
- Lógica específica de cada dashboard

### 4. INCONSISTENCIA EN DEFINICIONES
**Estado:** ✅ RESUELTO ✅  
- Problema #1 (Plan Anual con 373 IDs) resuelto y documentado
- Problema #2 (Casos especiales) resuelto y documentado
- Test ID fragility resuelto con fixtures dinámicos

---

## 📋 PLAN DE ACCIÓN

| Acción | Tipo | Prioridad | Impacto | Esfuerzo |
|--------|------|-----------|--------|----------|
| Documentar pipeline ETL en `services/data_loader.py` | Completar documentación | Alta | Alto | Medio |
| Agregar docstrings a dashboard pages | Completar documentación | Media | Medio | Bajo |
| Revisar `docs/03-CONFIG/` por duplicados | Limpieza | Baja | Bajo | Bajo |
| Consolidar guías de colores + gráficos | Consolidar | Media | Medio | Medio |

---

## 🔄 CICLO DE VIDA DOCUMENTACIÓN

```
NUEVO → REVISIÓN → VIGENTE → DEPRECADO → ELIMINADO
  ↑         ↓
  └─────────┴── (si requiere cambios)
```

### Revisado Semestralmente:
- **Enero** y **Julio** de cada año
- Verificar que cada documento en `docs/` sigue siendo vigente
- Eliminar documentos marcados como obsoletos

---

## 📞 RESPONSABLE

**Owner:** Equipo de desarrollo SGIND  
**Última revisión:** 22 de abril de 2026  
**Próxima revisión:** Julio 2026

---

**GitHub Copilot | SGIND Governance v1.0**
