# Fuentes Consolidadas — Kawak API

## Archivos presentes

| Archivo | Estado | Descripción |
|---|---|---|
| `Consolidado_API_Kawak.xlsx` | ✅ Activo — fuente oficial | Extracción directa de la API Kawak. Contiene indicadores con sus metas y ejecuciones en el formato original del sistema Kawak. Es insumo para el script `scripts/consolidar_api.py`. |
| `Consolidado_API_Kawak_REV.xlsx` | ⚠️ Revisión manual — NO usar como fuente ETL | Versión con correcciones manuales sobre `Consolidado_API_Kawak.xlsx`. Creada para revisar discrepancias en IDs y nombres de indicadores detectadas en abril 2026. **No está integrada al pipeline ETL.** Conservar como referencia de auditoría hasta que las correcciones sean validadas e incorporadas a la fuente oficial. |
| `Indicadores Kawak.xlsx` | ✅ Activo — catálogo de referencia | Catálogo maestro de indicadores registrados en Kawak. Usado para validación cruzada de IDs. |

## Decisión sobre `Consolidado_API_Kawak_REV.xlsx`

- **No eliminar aún**: contiene anotaciones de discrepancias que no han sido resueltas en la fuente oficial.
- **Próxima acción**: al cerrar el ciclo de limpieza de IDs (previsto S1-2026), incorporar correcciones al pipeline y eliminar este archivo.
- **Responsable**: equipo SGIND.

## Flujo de datos

```
API Kawak → scripts/consolidar_api.py → Consolidado_API_Kawak.xlsx
                                        ↓
                              services/data_loader.py (lectura)
                                        ↓
                              Dashboard Streamlit
```

> **Regla**: Solo `Consolidado_API_Kawak.xlsx` es fuente válida para el ETL.
> `_REV.xlsx` es solo archivo de trabajo/auditoría.
