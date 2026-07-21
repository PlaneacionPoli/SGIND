# Inventario de Wrappers Legacy - FASE 2

Fecha: 2026-05-11
Objetivo: identificar puentes de compatibilidad en runtime productivo y clasificarlos para mantener, deprecar o eliminar.

## Criterio de clasificacion

- Mantener: requerido por imports activos en rutas productivas o por estabilidad de despliegue.
- Deprecar: mantiene compatibilidad hoy, pero existe ruta canonica clara y migrable.
- Eliminar: sin consumo productivo activo o reemplazo total verificado.

## Estado actual (runtime productivo)

### 1) config.py
- Rol: facade legacy hacia `core.config`.
- Estado tecnico: ya migrado a reexport controlado (sin wildcard import).
- Clasificacion: Mantener (corto plazo), Deprecar (mediano plazo).
- Motivo: existe consumo legacy en `streamlit_app/app.py` (`from config import inject_styles`) y patrones historicos de import plano.
- Siguiente accion: migrar import legacy de `streamlit_app/app.py` a ruta canonica y retirar facade en fase posterior.

### 2) streamlit_app/services/strategic_indicators.py
- Rol: facade legacy hacia `services.strategic_indicators`.
- Estado tecnico: ya migrado a reexport controlado (sin wildcard import).
- Clasificacion: Mantener (corto plazo), Deprecar (mediano plazo).
- Motivo: protege imports heredados durante la transicion a paquete canonico.
- Siguiente accion: registrar warning de deprecacion y medir consumo real antes de retirar.

### 3) core/semantica.py
- Rol: facade principal de compatibilidad para funciones ahora en `core/domain` y `core/presentation`.
- Consumo detectado: alto (pages, services, scripts y tests).
- Clasificacion: Mantener.
- Motivo: retirar hoy generaria regresion amplia; es puente contractual central.
- Siguiente accion: migracion incremental de imports a `core.domain`/`core.presentation` por modulo.

### 4) core/db_manager.py
- Rol: modulo de compatibilidad para persistencia OM, delegando a `core/db/*`.
- Consumo detectado: `streamlit_app/pages/gestion_om.py`, `streamlit_app/components/renderers.py`, scripts de inspeccion.
- Clasificacion: Mantener.
- Motivo: preserva contratos legacy de DB_PATH y wrappers requeridos por tests y UI OM.
- Siguiente accion: mover consumidores nuevos a `core.db` y encapsular wrappers restantes con plan de sunset.

### 5) streamlit_app/auth.py
- Rol: wrapper de compatibilidad para `auth_modules`.
- Consumo detectado: `streamlit_app/pages/auth_guard.py` y `streamlit_app/app.py` (via `from auth import ...` en contexto de app).
- Clasificacion: Mantener.
- Motivo: frontera de autenticacion estable; bajo costo de mantener.
- Siguiente accion: estandarizar imports a `streamlit_app.auth` y eliminar alias ambiguos de ruta relativa.

### 6) streamlit_app/dashboard_config.py
- Rol: wrapper de compatibilidad de dashboard modules.
- Consumo detectado: no se encontraron imports activos en runtime productivo con busqueda rapida.
- Clasificacion: Deprecar.
- Motivo: probable wrapper residual.
- Siguiente accion: confirmar via busqueda semantica + ejecucion smoke de rutas legacy; si no hay consumo, programar eliminacion.

### 7) streamlit_app/components/filters.py
- Rol: wrapper legacy hacia `render_filter_panel`.
- Consumo detectado: no se observan imports directos activos en pages productivas (se usa `ui_components.render_filters` en app legacy).
- Clasificacion: Deprecar.
- Motivo: coexisten rutas nuevas (`filter_panel`) y legacy (`ui_components`).
- Siguiente accion: converger `ui_components.render_filters` a `filter_panel` directo y retirar wrapper duplicado.

### 8) utils/niveles.py
- Rol: reexport temporal de constantes/categorizacion (marcado como DEPRECADO en codigo).
- Consumo detectado: bajo en runtime productivo directo.
- Clasificacion: Eliminar (condicionado).
- Motivo: ya existe fuente unica en `core.config` + `core.semantica`.
- Siguiente accion: verificar cero imports en rutas productivas y remover en lote de limpieza.

## Wrappers de paquete (canonicos, mantener)

Estos `__init__.py` reexportan API publica y son parte del contrato canonico, no deuda inmediata:
- `services/strategic_indicators/__init__.py`
- `services/cmi_filters/__init__.py`
- `services/data_validation/__init__.py`
- `core/db/__init__.py`

Clasificacion: Mantener.

## Riesgos de retiro prematuro

- Ruptura de imports en paginas monoliticas aun no migradas.
- Fallos en OM por dependencia de wrappers en `core.db_manager`.
- Regresiones en tests de compatibilidad.

## Secuencia recomendada (proxima iteracion)

1. Migrar consumidores productivos de `core.semantica` a `core.domain`/`core.presentation` por modulo.
2. Confirmar no-uso real de `streamlit_app/dashboard_config.py` y `streamlit_app/components/filters.py`.
3. Retirar `utils/niveles.py` cuando no existan referencias productivas.
4. Mantener `core/db_manager.py` hasta cerrar migracion de OM a `core.db`.

## Checkpoint de avance FASE 2

- Eliminados wildcard imports productivos criticos: completado.
- Inventario de wrappers legacy con clasificacion: completado.
- Proximo hito: migracion de consumidores a rutas canonicas y retiro controlado de wrappers deprecables.

## Actualizacion de continuidad (2026-05-11)

- Migracion incremental a rutas canonicas completada en capas productivas principales (`streamlit_app`, `services`, `core`, scripts activos y lote amplio de tests).
- Referencias residuales a `core.semantica` permitidas por compatibilidad:
	- `core/semantica.py`: fachada legacy (contrato temporal).
	- `tests/test_semantica.py`: suite dedicada a validar la fachada.
	- `scripts/_archived/tmp_debug/strategic_indicators_legacy_backup.py`: archivo archivado fuera de runtime productivo.
	- `utils/niveles.py`: menciones documentales y reexports deprecados (sin ruta productiva prioritaria).

### Criterio operativo vigente

- Todo desarrollo nuevo debe importar desde `core.domain` / `core.presentation`.
- `core.semantica` se mantiene solo como puente de compatibilidad hasta sunset formal.
