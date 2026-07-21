# Modelo de Datos SGIND

Esta sección documenta el **modelo entidad-relación (ER)** y la arquitectura de datos centralizada para el sistema de indicadores institucionales (SGIND).

## Objetivo
- Garantizar que todas las fuentes y cálculos se realicen a partir de un modelo relacional robusto, usando el **ID** como llave global.
- Permitir joins, consultas y cálculos sin depender de la presencia de columnas específicas en cada fuente.
- Centralizar la lógica de negocio y las reglas de cálculo en un solo módulo reutilizable.

## Estructura
- `entidades.md`: Diagrama y descripción de entidades y relaciones.
- `calculos.md`: Lógica centralizada de KPIs y reglas de negocio.
- `modelo.py`: Clases y funciones para manipulación y consulta del modelo de datos.

## Uso
- Todos los scripts, dashboards y pipelines deben usar este modelo para obtener información relacional y realizar cálculos.
- El ID es la única llave obligatoria en todas las fuentes.

---

> **Actualizado:** 21/04/2026
