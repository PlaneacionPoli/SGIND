# ETL Pipeline Runner — Guía de Uso

Sistema de ejecución granular del pipeline ETL de Resultados Consolidados.

## Prerequisito

```bash
python scripts/consolidar_api.py   # genera Consolidado_API_Kawak.xlsx
```

## Opción A — Solo terminal (pipeline completo)

```bash
python scripts/pipeline_steps/00_run_all.py
```

## Opción B — Con UI visual

```bash
python scripts/pipeline_steps/runner_server.py
# Abre http://localhost:8765 automáticamente
```

## Ejecutar un paso específico

```bash
python scripts/pipeline_steps/06_construir_registros.py
python scripts/pipeline_steps/09_10_escribir_reparar.py --dry-run
```

## Ejecutar desde un paso específico

```bash
python scripts/pipeline_steps/00_run_all.py --desde 06
```

## Ver último reporte de auditoría

```bash
# Windows PowerShell
Get-Content (Get-ChildItem artifacts/audit/ | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
```

## Estado del pipeline

```bash
# Ver estado actual
type .pipeline_state\current_run.json
```
