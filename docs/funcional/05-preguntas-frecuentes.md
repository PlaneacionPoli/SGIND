# Preguntas frecuentes

**¿Por qué veo un color distinto para el mismo indicador en dos pantallas
distintas?**
Ya no debería pasar (corregido el 2026-09-20) — todas las pantallas
calculan el color desde el mismo lugar. Si lo ves, repórtalo como un caso
nuevo. Ver [03-como-se-calculan-los-indicadores.md](03-como-se-calculan-los-indicadores.md).

**¿Los datos se actualizan solos?**
No. Hay un proceso de preparación de datos que corre por fuera del sistema
web y hoy lo ejecuta un operador manualmente. Cada pantalla de indicadores
muestra al final un aviso con la fecha real de la última actualización, con
alerta visual si pasan más de 35 días sin refrescar.

**¿Puedo editar un indicador directamente desde el dashboard?**
No. Los indicadores se calculan a partir del archivo consolidado. Lo único
que se puede crear/editar/cerrar dentro de la aplicación web son las
Oportunidades de Mejora, y solo con rol Calidad o Desempeño.

**¿Dónde están el PDI/Acreditación y el panel de Diagnóstico?**
PDI/Acreditación se retiró del sistema (decisión de negocio, 2026-09-20).
Diagnóstico sigue existiendo pero es una herramienta interna de soporte
técnico, deliberadamente sin enlace en el menú — no está pensada para
usuarios de negocio.

**¿Cualquier usuario puede ver todos los módulos?**
No. Quien tiene rol **Procesos** (el rol por defecto) ve solo Resumen
General, CMI Estratégico, CMI por Procesos, Informe por Procesos y Plan de
Mejoramiento. Seguimiento Operativo y Gestión OM son para los roles
Administrador, Calidad y Desempeño, que además son los únicos que pueden
**editar** en Gestión de Oportunidades de Mejora. El rol Administrador se
asigna a una lista de correos definida por quien administra el sistema.

**¿Qué tan confiables son las cifras de "pruebas pasadas" o "cobertura de
tests" que aparecen en documentos anteriores del proyecto?**
Ya se verificaron con el entorno correcto (2026-09-20): 113 pruebas pasan,
34 fallan por causas conocidas y documentadas (mayoría requiere una base de
datos PostgreSQL local que no está disponible en este entorno de
auditoría), 16 se omiten. Cifras de documentos anteriores a esa fecha no
son confiables por sí solas.
