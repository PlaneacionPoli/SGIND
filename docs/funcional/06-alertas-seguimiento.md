# Alertas de Seguimiento Operativo (borradores para Outlook)

El módulo **no envía correos**. Prepara, para cada proceso, un **borrador** con la
tabla de indicadores que debe reportar en Kawak; la persona de Desempeño lo abre
en Outlook, lo revisa y lo envía. No requiere permisos del tenant de Microsoft.
Se administra en **Seguimiento Operativo → Alertas por correo** (Administrador,
Calidad y Desempeño).

## Qué contiene el borrador

Es un archivo `.eml` marcado como "no enviado": Outlook de escritorio lo abre
como un mensaje en edición, con asunto, destinatarios (Para), copia (CC) y el
cuerpo HTML. La tabla incluye **ID, nombre del indicador, subproceso y
frecuencia**. El subproceso sale del Catálogo de Indicadores; si un indicador no
lo tiene se muestra «—». Si el proceso no tiene destinatarios, el borrador se
crea igual y se completa el «Para» en Outlook.

## Plazos (fecha máxima de reporte)

Fecha máxima = último día del mes del corte + plazo del proceso. Equivale a ese
día del mes siguiente (plazo 15 = día 15). **Si cae en fin de semana o festivo
nacional, se corre al día hábil anterior** (calendario de Colombia, Ley Emiliani).
El plazo general es 15 (editable a 13).
El calendario de festivos se calcula por regla para cualquier año (verificado contra las listas
publicadas de 2026, 2027 y 2028) e incluye el festivo de la Virgen de Chiquinquirá creado por la
Ley 2578 de 2026 (9 de julio, trasladado al lunes: 13-jul-2026, 12-jul-2027, 10-jul-2028).

| Proceso | Plazo |
|---|---|
| Planeación Financiera, Contabilidad, Tesorería | 25 días |
| Planeación Estratégica, Gestión Ambiental | 20 días |
| Todos los demás | 15 días (plazo general; 13 si se cambia) |

Los plazos propios se editan por proceso en la sección 4 de la pantalla. Ejemplo
(corte junio 2026): plazo 15 → 15 de julio; plazo 20 → el 20 de julio es festivo, queda
el 17 de julio.

## Destinatarios

Los correos salen del directorio institucional `data/raw/Directorio/Correos.xlsx`
(hoja Destinatarios, cruce por proceso sin distinguir tildes). Lo que se edite en
la pantalla reemplaza al directorio de ese proceso; vaciar el campo y guardar
vuelve al directorio. Hoy no tienen correo: Bienestar Institucional y Operación de
nuevos negocios y CI. Ese archivo contiene datos personales: no versionarlo.

## Cuándo se preparan

- **Aviso de apertura:** los días 1 a 3 de cada mes, para **todos** los procesos,
  con los indicadores del corte recién cerrado (un solo borrador por proceso y corte).
- **Recordatorio:** desde *N* días antes de la fecha máxima de cada proceso
  (por defecto 5), según el plazo propio de ese proceso.
- Cada corte se prepara una sola vez por proceso y tipo. Los indicadores incluidos
  son los que corresponden al corte por su frecuencia y siguen sin reportar;
  se excluyen los «No aplica» y los dados de baja (Vigencia Hasta anterior al corte).

## Cómo se avisa

El programador deja los borradores en estado **listo**. Al entrar a Seguimiento
Operativo aparece un aviso «Hay N borradores listos para revisar y enviar» con el
botón *Descargar borradores (.eml)*, que baja un ZIP (una carpeta por corte y un
`LEEME.txt` con los procesos sin destinatarios) y los pasa a **descargado**.
También se pueden generar a demanda con *Generar borradores ahora*, o bajar el de
un solo proceso desde la vista previa.

## Mensaje

Asunto y cuerpo (HTML) editables para *Recordatorio* y *Apertura*. Variables:
`{proceso}`, `{corte}`, `{corte_mes}`, `{anio}`, `{fecha_limite}`,
`{dias_restantes}`, `{total}` y `{tabla_html}` (la tabla). Los valores
sustituidos se escapan; la plantilla HTML la redactan los roles autorizados.

## Requisitos del servidor

`ALERTAS_SCHEDULER_ENABLED=true` en **una sola** instancia del backend (ver
`backend/.env.example`). En una base ya desplegada hay que aplicar a mano
`database/migrations/005_alertas_seguimiento.sql` (idempotente; siembra los
plazos propios de la tabla anterior).

## Borradores directamente en Outlook (Auto_Correo)

Además de los `.eml`, SGING exporta el **listado para la automatización local Auto_Correo**
(`Documentos\Automatización\Auto_Correo`, script `generar_borradores_outlook_v2.py`), que crea los
borradores directamente en la carpeta *Borradores* del buzón `planeacionpoli@` por COM con
Outlook de escritorio. No requiere permisos del tenant; solo Windows, Outlook abierto y acceso
al buzón.

En *Alertas por correo → Generar borradores ahora*, el botón **Listado para Auto_Correo (Outlook)**
descarga `Listado_de_indicadores_AAAA-MM.xlsx` con:

- **Indicadores**: Id, Indicador, Proceso, Subproceso, Periodicidad, Estado y `FechaMaxima` de cada
  proceso (con su plazo propio y el día hábil). Solo los indicadores pendientes del corte.
- **Destinatarios**: Proceso y Correo (directorio `Correos.xlsx` + lo editado en pantalla).
- **Parametros**: `CORTE_TEXTO`, `CORTE_ASUNTO` y la fecha máxima más tardía.

El script ya lee `Indicadores` (Id, Indicador, Proceso, Periodicidad) y `Destinatarios` (Proceso,
Correo); las columnas adicionales se ignoran. Para usar la `FechaMaxima` por proceso (plazos de 20
y 25 días) hay que adaptar el script, que hoy usa una sola constante `FECHA_MAXIMA`.

## Fuente de los datos

El tracking sale de `data/raw/Kawak/<año>.xlsx` (indicadores activos, periodicidad y columnas
fechadas con resultado) y del consolidado de la API. El LMI **ya no se usa**. Se regenera con el paso
`generar_seguimiento` del pipeline.
