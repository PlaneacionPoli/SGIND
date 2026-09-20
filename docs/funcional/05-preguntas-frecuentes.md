# Preguntas frecuentes

**¿Por qué veo un color distinto para el mismo indicador en dos pantallas
distintas?**
Es una inconsistencia conocida del sistema (varias partes calculan el color
de forma ligeramente distinta). No es un error de captura de datos. Ver
[03-como-se-calculan-los-indicadores.md](03-como-se-calculan-los-indicadores.md).

**¿Los datos se actualizan solos?**
No. Hay un proceso de preparación de datos que corre por fuera del sistema
web y hoy lo ejecuta un operador manualmente. Si no se ha ejecutado
recientemente, los indicadores que ves pueden estar desactualizados sin
ninguna advertencia visible en pantalla.

**¿Puedo editar un indicador directamente desde el dashboard?**
No. Los indicadores se calculan a partir del archivo consolidado. Lo único
que se puede crear/editar/cerrar dentro de la aplicación web son las
Oportunidades de Mejora, y solo con rol Calidad o Desempeño.

**¿Dónde están el PDI/Acreditación y el panel de Diagnóstico? No los veo en
el menú.**
Existen y funcionan, pero no tienen un enlace visible todavía. Se puede
acceder escribiendo la dirección directamente. Es un pendiente de
conectarlos al menú (o decidir formalmente no mostrarlos).

**¿Cualquier usuario puede ver todos los módulos?**
Sí, cualquier persona que haya iniciado sesión puede consultar todos los
módulos, sin importar su rol. La única restricción por rol es poder
**editar** en Gestión de Oportunidades de Mejora.

**¿Qué tan confiables son las cifras de "pruebas pasadas" o "cobertura de
tests" que aparecen en documentos anteriores del proyecto?**
No se pueden confirmar hoy — el entorno técnico para correr esas pruebas
tiene un problema de compatibilidad de versiones que impide ejecutarlas. Es
un pendiente técnico, no significa que el sistema no funcione, solo que esa
cifra específica no está verificada actualmente.
