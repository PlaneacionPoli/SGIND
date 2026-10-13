# Revisión de indicadores «Tipo 2 / Desglose Variables» con formato %

Contexto: el ETL guarda como Meta/Ejecución las **variables** del indicador (p. ej. «planeadas» y
«ejecutadas») y no el resultado % del API. Con unidad «%» eso se ve como «1.107%» (Id 69). Se
corrigieron 8 indicadores leyendo meta y resultado % directo del API (`ids_desglose_var_directo` en
`config/settings.toml`: 69, 88, 91, 235, 282, 344, 397, 426). Esta nota clasifica los 32 restantes
que difieren del API (fecha de revisión: 2026-10-13, datos hasta jun-2026).

## A. Error de configuración (resultado equivocado) — recomendado: API directo
| Id | Indicador | Hallazgo |
|---|---|---|
| 86 | Reporte e investigación | La hoja Variables mapea **dos** símbolos (IR y NR) a «Ejecución» y ninguno a «Meta»: el ETL muestra Meta 100 / Ejecución 1–5 (cumplimiento 3 %, «Peligro») cuando el API reporta 100 % de resultado y meta 100 %. |

## B. Conteos con unidad «%» (cumplimiento coherente con el API, pero la unidad confunde)
Meta = conteo planeado, Ejecución = conteo ejecutado; el cociente coincide con el resultado % del API,
pero se muestran como «%» y se ignora la meta % del API (p. ej. 484: API meta 90 %, ETL compara contra 100 %).
Ids: 85, 89, 90, 95, 122, 172, 197, 232, 240, 241, 251, 300, 301, 318, 431, 452, 453, 455, 484, 513,
515, 518, 530, 531, 556.
Opciones: (1) API directo (meta y resultado en %), o (2) solo cambiar la unidad a «ENT».

## C. Revisados sin hallazgo
| Id | Motivo |
|---|---|
| 115, 117 | Meta 80 y resultado coinciden con el API; la diferencia son cortes sin reportar (0). |
| 245, 252 | Las variables ya son tasas %; meta y ejecución son comparables con el API. |
| 451 | Ejecución 65,4 % contra meta 50 % = resultado 130,8 % del API. Correcto. |

## D. Problema del dato fuente (no es del ETL)
| Id | Hallazgo |
|---|---|
| 231 | El API reporta resultado 7.277 % (7.933 asistentes contra 109 esperados): error de captura en la fuente. |
| 516 | Resultado 315 % (300 asistentes contra 95 objetivo): revisar la meta/población objetivo en la fuente. |

## Decisión aplicada (2026-10-13)
- **A:** solo el Id 86 se lee directo del API (`ids_desglose_var_directo`).
- **B:** los 25 conteos **conservan «%»** (decisión de negocio): no se cambia su unidad ni su lectura.
- **C y D:** sin cambios en el ETL; D queda como hallazgo para los responsables del dato fuente.
