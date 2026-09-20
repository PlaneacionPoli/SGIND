# ¿Qué es SGING?

SGING es el sistema web donde la institución consulta el desempeño de sus
**indicadores estratégicos**: qué tan bien va cada indicador frente a su
meta, cómo evoluciona en el tiempo, y qué acciones de mejora hay abiertas
cuando algo no va bien.

## ¿Para quién es?

- **Directivos y analistas de planeación**: consultan el estado general de
  los indicadores, el Cuadro de Mando Integral (CMI) y los informes por
  proceso.
- **Responsables de calidad y desempeño**: además de consultar, pueden
  crear, editar y cerrar "Oportunidades de Mejora" (acciones correctivas
  frente a un indicador que no cumple su meta).
- **Equipo de procesos**: consulta el seguimiento operativo y el plan de
  mejoramiento de su área.

## ¿Qué hace hoy, en la práctica?

El sistema muestra siete módulos de consulta (más dos adicionales,
terminados pero sin acceso visible desde el menú — ver
[02-modulos.md](02-modulos.md)):

1. Resumen General
2. CMI Estratégico
3. CMI por Procesos
4. Informe por Procesos
5. Plan de Mejoramiento
6. Seguimiento Operativo
7. Gestión de Oportunidades de Mejora (OM)

Todos estos módulos muestran datos que vienen de un archivo consolidado que
se prepara **por fuera del sistema web**, con un proceso separado que un
operador ejecuta manualmente cuando hay datos nuevos que cargar. El sistema
web en sí mismo no genera esos datos, solo los lee y los presenta —
ver [03-como-se-calculan-los-indicadores.md](03-como-se-calculan-los-indicadores.md)
para el detalle de cómo se calcula el cumplimiento y el semáforo de color.

La única parte del sistema donde la información se guarda y edita
directamente dentro de la aplicación web (no en el archivo consolidado) es
**Gestión de Oportunidades de Mejora**.

## ¿Qué NO hace todavía?

- No actualiza los indicadores automáticamente por sí solo — depende de que
  alguien corra el proceso de preparación de datos periódicamente.
- No tiene un panel de administración de usuarios y roles dentro de la
  aplicación (los roles se asignan a nivel de configuración, no desde una
  pantalla de administración).
- Dos módulos completos (PDI/Acreditación y un panel de Diagnóstico técnico)
  ya funcionan pero no aparecen en el menú principal — solo son accesibles
  si alguien conoce la dirección web exacta.
