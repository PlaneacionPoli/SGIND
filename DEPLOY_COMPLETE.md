# Guía completa de despliegue: SGIND v2 (Frontend + Backend)

Este documento describe cómo desplegar la aplicación completa en producción.

## Arquitectura de despliegue

```
┌─────────────────────────────────────────────────────────────┐
│                        Netlify CDN                           │
│  Frontend: Next.js 14 (sgind-v2/frontend)                   │
└────────────────────┬────────────────────────────────────────┘
                     │ API calls (HTTPS)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend API (FastAPI)                      │
│  - Render.com, Railway, AWS Lambda, o Google Cloud Run      │
│  - URL: https://api.sgind.poligran.edu.co                   │
└────────────────────┬────────────────────────────────────────┘
                     │ Database connection
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL                                │
│  - Managed Database (AWS RDS, Railway, Supabase, etc.)      │
└─────────────────────────────────────────────────────────────┘
```

## Fase 1: Preparación

### 1.1 Verificar estructura del proyecto

```bash
cd sgind-v2

# Debe contener:
ls -la
# frontend/
# backend/
# database/
# docker-compose.yml
# netlify.toml (frontend)
```

### 1.2 Crear account en proveedores

Elige uno según tus necesidades:

#### Backend hosting:
- **Render.com** (recomendado para FastAPI)
- Railway
- AWS Lambda + API Gateway
- Google Cloud Run
- Heroku

#### Database:
- **Supabase** (PostgreSQL managed)
- AWS RDS
- Railway Database
- Google Cloud SQL

### 1.3 Configurar credenciales

Copia las credenciales necesarias de:
- Azure AD (para autenticación)
- Provider de hosting (para Deploy tokens)

## Fase 2: Backend - Despliegue en Render

### 2.1 Preparar backend

```bash
cd sgind-v2/backend

# Crear requirements.txt actualizado
pip install -r requirements.txt
# (Asegúrate que esté en requirements.txt)

# Verificar que el código funciona localmente
ENVIRONMENT=staging python -m uvicorn app.main:app --reload
```

### 2.2 Crear Dockerfile (si no existe)

```dockerfile
# sgind-v2/backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código
COPY . .

# Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.3 Crear archivo render.yaml

```yaml
# sgind-v2/render.yaml
services:
  - type: web
    name: sgind-backend
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: cd sgind-v2/backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
    envVars:
      - key: ENVIRONMENT
        value: staging
      - key: LOG_LEVEL
        value: INFO
      - key: DATABASE_URL
        fromDatabase:
          name: sgind-db
          property: connectionString
      - key: SECRET_KEY
        sync: false
      - key: JWT_ALGORITHM
        value: HS256
      - key: JWT_EXPIRE_MINUTES
        value: "480"
      - key: CORS_ORIGINS
        value: https://sgind-staging.netlify.app,https://sgind.poligran.edu.co
      - key: AZURE_TENANT_ID
        sync: false
      - key: AZURE_CLIENT_ID
        sync: false
      - key: AZURE_CLIENT_SECRET
        sync: false
      - key: AZURE_REDIRECT_URI
        value: https://api-staging.sgind.poligran.edu.co/api/v1/auth/callback

  - type: pserv
    name: sgind-db
    dbName: sgind
    user: sgind_user
    plan: free  # Cambiar a 'standard' para producción
    region: oregon
```

### 2.4 Desplegar en Render

1. Ve a [render.com](https://render.com)
2. Conecta tu repositorio de GitHub
3. Haz clic en "Create Blueprint"
4. Sube el archivo `render.yaml`
5. Configurar variables de entorno sensibles:
   - `SECRET_KEY`: Generar con `python -c "import secrets; print(secrets.token_hex(32))"`
   - `AZURE_CLIENT_ID`: De Azure AD
   - `AZURE_CLIENT_SECRET`: De Azure AD
   - `AZURE_TENANT_ID`: De Azure AD
6. Haz clic en "Create Blueprint"

### 2.5 Obtener URL del backend

Después del deploy exitoso, Render proporciona una URL:
```
https://sgind-backend.onrender.com
```

Actualiza esta en:
- `netlify.toml` (frontend)
- Variables de entorno de Netlify
- `.env.staging` en el proyecto raíz

## Fase 3: Frontend - Despliegue en Netlify

### 3.1 Configurar Netlify

```bash
cd sgind-v2/frontend

# Instalar CLI
npm install -g netlify-cli

# Autenticar
netlify login

