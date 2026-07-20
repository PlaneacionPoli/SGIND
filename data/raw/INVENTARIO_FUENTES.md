# Inventario de Fuentes de Datos — Subdirectorios `data/raw/`

> Generado: 2026-05-09 | Responsable: equipo SGIND

## Estructura general

```
data/raw/
├── Auditoria/              ← Informes de auditoría interna y externa
├── Fuentes Consolidadas/   ← Datos Kawak consolidados (ver README propio)
├── Kawak/                  ← Extracciones brutas de la API Kawak
├── Monitoreo/              ← Monitoreo de información por procesos
├── Plan de accion/         ← Planes de acción (PA_*.xlsx)
├── Propuesta Indicadores/  ← Indicadores propuestos (no oficiales)
├── Retos/                  ← Plan de retos institucionales
└── API/                    ← Configuración/respuestas de la API
```

---

## Auditoria/

| Archivo | Tipo | Descripción | Uso en sistema |
|---|---|---|---|
| `auditoria_resultado.csv` | CSV | Resultados de auditoría en formato tabular | Lectura directa por scripts de análisis |
| `auditoria_resultado.xlsx` | Excel | Ídem en formato Excel | Respaldo editable |
| `Informe Auditoria Externa Icontec 2025.pdf` | PDF | Informe oficial de auditoría externa Icontec 2025 (ISO 9001/14001/45001/21001) | Solo referencia — no procesado automáticamente |
| `INFORME AUDITORIA INTERNA FINAL 9001-14001-45001-21001.pdf` | PDF | Informe de auditoría interna integrada | Solo referencia — no procesado automáticamente |

**Estado**: Activo. Los CSV/xlsx son procesados; los PDF son fuentes documentales de referencia.

**Próxima acción**: Verificar si `auditoria_resultado.csv` y `.xlsx` están sincronizados (misma versión).

---

## Monitoreo/

| Archivo | Tipo | Descripción | Uso en sistema |
|---|---|---|---|
| `Monitoreo_Informacion_Procesos 2025.xlsx` | Excel | Monitoreo del estado de información por proceso, corte 2025 | No integrado al pipeline principal actualmente |

**Estado**: Presente pero **sin integración ETL**. Contiene datos de seguimiento de calidad de información por proceso.

**Próxima acción**: Evaluar si incorporar al dashboard de monitoreo (pág. Gestión OM o nueva sección). Responsable: equipo SGIND, S2-2026.

---

## Retos/

| Archivo | Tipo | Descripción | Uso en sistema |
|---|---|---|---|
| `Plan de retos.xlsx` | Excel | Plan de retos institucionales con metas y responsables | No integrado al pipeline principal actualmente |

**Estado**: Presente pero **sin integración ETL**. Corresponde a iniciativas estratégicas de mediano plazo.

**Próxima acción**: Definir si los retos se monitorizan como indicadores de resultado o en sección separada. Responsable: equipo SGIND, S2-2026.

---

## Kawak/ y API/

Contienen extracciones brutas y configuración de la API Kawak.
El flujo oficial es: `API Kawak → scripts/consolidar_api.py → Fuentes Consolidadas/Consolidado_API_Kawak.xlsx`.

---

## Plan de accion/

Archivos `PA_*.xlsx` con planes de acción por proceso. Contrato de datos definido en `config/data_contracts.yaml` (clave: `plan_accion`).

---

## Reglas de gobierno

1. **Solo archivos en `Fuentes Consolidadas/`** son fuente válida para el ETL principal.
2. **Archivos PDF** en `Auditoria/` son solo documentales — no procesar programáticamente.
3. **Archivos sin integración ETL** (`Monitoreo/`, `Retos/`) deben tener decisión explícita antes de S2-2026.
4. **Archivos `_REV`** o con sufijo de revisión manual no deben usarse en producción (ver `Fuentes Consolidadas/README.md`).
