# Guía de Configuración - SGIND

## Archivo Principal: config/settings.toml

Este archivo contiene toda la configuración del sistema. **NO editar código Python** para cambios de configuración.

---

## Secciones de Configuración

### 1. [project] - Información del Proyecto

```toml
[project]
name = "Indicadores_Oportunidad_Mejora"
```

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `name` | string | Nombre del proyecto | `"Indicadores_Oportunidad_Mejora"` |

---

### 2. [business] - Reglas de Negocio

```toml
[business]
"año_cierre" = 2025
ids_plan_anual = ["373","390","414","415","416","417","418","420","469","470","471"]
ids_tope_100 = ["208","218"]
ids_siempre_validos = []
```

| Campo | Tipo | Descripción | Default |
|-------|------|-------------|---------|
| `año_cierre` | int | Año actual de cierre de indicadores | `2025` |
| `ids_plan_anual` | list[str] | IDs de indicadores del plan anual | `["373","390",...]` |
| `ids_tope_100` | list[str] | IDs con tope de 100% | `["208","218"]` |
| `ids_siempre_validos` | list[str] | IDs que siempre son válidos | `[]` |

**Nota:** Editar `año_cierre` cada año. Los demás campos son estables.

---

### 3. [paths] - Rutas del Sistema

```toml
[paths]
base_dir = "."
data_raw = "data/raw"
data_output = "data/output"
```

| Campo | Tipo | Descripción | Default |
|-------|------|-------------|---------|
| `base_dir` | string | Directorio raíz | `"."` |
| `data_raw` | string | Datos crudos | `"data/raw"` |
| `data_output` | string | Datos de salida | `"data/output"` |
| `input_fuente_consolidado` | string | Fuente principal de entrada | `"data/raw/Resultados_Consolidados_Fuente.xlsx"` |
| `kawak_dir` | string | Directorio de archivos Kawak | `"data/raw/Kawak"` |
| `api_dir` | string | Directorio de archivos API | `"data/raw/API"` |
| `fuentes_consolidadas_dir` | string | Fuentes consolidadas | `"data/raw/Fuentes Consolidadas"` |
| `out_resultados_consolidados` | string | Archivo de salida principal | `"data/output/Resultados Consolidados.xlsx"` |
| `out_seguimiento_reporte` | string | Reporte de seguimiento | `"data/output/Seguimiento_Reporte.xlsx"` |
| `out_kawak_catalogo` | string | Catálogo Kawak generado | `"data/raw/Fuentes Consolidadas/Indicadores Kawak.xlsx"` |
| `out_api_consolidado` | string | Consolidado API generado | `"data/raw/Fuentes Consolidadas/Consolidado_API_Kawak.xlsx"` |

---

### 4. [pipeline] - Configuración del Pipeline

```toml
[pipeline]
steps = ["consolidar_api", "actualizar_consolidado", "generar_reporte"]
```

| Campo | Tipo | Descripción | Default |
|-------|------|-------------|---------|
| `steps` | list[str] | Orden de ejecución del pipeline | `["consolidar_api", "actualizar_consolidado", "generar_reporte"]` |

---

### 5. [checks] - Validaciones

```toml
[checks]
strict_data_contracts = true
required_outputs = [...]
resultados_consolidados_required_sheets = [...]
seguimiento_reporte_required_sheets = [...]
```

| Campo | Tipo | Descripción | Default |
|-------|------|-------------|---------|
| `strict_data_contracts` | bool | Validaciones estrictas | `true` |
| `required_outputs` | list[str] | Archivos requeridos post-ejecución | Ver settings.toml |
| `resultados_consolidados_required_sheets` | list[str] | Hojas requeridas en consolidados | Ver settings.toml |
| `seguimiento_reporte_required_sheets` | list[str] | Hojas requeridas en reportes | Ver settings.toml |

---

### 6. [agent] - Configuración del Agente IA

```toml
[agent]
model = "claude-opus-4-6"
max_tokens = 2048
max_log_chars = 12000
enable_hotfix = false
```

| Campo | Tipo | Descripción | Default |
|-------|------|-------------|---------|
| `model` | string | Modelo Claude a usar | `"claude-opus-4-6"` |
| `max_tokens` | int | Máximo tokens en respuesta | `2048` |
| `max_log_chars` | int | Máximo caracteres de logs | `12000` |
| `enable_hotfix` | bool | Habilitar hotfixes automáticos | `false` |

---

### 7. [schedule] - Programación Automática

```toml
[schedule]
cron = "0 6 5 * *"
branch = "main"
commit_paths = [...]
commit_message = "chore(data): actualizar consolidado automático [{date}]"
```

| Campo | Tipo | Descripción | Default |
|-------|------|-------------|---------|
| `cron` | string | Expresión cron (GitHub Actions) | `"0 6 5 * *"` |
| `branch` | string | Rama para commits | `"main"` |
| `commit_paths` | list[str] | Archivos a incluir en commit | Ver settings.toml |
| `commit_message` | string | Mensaje de commit | `"chore(data): ..."` |

---

## Cambios Comunes

### Cambiar Año de Cierre
```toml
[business]
"año_cierre" = 2026  # Cambiar de 2025 a 2026
```

### Agregar Indicador al Plan Anual
```toml
[business]
ids_plan_anual = ["373","390","414","415","416","417","418","420","469","470","471","NUEVO_ID"]
```

### Cambiar Rutas de Salida
```toml
[paths]
out_resultados_consolidados = "data/output/Resultados_Consolidados_2026.xlsx"
```

### Deshabilitar Validaciones Estrictas
```toml
[checks]
strict_data_contracts = false
```

---

## Variables de Entorno

Además de settings.toml, se pueden usar variables de entorno:

| Variable | Descripción |
|----------|-------------|
| `PYTHONPATH` | Ruta de búsqueda de módulos |
| `OPENCODE_CONFIG` | Ruta adicional de configuración |

---

## Notas Importantes

1. **NO editar código Python** para cambios de configuración
2. **Editar settings.toml** para cambios de negocio
3. **Reiniciar el pipeline** después de cambios
4. **Validar** con `python scripts/validar_config.py` si existe

---

**Última actualización:** 2026-06-03  
**Maintainer:** Equipo SGIND
