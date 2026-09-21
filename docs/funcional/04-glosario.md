# Glosario

- **Indicador**: variable que la institución sigue con una meta y un valor
  ejecutado periódico. Se le calcula **cumplimiento** y se le asigna un
  color de semáforo.
- **Métrica**: dato de seguimiento que **no** se compara contra una meta.
  Existe en dos formas distintas dentro del sistema:
  - En **Plan de Mejoramiento**, es una categoría formal y separada (pestaña
    "Métricas"): viene de su propia fuente de datos, no tiene semáforo, y en
    su lugar recibe una **tendencia** (Creciente/Decreciente/Estable) según
    cómo varió año a año. Puede tener **subindicadores** (desgloses, por
    ejemplo "Presencial" y "Virtual" dentro de la misma métrica).
  - En **CMI por Procesos** e **Informe por Procesos** también hay ítems de
    seguimiento sin meta real, pero el sistema **no los distingue
    formalmente** como "métrica": hoy se muestran igual que un dato que
    simplemente no se ha reportado (en gris, "Sin dato"). Es un pendiente
    identificado, no una funcionalidad terminada — ver
    [gaps y riesgos](../tecnico/09-gaps-y-riesgos.md) (G-19, agregado tras
    revisión con el equipo el 2026-09-20).
- **Cumplimiento**: qué porcentaje de la meta se alcanzó en un periodo
  (aplica solo a indicadores, no a métricas).
- **Semaforización / semáforo**: clasificación visual del cumplimiento en
  colores (rojo=Peligro, naranja=Alerta, verde=Cumplimiento,
  azul=Sobrecumplimiento).
- **CMI (Cuadro de Mando Integral)**: forma de organizar los indicadores
  por líneas estratégicas y objetivos institucionales.
- **OM (Oportunidad de Mejora)**: acción correctiva que se abre cuando un
  indicador no cumple su meta; se registra, se sigue y se cierra dentro del
  sistema.
- **Plan de Mejoramiento**: conjunto de indicadores y métricas que se
  reportan periódicamente en el marco de la acreditación institucional
  (CNA).
- **CNA**: Consejo Nacional de Acreditación — entidad ante la cual se
  reporta el Plan de Mejoramiento.
- **PDI**: Plan de Desarrollo Institucional.
- **Línea estratégica / Objetivo estratégico**: nivel de agrupación
  jerárquica de los indicadores dentro del CMI (Macro → Meso → Micro).
- **Pipeline de datos**: el proceso (fuera del sistema web) que junta
  varias fuentes de información y produce el archivo consolidado que el
  sistema web lee. Hoy se ejecuta manualmente, no en automático.
- **Excel consolidado**: el archivo (`Resultados Consolidados.xlsx`) que
  contiene todos los indicadores procesados; es la fuente real de los
  datos que ves en el dashboard.
- **Rol**: nivel de acceso de un usuario. En SGING hay cuatro: Procesos,
  Administrador, Calidad y Desempeño. Procesos ve cinco de las siete
  pantallas y no edita; los otros tres ven todo y pueden editar
  Oportunidades de Mejora.