# Crear sitio (si no existe)
netlify connect
```

### 3.2 Configurar variables de entorno

En **Netlify → Settings → Build & deploy → Environment**:

```
NEXT_PUBLIC_API_URL=https://sgind-backend.onrender.com
NEXT_PUBLIC_ENV=staging
```

### 3.3 Desplegar

```bash
cd sgind-v2/frontend
npm run build
netlify deploy --prod
```

O desde GitHub (automático):

1. Netlify Dashboard → "New site from Git"
2. Conectar repositorio
3. Base directory: `sgind-v2/frontend`
4. Build command: `npm run build`
5. Publish directory: `.next/standalone`

## Fase 4: Configuración post-despliegue

### 4.1 Salud del sistema

Verificar que todo funciona:

```bash
# Frontend
curl https://sgind-staging.netlify.app

# Backend
curl https://sgind-backend.onrender.com/docs
curl https://sgind-backend.onrender.com/api/v1/health

# Database
psql postgresql://sgind_user:password@host:5432/sgind -c "SELECT 1"
```

### 4.2 Dominios personalizados

#### Frontend:

1. Netlify → Domain management → Add custom domain
2. Dominio: `sgind.poligran.edu.co`
3. Actualizar DNS records (CNAME)

#### Backend:

1. Render → Custom domain
2. Dominio: `api.sgind.poligran.edu.co`
3. Actualizar DNS records (CNAME)

Verificar:

```bash
# Debe resolver el nombre de dominio
nslookup sgind.poligran.edu.co
nslookup api.sgind.poligran.edu.co

# Debe servir HTTPS
curl -I https://sgind.poligran.edu.co
curl -I https://api.sgind.poligran.edu.co
```

### 4.3 Monitoreo

#### Logs en tiempo real:

```bash
# Backend (Render)
render logs sgind-backend --follow

# Frontend (Netlify)
netlify logs --tail
```

#### Alertas:

- Render: Settings → Alerts
- Netlify: Settings → Notifications

### 4.4 Backups de base de datos

Si usas Render Postgres:

1. Render → Database → Backups
2. Habilitar backups automáticos (diarios)
3. Retención: 7 días

Para producción, usar:
- AWS RDS con backups a S3
- Supabase con PITR (Point-in-Time Recovery)

## Fase 5: Ciclo de desarrollo

### Rama develop (staging)

```bash
# Push a develop dispara auto-build en:
# - Netlify → https://sgind-staging.netlify.app
# - Render → https://sgind-backend.onrender.com

git push origin develop
```

### Rama main (producción)

```bash
# Después de QA en staging, merge a main
git push origin main

# Dispara deploy automático en ambos servicios
# Frontend: https://sgind.poligran.edu.co
# Backend: https://api.sgind.poligran.edu.co
```

### Rollback de emergencia

```bash
# Si hay problema en producción:

# Backend
render deploy sgind-backend --build-id <previous-build-id>

# Frontend
netlify deploy --alias=production --prod
```

## Checklist de despliegue

### Pre-despliegue
- [ ] Código testeado localmente
- [ ] Variables de entorno configuradas
- [ ] Database migrations ejecutadas
- [ ] Frontend build funciona (`npm run build`)
- [ ] Backend tests pasan (`pytest`)

### Backend (Render)
- [ ] render.yaml creado y validado
- [ ] Credenciales Azure AD configuradas
- [ ] Database creada y migrada
- [ ] Health check respondiendo
- [ ] CORS configurado correctamente

### Frontend (Netlify)
- [ ] netlify.toml configurado
- [ ] Variables de entorno correctas
- [ ] API URL apuntando al backend correcto
- [ ] Build funciona
- [ ] Rutas SPA funcionando (sin 404s)
- [ ] API calls funcionando

### Post-despliegue
- [ ] Acceder a URLs (HTTP → HTTPS redirect)
- [ ] Login funciona (Azure AD)
- [ ] Dashboard carga datos desde API
- [ ] Búsqueda/filtros funcionan
- [ ] Reportes generan correctamente
- [ ] Logs están siendo registrados
- [ ] Alertas configuradas

## Troubleshooting

### "Cannot connect to API"

```bash
# Verificar CORS en backend
curl -I -X OPTIONS https://api.sgind.poligran.edu.co

# Debe tener headers:
# Access-Control-Allow-Origin: https://sgind.netlify.app
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
```

Solución: Actualizar `CORS_ORIGINS` en backend `.env`

### "Build fails on Netlify"

```bash
# Limpiar cache
netlify build --context=production

# Ver logs detallados
netlify deploy --dry-run
```

### "Database connection timeout"

Verificar que:
1. IP del backend esté en lista blanca del database
2. Connection string es correcta
3. Database está en la misma región o tiene latencia baja

## Costos estimados (mensuales)

| Servicio | Tier | Costo |
|----------|------|-------|
| Netlify | Free/Pro | $19-99 |
| Render | Starter (web) | $7+ |
| Render | Database | $7+ |
| **Total** | | ~$25+ |

## Referencias

- [Render Deployment Guide](https://render.com/docs)
- [Netlify Documentation](https://docs.netlify.com)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [FastAPI on Render](https://render.com/docs/python)
