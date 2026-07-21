# Cálculos Centralizados — SGIND

## Principios
- Todos los cálculos de cumplimiento, KPIs y reglas de negocio deben implementarse aquí, usando el modelo de datos relacional.
- No se debe depender de columnas sueltas ni de la estructura de cada fuente individual.

## Ejemplo de Cálculo de Cumplimiento

- **Por indicador:**
  - Si sentido es ASCENDENTE: cumplimiento = ejecucion / meta
  - Si sentido es DESCENDENTE: cumplimiento = meta / ejecucion
  - Aplicar tope según tipo de indicador (1.0 o 1.3)
  - Multiplicar por 100 para porcentaje

- **Por línea estratégica:**
  - Promedio de cumplimiento de todos los indicadores de la línea (join por ID)

## KPIs y Agregaciones
- Cumplimiento global
- Cumplimiento por objetivo, meta, proceso, etc.
- Tendencias históricas (por año, usando ID y periodo)

## Ejemplo de función (pseudocódigo)

```python
# Obtener cumplimiento promedio por línea
join = indicadores.merge(lineas, on="ID")
solo_cierre = resultados[resultados["Mes"] == 12]
por_linea = join.groupby("Linea")["cumplimiento_pct"].mean()
```

---

> **Actualizado:** 21/04/2026
