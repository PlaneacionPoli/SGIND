# Cómo se calculan los indicadores y su color de semáforo

## Importante: "indicador" y "métrica" no son lo mismo

Esta guía explica cómo se calcula un **indicador**: algo que se compara
contra una meta y recibe un color de semáforo. No todo lo que ves en el
sistema es un indicador con meta — hay ítems de seguimiento sin meta (lo
que llamamos **métrica**) en más de un lugar, y el sistema los trata de
forma distinta según dónde estén:

- En **Plan de Mejoramiento**, "Métrica" es una categoría propia, con su
  pestaña separada: no tiene semáforo, en su lugar recibe una
  **tendencia** (Creciente/Decreciente/Estable) — ver el final de esta
  página.
- En **CMI por Procesos** e **Informe por Procesos** también hay ítems sin
  meta real, pero ahí el sistema **no los distingue de un dato faltante**:
  se muestran igual, en gris con la etiqueta "Sin dato". Si ves un "Sin
  dato" en esas pantallas, puede significar dos cosas distintas — que nadie
  reportó el valor todavía, o que ese ítem nunca tuvo una meta que cumplir
  — y hoy no hay forma de saber cuál de las dos es, desde la pantalla.

## De dónde vienen los datos

Los datos que ves en el dashboard **no se generan dentro de la aplicación
web**. Vienen de un archivo consolidado que un proceso separado (fuera del
sistema web, ejecutado manualmente por un operador) construye a partir de
varias fuentes (el sistema Kawak y catálogos institucionales). El sistema
web solo **lee ese archivo ya construido**, lo complementa con información
de catálogo (a qué línea estratégica y objetivo pertenece cada indicador) y
lo muestra.

**Esto significa que si nadie ejecuta ese proceso de preparación de datos,
los indicadores que ves quedan congelados en su última actualización — sin
que la aplicación te avise de que están desactualizados.**

## Cómo se calcula el cumplimiento

Para cada indicador, el cumplimiento se calcula dividiendo lo ejecutado
entre la meta (`Ejecución / Meta`), ajustando el sentido del indicador (si
es "cuanto más alto mejor" o al revés). Ese resultado se convierte en una
categoría:

| Color | Nombre | Significado (régimen general) |
|---|---|---|
| 🔴 Rojo | Peligro | Menos del 80% de la meta |
| 🟠 Naranja | Alerta | Desde 80% hasta 99,9...% — el 100% exacto **ya no** cuenta como Alerta |
| 🟢 Verde | Cumplimiento | Desde 100% hasta 104,9...% |
| 🔵 Azul | Sobrecumplimiento | Desde 105% en adelante |
| ⚪ Gris | Sin dato | No hay información suficiente para calcularlo |

Es decir: los cortes (80%, 100%, 105%) siempre "pertenecen" a la categoría
de arriba, nunca a la de abajo. Un indicador con exactamente 100.0% de
cumplimiento es **Cumplimiento**, no Alerta.

Otros regímenes usan cortes distintos porque su naturaleza es diferente:

- **Plan Anual**: Peligro `<80%`, Alerta `80%–94,9%`, Cumplimiento
  `95%–100%` (aquí el 100% exacto sí cuenta como Cumplimiento, igual que el
  95% exacto), Sobrecumplimiento `>100%`.
- **Negativo-Porcentual** (indicadores donde "menos es mejor" en escala
  0-100): Cumplimiento `<102%`, Alerta `102%–110%`, Peligro `>110%`.

## Una inconsistencia conocida que debes tener en cuenta

Existen **varias formas de calcular este mismo color** repartidas en
distintas partes del sistema, y no todas usan exactamente los mismos
cortes. En la práctica esto significa que **el mismo indicador podría
mostrarse con un color ligeramente distinto según en qué pantalla lo
consultes** (por ejemplo, entre el Informe por Procesos y el CMI
Estratégico), especialmente para los indicadores con reglas especiales
(Plan Anual). Esto ya está identificado como algo a corregir — ver la
oportunidad de mejora M-06 en la documentación técnica — pero mientras se
corrige, si ves un color distinto para el mismo indicador en dos pantallas,
no asumas que es un error de captura de datos: puede ser esta
inconsistencia conocida del sistema.

## Tendencia (Plan de Mejoramiento)

En el módulo de Plan de Mejoramiento, además del color de cumplimiento, se
calcula una **tendencia histórica** comparando el promedio de variación año
a año:

- Más de +3% de variación promedio → **Creciente**
- Menos de -3% → **Decreciente**
- Entre -3% y +3% → **Estable**
- Menos de 2 años con dato → **Sin suficiente historia**
