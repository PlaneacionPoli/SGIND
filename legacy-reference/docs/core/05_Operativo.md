# 05 - OPERACIÓN Y DEPLOYMENT

**Documento:** 05_Operativo.md  
**Versión:** 1.0  
**Fecha:** 22 de abril de 2026  
**Status:** ✅ Consolidado MDV

---

## 1. Pipeline ETL

### 1.1 Flujo de Consolidación

```
scripts/consolidar_api.py (PRE-REQUISITO)
    │
    ▼
[Fuentes API + Kawak] → cargar_fuente_consolidada()
    │
    ▼
actualizar_consolidado.py (ORQUESTADOR)
    │
    ├──► 1. Cargar fuente consolidada (df_api)
    ├──► 2. Cargar catálogo completo
    ├──► 3. Cargar metadatos y catálogos auxiliares
    ├──► 4. Cargar config_patrones
    ├──► 5. Abrir workbook de salida
    ├──► 6. Leer hojas existentes (signos)
    ├──► 7. Purga de filas inválidas
    ├──► 8. Construir escalas históricas
    ├──► 9. Preparar fuentes para builders
    ├──► 10. Construir nuevos registros (HISTÓRICO, SEMESTRAL, CIERRES)
    ├──► 11. Escribir nuevas filas
    ├──► 12. Reparar valores vacíos
    ├──► 13. Deduplicar y reescribir fórmulas
    ├──► 14. Actualizar Catálogo Indicadores
    └──► 15. Guardar
```

### 1.2 Tiempos de Ejecución

| Fase | Duración | Descripción |
|------|----------|-------------|
| Total ETL | 45-50 seg | Pipeline completo |
| Pre-requisito | 5-10 seg | consolidar_api.py |
| Carga fuentes | 10-15 seg | API + Kawak |
| Construcción | 20-25 seg | Builders + escritura |

---

## 2. Deployment Streamlit Cloud

### 2.1 Configuración

**Archivo:** `render.yaml`

```yaml
services:
  - type: web
    name: sgind
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run streamlit_app/app.py
```

### 2.2 Variables de Entorno

| Variable | Descripción | Valor típico |
|----------|-------------|--------------|
| `STREAMLIT_SERVER_PORT` | Puerto del servidor | 8501 |
| `STREAMLIT_SERVER_HEADLESS` | Modo headless | true |

### 2.3 Requirements

```
streamlit>=1.28
pandas>=2.0
openpyxl>=3.1
plotly>=5.18
supabase>=2.0
```

---

## 3. GitHub Actions Workflows

### 3.1 Tests Workflow

```yaml
name: Tests
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ['3.10', '3.11']
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest --cov=. --cov-report=xml
```

### 3.2 Deploy Staging

```yaml
name: Deploy Staging
on:
  push:
    branches: [develop]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Render Deploy
        run: curl -X POST $RENDER_DEPLOY_HOOK_URL
      - name: Wait for propagation
        run: sleep 30
      - name: Health check
        run: curl -f $STAGING_URL/health
```

---

## 4. Configuración Local

### 4.1 Instalación

```bash
# 1. Clonar repositorio
git clone <repo-url>
cd Sistema_Indicadores_Poli

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar config.toml
# Editar año_cierre, rutas, etc.

# 5. Ejecutar aplicación
streamlit run streamlit_app/app.py
```

### 4.2 Estructura de Datos Esperada

```
data/
├── raw/
│   ├── Fuentes Consolidadas/
│   │   ├── Consolidado_API_Kawak.xlsx
│   │   └── Indicadores Kawak.xlsx
│   ├── Kawak/
│   │   └── Catalogo_2026.xlsx
│   ├── Indicadores por CMI.xlsx
│   ├── Ficha_Tecnica.xlsx
│   ├── acciones_mejora.xlsx
│   ├── OM.xlsx / OM.xls
│   └── Plan de accion/
│       ├── PA_1.xlsx
│       └── PA_2.xlsx
├── output/
│   └── Resultados Consolidados.xlsx
└── db/
    └── registros_om.db
```

---

## 5. Troubleshooting Operativo

### 5.1 Problemas Comunes

| Problema | Solución |
|---------|----------|
| Error al cargar Excel | Verificar que el archivo no esté abierto |
| Timeout en API | Verificar conexión a internet, ajustar timeout |
| Error de formato | Revisar data contracts en `config/data_contracts.yaml` |
| Página en blanco | Verificar logs de Streamlit, verificar DataFrame |

### 5.2 Logs

```bash
# Ver logs de Streamlit
streamlit run streamlit_app/app.py --logger.level=debug

# Ver logs de la aplicación
tail -f logs/app.log
```

---

## 6. Referencias

- **Config TOML:** [`config.toml`](../../config.toml)
- **Settings:** [`config/settings.toml`](../../config/settings.toml)
- **Requirements:** [`requirements.txt`](../../requirements.txt)
- **Dockerfile:** [`Dockerfile`](../../Dockerfile)
