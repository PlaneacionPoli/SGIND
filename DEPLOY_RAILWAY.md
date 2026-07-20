# Guía de Despliegue: SGIND v2 en Railway

Railway es una plataforma moderna y fácil de usar para desplegar aplicaciones full-stack. Esta guía cubre el despliegue de frontend, backend y database en Railway.

## 📋 Índice

1. [Requisitos previos](#requisitos-previos)
2. [Crear cuenta en Railway](#crear-cuenta-en-railway)
3. [Configurar base de datos](#paso-1-configurar-base-de-datos)
4. [Desplegar backend](#paso-2-desplegar-backend-fastapi)
5. [Desplegar frontend](#paso-3-desplegar-frontend-nextjs)
6. [Configurar dominio personalizado](#paso-4-configurar-dominio-personalizado)
7. [Verificación y monitoreo](#paso-5-verificación-y-monitoreo)
8. [Troubleshooting](#troubleshooting)

---

## Requisitos previos

- Cuenta de GitHub (para conectar repositorio)
- Repositorio del proyecto con código pusheado
- Credenciales de Azure AD (para autenticación)
- Tarjeta de crédito (Railway requiere verificación, pero ofrece crédito gratis)

---

## Crear cuenta en Railway

### 1. Registrarse

1. Ve a [railway.app](https://railway.app)
2. Haz clic en "Start Free"
3. Selecciona "Continue with GitHub"
4. Autoriza la aplicación de Railway
5. Completa tu perfil

### 2. Crear nuevo proyecto

1. Ve a tu dashboard
2. Haz clic en "New Project"
3. Selecciona "Deploy from GitHub repo"

---

## PASO 1: Configurar base de datos

Railway ofrece PostgreSQL managed. Vamos a crearlo primero porque el backend la necesita.

### 1.1 Crear servicio PostgreSQL

```
Dashboard → New Project → PostgreSQL
```

1. Se abre Railway en el editor visual
2. Ve a "Plugins" (icono de puzzle)
3. Busca "PostgreSQL"
4. Haz clic en "Add"
5. Se crea automáticamente un servicio `postgres`

### 1.2 Configurar la base de datos

1. En el diagrama, haz clic en el recuadro `postgres`
2. En la pestaña "Variables" copiar:
   - `DATABASE_URL` — URL de conexión completa
   - `PGHOST` — Host
   - `PGPORT` — Puerto (por defecto 5432)
   - `PGUSER` — Usuario
   - `PGPASSWORD` — Contraseña
   - `PGDATABASE` — Nombre de BD

Guarda estas credenciales, las necesitarás en los próximos pasos.

### 1.3 Inicializar la base de datos (opcional)

Si tienes migraciones SQL:

```bash
# Desde tu máquina local
cd sgind-v2/database

# Conectar a la BD en Railway
psql $DATABASE_URL -f 001_initial.sql

# O si tienes múltiples migraciones
for file in migrations/*.sql; do
  psql $DATABASE_URL -f "$file"
done
```

---

## PASO 2: Desplegar Backend (FastAPI)

### 2.1 Crear servicio web para el backend

```
Dashboard → Proyecto → New → GitHub Repo
```

1. Selecciona tu repositorio
2. Branch: `main` o `develop`
3. **Importante**: En la configuración, establece:
   - **Root Directory** (si aplica): `sgind-v2/backend`

### 2.2 Configurar Dockerfile

Verifica que exista `sgind-v2/backend/Dockerfile`:

```dockerfile
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

# Puerto
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Si no existe, créalo ahora:

```bash
cat > sgind-v2/backend/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
```

### 2.3 Configurar variables de entorno (Backend)

En el dashboard de Railway → Tu proyecto → Backend service → Variables

Copia estas variables:

```bash
ENVIRONMENT=production
LOG_LEVEL=INFO

# Base de datos (de PASO 1)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/sgind

# Seguridad JWT - GENERAR NUEVO:
# En terminal: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=<generar-nuevo-valor>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480

# CORS - Agrega tu frontend aquí
CORS_ORIGINS=https://tu-sitio.railway.app,https://sgind.poligran.edu.co

# Azure AD - Obtener de Azure Portal
AZURE_TENANT_ID=<tu-tenant-id>
AZURE_CLIENT_ID=<tu-client-id>
AZURE_CLIENT_SECRET=<tu-client-secret>

# Callback debe coincidir con lo que registraste en Azure
AZURE_REDIRECT_URI=https://api.tu-sitio.railway.app/api/v1/auth/callback

# Emails permitidos (vacío = cualquier usuario del tenant)
ALLOWED_EMAILS=

# Datos Excel
SGIND_DATA_PATH=/app/data
EXCEL_CACHE_TTL_SECONDS=300
```

**Importante**: 
- `AZURE_CLIENT_SECRET` debe ser un secreto (Railway los marca con icono 🔒)
- `SECRET_KEY` debe generarse nuevo para cada ambiente

### 2.4 Monitorear el deployment

En Dashboard → Backend service → Deployments

Verás un log como:

```
Building Docker image...
Building... (puede tomar 2-3 minutos)
✓ Build successful
Starting container...
✓ Container running
```

Cuando veas el URL asignado:
```
https://sgind-backend-production.up.railway.app
```

Anota este URL, lo necesitarás para el frontend.

### 2.5 Verificar que el backend funciona

```bash
# Test health check
curl https://sgind-backend-production.up.railway.app/api/v1/health

# Ver API docs
curl https://sgind-backend-production.up.railway.app/docs
```

---

## PASO 3: Desplegar Frontend (Next.js)

### 3.1 Crear servicio web para el frontend

```
Dashboard → Proyecto → New → GitHub Repo
```

1. Selecciona tu repositorio de nuevo
2. Branch: `main` o `develop`
3. **Root Directory**: `sgind-v2/frontend`

### 3.2 Configurar build y start

Railway detecta automáticamente que es Next.js. Verifica:

En Dashboard → Frontend service → Settings:

- **Build Command**: `npm run build`
- **Start Command**: `npm start`
- **Port**: `3000`

### 3.3 Configurar variables de entorno (Frontend)

En Dashboard → Frontend service → Variables

```bash
# API del backend (obtén el URL del PASO 2.4)
NEXT_PUBLIC_API_URL=https://sgind-backend-production.up.railway.app

# Ambiente
NEXT_PUBLIC_ENV=production
NEXT_PUBLIC_APP_NAME=SGIND v2
NEXT_PUBLIC_APP_VERSION=0.1.0
```

### 3.4 Actualizar CORS en backend

Ahora que tienes el URL del frontend, actualiza `CORS_ORIGINS` en el backend:

Backend service → Variables → CORS_ORIGINS

```bash
# Agregar el URL del frontend
CORS_ORIGINS=https://sgind-frontend-production.up.railway.app,https://sgind.poligran.edu.co
```

El backend se redesplegará automáticamente.

### 3.5 Monitorear el deployment del frontend

```
Dashboard → Frontend service → Deployments
```

Cuando esté listo, verás el URL:
```
https://sgind-frontend-production.up.railway.app
```

---

## PASO 4: Configurar dominio personalizado

### 4.1 Frontend con dominio personalizado

1. Dashboard → Frontend service → Settings
2. Scroll hasta "Domains"
3. Haz clic en "+ Generate Domain"
4. Elige tu dominio (o USA el autogenerado)

**Para dominio personalizado**:

1. Tienes un dominio como `sgind.poligran.edu.co`
2. En tu proveedor de DNS (GoDaddy, Namecheap, etc.):
   - Crear un registro CNAME:
     ```
     Nombre: sgind
     Tipo: CNAME
     Valor: sgind-frontend-production.up.railway.app
     ```
3. En Railway → Frontend service → Domains → Add Custom Domain
4. Ingresa: `sgind.poligran.edu.co`
5. Espera validación de DNS (5-10 minutos)

### 4.2 Backend con dominio personalizado

Repetir lo anterior para el backend:

1. CNAME: `api.sgind.poligran.edu.co` → `sgind-backend-production.up.railway.app`
2. Railway → Backend service → Domains → Add Custom Domain
3. Ingresa: `api.sgind.poligran.edu.co`

### 4.3 Actualizar variables después de dominios

Una vez que los dominios funcionen:

1. **Backend**: Actualizar `AZURE_REDIRECT_URI`:
   ```
   https://api.sgind.poligran.edu.co/api/v1/auth/callback
   ```

2. **Backend**: Actualizar `CORS_ORIGINS`:
   ```
   https://sgind.poligran.edu.co,https://api.sgind.poligran.edu.co
   ```

3. **Frontend**: Actualizar `NEXT_PUBLIC_API_URL`:
   ```
   https://api.sgind.poligran.edu.co
   ```

---

## PASO 5: Verificación y monitoreo

### 5.1 Verificar que todo funciona

```bash
# 1. Frontend carga
curl https://sgind.poligran.edu.co

# 2. Backend API funciona
curl https://api.sgind.poligran.edu.co/api/v1/health

# 3. Frontend puede conectar a backend
# En el navegador, abre DevTools (F12)
# Ve a Console y ejecuta:
fetch('https://api.sgind.poligran.edu.co/api/v1/health').then(r => r.json()).then(console.log)
```

### 5.2 Ver logs en tiempo real

```bash
# Backend logs
railway logs --service backend --follow

# Frontend logs
railway logs --service frontend --follow

# O en Dashboard → Service → View logs
```

### 5.3 Configurar alertas

Dashboard → Project → Settings → Alerts

Activa notificaciones para:
- Build failed
- Deployment completed
- High memory usage
- High CPU usage

### 5.4 Monitorear base de datos

Dashboard → PostgreSQL service → Logs

Ver queries lentas, conexiones activas, etc.

---

## Flujo de despliegue: Git to Production

Railway se integra automáticamente con GitHub. El flujo es:

```
┌─────────────────┐
│  Git push       │
│  (main branch)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Railway detects push               │
│  (automático)                       │
└────────┬────────────────────────────┘
         │
         ├──────────┬──────────┐
         ▼          ▼          ▼
    ┌────────┐ ┌────────┐ ┌────────┐
    │Backend │ │Frontend│ │ Database│
    │ Build  │ │ Build  │ │ (sin   │
    │        │ │        │ │  cambios)
    └────┬───┘ └───┬────┘ └────────┘
         │         │
         ▼         ▼
    ┌─────────────────────┐
    │ Deploy to production │
    │ (automático)        │
    └─────────────────────┘
```

Para **staging**, crea otra rama `develop` y Railway creará automáticamente servicios staging.

---

## CI/CD Avanzado (Opcional)

### Deploy desde PR

1. Dashboard → Project → Settings → GitHub Integration
2. Habilitar "Preview Deployments"
3. Cada PR crea un environment de prueba temporal

### Deploy manual

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up --service backend
railway up --service frontend

# Ver status
railway status
```

---

## Troubleshooting

### Error: "Cannot connect to database"

**Síntomas**: Backend logs muestran `connection refused`

**Solución**:

1. Verificar `DATABASE_URL` es correcto:
   ```bash
   railway logs --service backend | grep DATABASE
   ```

2. Verificar que PostgreSQL está corriendo:
   ```
   Dashboard → postgres service → Status
   ```

3. Verificar firewall: Railway permite conexiones desde cualquier IP

### Error: "CORS error" en frontend

**Síntomas**: Requests a API fallan con CORS error

**Solución**:

1. Verificar `CORS_ORIGINS` en backend:
   ```
   Backend service → Variables → CORS_ORIGINS
   ```
   Debe incluir el URL del frontend

2. Verificar que el backend responde a requests:
   ```bash
   curl -H "Origin: https://sgind.poligran.edu.co" \
        -X OPTIONS https://api.sgind.poligran.edu.co/api/v1/health
   ```

3. Si no devuelve headers CORS, revisar código FastAPI

### Error: "Build failed"

**Síntomas**: Dashboard muestra build error

**Solución**:

1. Revisar logs:
   ```
   Dashboard → Service → Deployments → Click en failed build
   ```

2. Common issues:
   - Node.js version: crear `.nvmrc` con `20`
   - Python version: verificar `runtime.txt` si aplica
   - Dependencias faltantes: `pip install -r requirements.txt`

### Error: "Application crashed"

**Síntomas**: Deploya pero luego crash

**Solución**:

1. Ver logs en tiempo real:
   ```bash
   railway logs --service backend --follow
   ```

2. Common issues:
   - Database connection timeout: verificar `DATABASE_URL`
   - Missing environment variable: revisar todas en Dashboard
   - Port conflict: Next.js debe escuchar en puerto 3000, FastAPI en 8000

### Dominio no resuelve

**Síntomas**: `nslookup sgind.poligran.edu.co` falla

**Solución**:

1. Verificar CNAME está correcto:
   ```bash
   nslookup sgind.poligran.edu.co
   # Debe devolver: sgind-frontend-production.up.railway.app
   ```

2. Si no devuelve CNAME:
   - Esperar propagación DNS (puede tomar 24h)
   - Verificar que CNAME está correcto en proveedor de DNS

3. Verificar Railway reconoce el dominio:
   ```
   Dashboard → Frontend service → Domains → Status
   ```

---

## Comandos útiles de Railway CLI

```bash
# Login
railway login

# Ver proyecto actual
railway status

# Ver logs
railway logs --service backend --follow
railway logs --service frontend --follow

# Ver variables
railway variables

# Set variable
railway variables set ENVIRONMENT=production

# Deploy específico
railway up --service backend

# Stop service
railway stop --service frontend

# Ejecutar comando en container
railway run bash
railway run python manage.py migrate
```

---

## Plan de costos (Monthly)

| Servicio | Recursos | Costo |
|----------|----------|-------|
| Frontend (Next.js) | 512MB RAM, 1 CPU | $5/mes |
| Backend (FastAPI) | 512MB RAM, 1 CPU | $5/mes |
| PostgreSQL | 1GB storage | $5/mes |
| **Total** | | **~$15/mes** |

Railway ofrece $5 de crédito gratis cuando te registras.

---

## Checklist de despliegue

### Pre-despliegue
- [ ] Código en GitHub
- [ ] Credenciales Azure AD obtenidas
- [ ] Dominio disponible
- [ ] Database migrations preparadas

### Railway Setup
- [ ] Cuenta creada y verificada
- [ ] PostgreSQL deployada
- [ ] Backend deployada y funcionando
- [ ] Frontend deployada y funcionando

### Configuración
- [ ] Variables de entorno correctas
- [ ] CORS configurado
- [ ] Azure Redirect URI actualizado
- [ ] Dominios personalizados activos

### Verificación
- [ ] Frontend carga sin errores
- [ ] Login con Azure AD funciona
- [ ] API requests funcionan
- [ ] Datos cargan desde dashboard
- [ ] Logs monitoreados

### Post-despliegue
- [ ] Backup de database habilitado
- [ ] Alertas configuradas
- [ ] Monitoreo activo

---

## Comparativa: Railway vs otras opciones

| Feature | Railway | Render | Vercel | Netlify |
|---------|---------|--------|--------|---------|
| Frontend | ✅ | ✅ | ✅ | ✅ |
| Backend (Python) | ✅ | ✅ | ❌ | ❌ |
| Database | ✅ | ✅ | ✅ (Serverless) | ❌ |
| Ease of use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Cost | $5-15/mes | $7-20/mes | $20-100/mes | $19-99/mes |
| Best for | Full-stack | Full-stack | SPA/JAM | SPA/JAM |

**Railway es ideal para SGIND v2** porque:
- ✅ Soporta Python/FastAPI
- ✅ Incluye PostgreSQL managed
- ✅ UI simple y visual
- ✅ Precio accesible
- ✅ Buena experiencia de desarrollador

---

## Referencias

- [Railway Documentation](https://docs.railway.app)
- [Railway GitHub Integration](https://docs.railway.app/guides/github)
- [Railway CLI](https://docs.railway.app/reference/cli)
- [Railway Pricing](https://railway.app/pricing)
- [PostgreSQL on Railway](https://docs.railway.app/databases/postgresql)

---

**Última actualización**: 2026-06-21
**Tiempo estimado de despliegue**: 30-45 minutos
**Dificultad**: ⭐⭐⭐ Intermedia (Railway automatiza mucho)
