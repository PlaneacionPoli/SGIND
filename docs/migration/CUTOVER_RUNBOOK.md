# Cutover Runbook — SGIND v2 Go-Live

**Fase:** 12 — Cutover a Producción  
**Objetivo:** Migrar el tráfico de producción de Streamlit legacy a SGIND v2 sin pérdida de datos ni de servicio.  
**Prerequisito:** `ACCEPTANCE_DOCUMENT.md` firmado (Fase 11 aprobada).

---

## Resumen del Plan

```
T-7 días  → Preparación y comunicación previa
T-2 días  → Ensayo final y validación staging
T-1 día   → Backup completo y freeze de cambios
T=0       → VENTANA DE MANTENIMIENTO — cutover (60-90 min)
T+2 horas → Verificación post-cutover
T+48 horas → Cierre de monitoreo activo
T+30 días → Decisión final sobre Streamlit legacy
```

**Ventana recomendada:** Viernes 18:00 – 20:00 (tráfico mínimo institucional)  
**Duración estimada:** 60–90 minutos  
**Ejecutor principal:** ___________  
**Contacto de emergencia:** ___________

---

## Pre-requisitos de Entrada

Antes de iniciar la ventana de cutover, confirmar que todos están en `[x]`:

- [ ] `ACCEPTANCE_DOCUMENT.md` firmado por usuarios clave
- [ ] Script `uat_verify.py` pasó sin errores en staging
- [ ] `npm run build` pasa limpio en el branch a deployar
- [ ] Todos los tests pytest pasan (`pytest tests/ -q`)
- [ ] Imágenes Docker publicadas en GHCR con el tag del commit a desplegar
- [ ] Servidor de producción con Docker + compose v2 instalado
- [ ] `.env.production` creado y verificado en el servidor
- [ ] Secrets de GitHub configurados para CI/CD en producción
- [ ] Backup automático de PostgreSQL staging probado
- [ ] URL de producción acordada con el área de TI

---

## T-7 días — Preparación

### Comunicación previa a usuarios

1. Enviar comunicación inicial (ver `COMUNICACION_USUARIOS.md` → Plantilla A)
2. Confirmar fecha/hora de ventana de mantenimiento con directivos
3. Agendar sesión de capacitación/demostración si es necesario

### Checklist técnico

```bash
# Verificar que staging está sano
python sgind-v2/scripts/smoke_test.py \
    --api-url http://staging.poli.edu.co:8000 \
    --frontend-url http://staging.poli.edu.co:3000

# Verificar paridad numérica final
python sgind-v2/scripts/uat_verify.py \
    --api-url http://staging.poli.edu.co:8000 \
    --anio 2025 \
    --output-json uat_results_final.json
```

---

## T-2 días — Ensayo Final

### Validar el tag de release a deployar

```bash
# Crear tag de release en git
git tag v2.0.0 -m "SGIND v2 — Release candidato go-live"
git push origin v2.0.0

# Verificar que las imágenes existen en GHCR
curl -s https://ghcr.io/v2/ximena5745/sgind-v2-backend/tags/list
```

### Ensayo del flujo de cutover (en staging)

1. Simular el proceso completo en staging
2. Cronometrar cada paso
3. Documentar cualquier ajuste al runbook

---

## T-1 día — Freeze y Backup

### 1. Freeze de cambios

- Comunicar al equipo: **sin merges a `main` hasta después del cutover**
- Verificar que no hay PRs abiertos críticos

### 2. Backup completo

```bash
# ── En el servidor de PRODUCCIÓN ──

# Backup de PostgreSQL (si ya hay datos en producción)
BACKUP_DIR="/opt/sgind-v2/backups"
mkdir -p "$BACKUP_DIR"
DATE=$(date +%Y%m%d_%H%M%S)

docker compose exec -T db pg_dump -U sgind sgind \
    | gzip > "$BACKUP_DIR/sgind_PRE_CUTOVER_$DATE.sql.gz"

echo "Backup guardado: sgind_PRE_CUTOVER_$DATE.sql.gz"
ls -lh "$BACKUP_DIR"

# Backup de archivos Excel (fuente de verdad KPIs)
tar -czf "$BACKUP_DIR/data_PRE_CUTOVER_$DATE.tar.gz" /opt/sgind-v2/data/
```

