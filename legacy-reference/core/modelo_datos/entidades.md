# Entidades y Relaciones — SGIND

## Diagrama Entidad-Relación (ER)

```
[Indicador] --(N:1)--> [Meta]
     |                 |
     |                 v
     |             [Objetivo]
     |                 |
     |                 v
     |             [Linea]
     |
     +--(N:1)--> [Proceso]
     +--(N:1)--> [Subproceso]
     +--(N:1)--> [Area]
```

## Descripción de Entidades

- **Indicador**: Entidad central, identificada por `ID` (llave global). Puede tener atributos como nombre, sentido, meta, ejecución, etc.
- **Meta**: Meta asociada al indicador, puede cambiar por año.
- **Objetivo**: Objetivo estratégico al que contribuye el indicador.
- **Linea**: Línea estratégica superior.
- **Proceso/Subproceso/Area**: Dimensiones operativas, pueden variar según el indicador.

## Relaciones Clave
- Todas las entidades se relacionan a través del `ID` del indicador.
- No es necesario que todas las fuentes tengan todas las columnas, solo el `ID`.
- Los joins y consultas deben realizarse siempre a través del `ID`.

---

> **Nota:** El modelo puede expandirse según nuevas necesidades (por ejemplo, agregar Periodo, Responsable, etc.).
