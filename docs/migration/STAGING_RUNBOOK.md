# Runbook de Staging — SGIND v2 Fase 10

**Última actualización:** 2026-06-19

---

## Arquitectura de staging

```
Internet
    │
    ▼
[ Servidor Linux ] (Ubuntu 22.04 o similar)
    ├── :3000  → Frontend Next.js   (container sgind-v2-frontend)
    ├── :8000  → Backend FastAPI    (container sgind-v2-backend)
    └── :5432  → PostgreSQL 16      (container sgind-v2-db — solo interno)
```

Para acceso externo se recomienda poner NGINX como reverse proxy (ver sección NGINX más abajo).

---

## Primer deploy manual

### 1. Requisitos en el servidor

```bash
# Docker + compose v2
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER  # y abrir nueva sesión

# Verificar
docker --version        # >= 24
docker compose version  # >= 2.20
```

### 2. Clonar / copiar archivos necesarios

```bash
mkdir -p /opt/sgind-v2
cd /opt/sgind-v2

# Copiar desde el repositorio (o clonar)
git clone https://github.com/Ximena5745/Sistema_Indicadores_Poli.git repo
cp repo/sgind-v2/docker-compose.staging.yml docker-compose.yml
cp -r repo/sgind-v2/database ./database
cp -r repo/data ./data         # datos Excel — directorio read-only
```

### 3. Crear `.env.staging`

```bash
cp repo/sgind-v2/.env.staging .env.staging

# Editar con valores reales:
nano .env.staging
# → Cambiar POSTGRES_PASSWORD, SECRET_KEY, AZURE_*, CORS_ORIGINS, NEXT_PUBLIC_API_URL
```

Variables obligatorias antes del primer deploy:

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `POSTGRES_PASSWORD` | `s3cr3tPass!` | Contraseña PostgreSQL (mín 16 chars) |
| `SECRET_KEY` | (output de `python -c "import secrets; print(secrets.token_hex(32))"`) | Clave JWT |
| `CORS_ORIGINS` | `https://sgind-v2.poli.edu.co` | URL del frontend |
| `NEXT_PUBLIC_API_URL` | `https://api.sgind-v2.poli.edu.co` | URL del backend (público) |
| `SGIND_DATA_HOST_PATH` | `/opt/sgind-v2/data` | Ruta de datos Excel en el host |

### 4. Autenticar en GHCR

```bash
# Token de GitHub con permisos read:packages
echo "ghp_TOKEN_AQUI" | docker login ghcr.io -u Ximena5745 --password-stdin
```

### 5. Primer arranque

```bash
cd /opt/sgind-v2
docker compose --env-file .env.staging pull
docker compose --env-file .env.staging up -d

# Verificar
docker compose ps
docker compose logs backend --tail=50
docker compose logs frontend --tail=20
```

### 6. Smoke tests manuales

```bash
# Health backend
curl http://localhost:8000/api/v1/health

# Auth endpoint
curl http://localhost:8000/api/v1/auth/login-url

# Frontend
curl -s http://localhost:3000 | grep "<title>"
```

---

## Deploy de una nueva versión (CI/CD automático)

Los merges a `main` disparan `.github/workflows/deploy-staging.yml` que:

1. Construye las imágenes Docker y las sube a GHCR
2. Si `STAGING_HOST` está configurado como secret de GitHub → SSH + `docker compose pull && up -d`
3. Ejecuta smoke tests automáticamente

### Secretos requeridos en GitHub (Settings → Secrets → Actions)

| Secret | Descripción |
|--------|-------------|
| `STAGING_HOST` | IP o hostname del servidor de staging |
| `STAGING_USER` | Usuario SSH (ej. `ubuntu`, `deploy`) |
| `STAGING_SSH_KEY` | Clave privada SSH (sin passphrase) |
| `STAGING_PORT` | Puerto SSH (opcional, default 22) |

### Variables de entorno en GitHub (Settings → Variables → Actions)

| Variable | Ejemplo |
|----------|---------|
| `STAGING_URL` | `http://staging.poli.edu.co:3000` |
| `STAGING_API_URL` | `http://staging.poli.edu.co:8000` |
| `STAGING_DEPLOY_DIR` | `/opt/sgind-v2` |

---

## Rollback

### Rollback rápido a imagen anterior (tag SHA)

```bash
# En el servidor
cd /opt/sgind-v2

# Listar tags disponibles en GHCR (o usar 'docker images' si ya fue descargada)
# Los tags SHA se generan como sha-XXXXXXX (7 chars del commit)

# Editar docker-compose.yml para usar el tag anterior
# image: ghcr.io/ximena5745/sgind-v2-backend:sha-abc1234
nano docker-compose.yml

docker compose pull
docker compose up -d --remove-orphans
```

### Rollback de base de datos

Si el schema cambió (migraciones nuevas), revertir manualmente:

```bash
# Conectar a PostgreSQL
docker compose exec db psql -U sgind -d sgind

-- Ver historial de migraciones (si se implementa tabla de migraciones)
-- Por ahora: restaurar desde backup

-- Restaurar desde backup del día anterior
\q

docker compose exec db psql -U sgind -d sgind < /backups/sgind_YYYYMMDD.sql
```

### Rollback completo a Streamlit legacy

Si SGIND v2 falla en staging y Streamlit sigue activo:

```bash
# En el servidor de staging, parar los contenedores
docker compose down

# El sistema legacy (Streamlit Cloud) nunca se apaga — sigue disponible
```

---

## NGINX reverse proxy (recomendado)

```nginx
# /etc/nginx/sites-available/sgind-v2-staging
server {
    listen 80;
    server_name sgind-v2-staging.poli.edu.co;

    # Frontend Next.js
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Backend FastAPI
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Con TLS (Let's Encrypt):

```bash
sudo certbot --nginx -d sgind-v2-staging.poli.edu.co
```

---

## Backups de PostgreSQL

```bash
# Cron diario en el servidor:
# 0 2 * * * /opt/sgind-v2/scripts/backup_db.sh

#!/bin/bash
BACKUP_DIR="/opt/sgind-v2/backups"
mkdir -p "$BACKUP_DIR"
DATE=$(date +%Y%m%d_%H%M%S)
docker compose -f /opt/sgind-v2/docker-compose.yml \
    exec -T db pg_dump -U sgind sgind \
    | gzip > "$BACKUP_DIR/sgind_$DATE.sql.gz"

# Mantener solo últimos 7 días
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete
```

---

## Smoke tests locales

```bash
# Con el stack corriendo localmente:
pip install httpx
python sgind-v2/scripts/smoke_test.py \
    --api-url http://localhost:8000 \
    --frontend-url http://localhost:3000
```

---

## Imágenes Docker en GHCR

| Imagen | URL |
|--------|-----|
| Backend | `ghcr.io/ximena5745/sgind-v2-backend:latest` |
| Frontend | `ghcr.io/ximena5745/sgind-v2-frontend:latest` |

Para ver todas las versiones publicadas:
`https://github.com/Ximena5745/Sistema_Indicadores_Poli/pkgs/container/sgind-v2-backend`