### 3. Notificación de mantenimiento (T-24h)

Enviar Plantilla B de `COMUNICACION_USUARIOS.md`.

---

## T=0 — VENTANA DE CUTOVER

> **Inicio:** Confirmar con todos los involucrados antes de ejecutar el paso 1.

### PASO 1 — Anunciar inicio de mantenimiento (5 min)

```
[Teams/Email] Asunto: [SGIND] Mantenimiento en curso — sistema no disponible 60 min
Mensaje: El sistema de indicadores está en proceso de actualización.
         Estará disponible nuevamente a las [hora estimada].
```

### PASO 2 — Poner Streamlit en modo read-only (10 min)

```bash
# Desde el directorio raíz del repo:
python sgind-v2/scripts/set_streamlit_readonly.py --enable

# Verificar que el mensaje de mantenimiento aparece en Streamlit
# Abrir http://[url-streamlit] en el navegador
```

### PASO 3 — Deploy de SGIND v2 en producción (20 min)

```bash
# ── En el servidor de PRODUCCIÓN ──
cd /opt/sgind-v2

# Descargar imágenes del tag de release
export RELEASE_TAG="v2.0.0"
docker compose --env-file .env.production pull

# Levantar servicios
docker compose --env-file .env.production up -d

# Verificar que todos los contenedores están corriendo
docker compose ps

# Revisar logs iniciales
docker compose logs backend --tail=50
docker compose logs frontend --tail=20
```

### PASO 4 — Migración de datos final (15 min)

```bash
# Ejecutar migración Excel → PostgreSQL (idempotente)
docker compose exec backend python -m app.scripts.migrate_excel_to_postgres \
    --data-path /data

# Verificar conteo de registros
docker compose exec db psql -U sgind -d sgind \
    -c "SELECT COUNT(*) FROM acciones_mejora;"
```

### PASO 5 — Smoke tests en producción (5 min)

```bash
export PROD_URL="https://sgind-v2.poli.edu.co"
export PROD_API="https://api.sgind-v2.poli.edu.co"

python sgind-v2/scripts/smoke_test.py \
    --api-url "$PROD_API" \
    --frontend-url "$PROD_URL"
```

Si algún smoke test falla → **ir a ROLLBACK** (ver sección abajo).

### PASO 6 — Redirigir URL principal (5 min)

**Opción A — NGINX (mismo servidor):**

```nginx
# /etc/nginx/sites-available/sgind-produccion
server {
    listen 80;
    listen 443 ssl;
    server_name indicadores.poli.edu.co;

    # Redirigir a SGIND v2
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

**Opción B — DNS (si hay URL separada):**

Actualizar registro DNS para que `indicadores.poli.edu.co` apunte al servidor v2.  
TTL: 300 segundos (5 min) para rollback rápido si es necesario.

### PASO 7 — Verificación final (10 min)

```bash
# Verificación numérica completa en producción
python sgind-v2/scripts/uat_verify.py \
    --api-url "$PROD_API" \
    --anio 2025 \
    --output-json cutover_verify_$(date +%Y%m%d_%H%M).json
```

Verificar manualmente en el navegador:
- [ ] Login con cuenta institucional funciona
- [ ] Resumen General muestra KPIs correctos
- [ ] CMI Estratégico carga sin errores
- [ ] Informe por Procesos descarga PDF

### PASO 8 — Anunciar go-live (5 min)

```
[Teams/Email] Asunto: [SGIND v2] Sistema actualizado — ya disponible
Ver: COMUNICACION_USUARIOS.md → Plantilla C
```

**✅ CUTOVER COMPLETADO**

---

## ROLLBACK — Si algo falla

> Criterio de activación: smoke test falla O error crítico detectado en T+2h.  
> Decisión máxima: **30 minutos** desde detección del problema.

### Rollback NGINX / DNS (< 5 min)

```bash
# Revertir NGINX al upstream Streamlit
sudo nano /etc/nginx/sites-available/sgind-produccion
# → Cambiar proxy_pass a la URL de Streamlit Cloud

sudo nginx -t && sudo systemctl reload nginx
```

O si se usó DNS: cambiar el registro A de vuelta a la IP de Streamlit Cloud.

### Rollback de contenedores (< 5 min)

```bash
cd /opt/sgind-v2
docker compose down

# Volver al tag anterior (si existe)
# Editar docker-compose.yml para usar el SHA anterior
docker compose pull
docker compose up -d
```

### Rollback de base de datos (si hubo migración)

```bash
docker compose exec db psql -U sgind -d sgind \
    -c "DROP TABLE IF EXISTS acciones_mejora CASCADE;"

# Restaurar desde backup pre-cutover
BACKUP_FILE="$BACKUP_DIR/sgind_PRE_CUTOVER_YYYYMMDD_HHMMSS.sql.gz"
gunzip -c "$BACKUP_FILE" | docker compose exec -T db psql -U sgind -d sgind
```

### Reactivar Streamlit

```bash
python sgind-v2/scripts/set_streamlit_readonly.py --disable
```

### Comunicar rollback

```
[Teams/Email] Asunto: [SGIND] Actualización pospuesta — sistema restaurado
Mensaje: La actualización del sistema ha sido pospuesta para garantizar
         la calidad del servicio. El sistema legacy está nuevamente disponible.
         Notificaremos la nueva fecha de actualización.
```

---

## T+2 horas — Verificación Post-Cutover

Completar este checklist 2 horas después del go-live:

| # | Verificación | Estado |
|---|-------------|--------|
| 1 | Login institucional Azure AD funcional | |
| 2 | Resumen General — KPIs correctos vs legacy | |
| 3 | CMI Estratégico — datos año en curso | |
| 4 | Gestión OM — CRUD completo funcional | |
| 5 | Plan de Mejoramiento — filtros y tabla CNA | |
| 6 | Seguimiento Operativo — export Excel OK | |
| 7 | Informe por Procesos — PDF descargable | |
| 8 | Logs de backend sin errores 500 | |
| 9 | Tiempo de respuesta < 8 segundos por página | |
| 10 | Sin reportes de error de usuarios finales | |

```bash
# Monitoreo de logs en tiempo real
docker compose logs -f backend 2>&1 | grep -E "ERROR|WARNING|500"
```

---

## T+48 horas — Cierre de Monitoreo Activo

Al finalizar las 48 horas de monitoreo:

- [ ] Revisar logs: sin errores 5xx persistentes
- [ ] Confirmar métricas de uso (página más visitada, tiempos promedio)
- [ ] Documentar incidencias menores en `UAT_BUGS.md` para sprint de mantenimiento
- [ ] Comunicar cierre de monitoreo al equipo

---

## T+30 días — Decisión sobre Streamlit Legacy

Revisar con el equipo:

- [ ] Número de usuarios que aún acceden al Streamlit legacy
- [ ] Bugs bloqueantes registrados en v2 (si hay, no archivar aún)
- [ ] Si OK → ejecutar archivado: `sgind-v2/scripts/set_streamlit_readonly.py --archive`
- [ ] Actualizar `README.md` del repo con estado final

---

## Comandos de Monitoreo Útiles

```bash
# Estado de contenedores
docker compose ps

# Uso de recursos
docker stats --no-stream

# Logs backend (últimas 100 líneas)
docker compose logs backend --tail=100

# Logs frontend
docker compose logs frontend --tail=50

# Conexiones activas PostgreSQL
docker compose exec db psql -U sgind -d sgind \
    -c "SELECT count(*) FROM pg_stat_activity WHERE state='active';"

# Tamaño de la base de datos
docker compose exec db psql -U sgind -d sgind \
    -c "SELECT pg_size_pretty(pg_database_size('sgind'));"
```

---

## Contactos de Escalada

| Rol | Nombre | Contacto |
|-----|--------|---------|
| Responsable técnico | | |
| Director de Planeación | | |
| Soporte TI institucional | | |
| Azure AD admin | | |

---

*Referencia: `sgind-v2/docs/migration/ROADMAP.md` — Fase 12*  
*Rollback de staging: `sgind-v2/docs/migration/STAGING_RUNBOOK.md`*
