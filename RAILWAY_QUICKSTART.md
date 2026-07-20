# Railway QuickStart - 5 pasos en 30 minutos

## 🎯 Objetivo final

Desplegar SGIND v2 completo (frontend + backend + database) en Railway.

```
┌──────────────────────────────────────────────────────────────┐
│                    RAILWAY DASHBOARD                         │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Frontend   │  │   Backend    │  │   PostgreSQL    │   │
│  │  Next.js    │◄─┤   FastAPI    │◄─┤   Database      │   │
│  │ :3000       │  │  :8000       │  │  :5432          │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
│        │                │                  │                 │
│        └────────────────┴──────────────────┘                │
│              ✅ HTTPS + SSL Automático                      │
└──────────────────────────────────────────────────────────────┘
```

---

## ✨ PASO 1: Crear cuenta Railway (2 min)

```bash
# 1. Ve a https://railway.app
# 2. Click "Start Free"
# 3. "Continue with GitHub"
# 4. ✅ Autoriza Railway
```

---

## 🗄️ PASO 2: Crear Database (3 min)

```
Dashboard → New Project → PostgreSQL
```

**Resultado**: Tendrás variables:
```
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/sgind
PGHOST=host
PGPORT=5432
PGUSER=user
PGPASSWORD=pass
```

**📌 Anota estas credenciales**, las necesitarás en los siguientes pasos.

---

## 🔧 PASO 3: Desplegar Backend (5 min)

### 3a. Conectar repo

```
Dashboard → New → GitHub Repo
Selecciona tu repositorio
Branch: main
Root Directory: sgind-v2/backend
```

Railway automáticamente:
- ✅ Detecta Python
- ✅ Lee Dockerfile
- ✅ Compila imagen Docker
- ✅ Despliega en ~2-3 minutos

### 3b. Configurar variables

Backend service → Variables:

```bash
# Copiar de PASO 2
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/sgind

# Copiar de Azure Portal
AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_SECRET=<tu-secreto>  # Click 🔒 para marcar como secret

# Generar nuevo
SECRET_KEY=<ejecuta: python -c "import secrets; print(secrets.token_hex(32))">

# Resto
ENVIRONMENT=production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480
CORS_ORIGINS=https://sgind-frontend.up.railway.app
AZURE_REDIRECT_URI=https://sgind-backend.up.railway.app/api/v1/auth/callback
LOG_LEVEL=INFO
```

### 3c. Obtener URL del backend

```
Backend service → Deployments → Copiar URL
Ejemplo: https://sgind-backend-production.up.railway.app
```

**📌 Anota este URL**

---

## 🎨 PASO 4: Desplegar Frontend (5 min)

### 4a. Conectar repo

```
Dashboard → New → GitHub Repo
Selecciona tu repositorio (mismo)
Branch: main
Root Directory: sgind-v2/frontend
```

Railway automáticamente:
- ✅ Detecta Next.js
- ✅ Ejecuta `npm install`
- ✅ Ejecuta `npm run build`
- ✅ Despliega en ~3-4 minutos

### 4b. Configurar variables

Frontend service → Variables:

```bash
# Usar URL del backend (de PASO 3c)
NEXT_PUBLIC_API_URL=https://sgind-backend-production.up.railway.app

# Resto
NEXT_PUBLIC_ENV=production
NEXT_PUBLIC_APP_NAME=SGIND v2
NEXT_PUBLIC_APP_VERSION=0.1.0
```

### 4c. Obtener URL del frontend

```
Frontend service → Deployments → Copiar URL
Ejemplo: https://sgind-frontend.up.railway.app
```

**📌 Anota este URL**

---

## 🌐 PASO 5: Configurar dominios (5 min)

### 5a. Frontend con dominio personalizado

```
Frontend service → Settings → Domains → Add Custom Domain
Ingresa: sgind.poligran.edu.co
Copia el CNAME que genera
```

### 5b. Agregar CNAME en tu proveedor DNS

En tu proveedor (GoDaddy, Namecheap, etc.):

```
Tipo: CNAME
Nombre: sgind
Valor: sgind-frontend-production.up.railway.app
```

### 5c. Repetir para backend

```
Backend service → Settings → Domains → Add Custom Domain
Ingresa: api.sgind.poligran.edu.co
CNAME: api.sgind-backend-production.up.railway.app
```

En DNS:

```
Tipo: CNAME
Nombre: api
Valor: sgind-backend-production.up.railway.app
```

**⏳ Espera 5-10 minutos** para que DNS se propague.

---

## ✅ Verificación final

```bash
# 1. Frontend carga
curl https://sgind.poligran.edu.co

# 2. Backend API funciona
curl https://api.sgind.poligran.edu.co/api/v1/health

# 3. Login funciona (en navegador)
# https://sgind.poligran.edu.co
# Click en login, debe redirigir a Microsoft login
```

---

## 📊 Ver logs en tiempo real

### Opción 1: Dashboard

```
Dashboard → Backend service → Logs → View live logs
Dashboard → Frontend service → Logs → View live logs
```

### Opción 2: CLI

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Ver logs
railway logs --service backend --follow
railway logs --service frontend --follow
```

---

## 🚀 Deploy automático en el futuro

Ahora, cada vez que hagas `git push`:

```
┌─────────────────────────────────────────────────┐
│  git push origin main                           │
└────────────┬────────────────────────────────────┘
             │ GitHub webhook
             ▼
┌─────────────────────────────────────────────────┐
│  Railway detecta cambios automáticamente        │
└────────┬────────────────────────────────┬───────┘
         │                                │
         ▼                                ▼
   ┌──────────────┐              ┌──────────────┐
   │   Backend    │              │  Frontend    │
   │   rebuild    │              │   rebuild    │
   │   & deploy   │              │   & deploy   │
   └──────────────┘              └──────────────┘
         │                                │
         └────────────┬───────────────────┘
                      ▼
         ✅ En vivo en producción
```

---

## 💡 Pro Tips

### Tip 1: Staging automático

Crea rama `develop` y Railway crea automáticamente environments staging:

```bash
git push origin develop
# Genera automáticamente:
# https://sgind-backend-staging.up.railway.app
# https://sgind-frontend-staging.up.railway.app
```

### Tip 2: Rollback rápido

```bash
# En Dashboard → Deployments → Click en deployment anterior
# Click "Redeploy" en 1 segundo
```

### Tip 3: Monitoreo

```bash
# Dashboard → Project → Settings → Alerts
# Activa notificaciones en Slack/Email
```

### Tip 4: Database backups

```bash
# PostgreSQL service → Backups → Enable automatic backups
# Railway guarda últimos 7 días automáticamente
```

---

## 🆘 Si algo falla

### Error: "Build failed"

```
Dashboard → Deployments → Click en failed build → Ver logs
Común: Faltan dependencias
Solución: Verificar requirements.txt y npm dependencies
```

### Error: "Cannot connect to database"

```bash
# Ver logs del backend
railway logs --service backend | grep -i database

# Verificar DATABASE_URL es correcto
# Debe ser: postgresql+asyncpg://user:pass@host:5432/sgind
```

### Error: "CORS error"

```
Backend service → Variables → CORS_ORIGINS
Debe incluir: https://sgind-frontend.up.railway.app
```

### Error: "Dominio no funciona"

```bash
# Esperar 5-10 minutos para DNS
nslookup sgind.poligran.edu.co

# Si aún no funciona, verificar CNAME en proveedor DNS
# Debe ser: sgind-frontend-production.up.railway.app
```

---

## 📈 Costos mensuales

```
Frontend (512MB, 1 CPU)    = $5
Backend (512MB, 1 CPU)     = $5
PostgreSQL (1GB storage)   = $5
─────────────────────────────
TOTAL                      ≈ $15/mes
```

Railway da $5 crédito gratis → primer mes es gratis.

---

## ✨ Resumen de comandos útiles

```bash
# Login
railway login

# Ver estado
railway status

# Ver logs
railway logs --follow
railway logs --service backend --follow
railway logs --service frontend --follow

# Set variables
railway variables set ENVIRONMENT=production

# Stop service
railway stop --service backend

# Ver proyecto
railway open
```

---

## 🎓 Próximos pasos

- [ ] Verificar que login con Azure AD funciona
- [ ] Verificar que dashboard carga datos
- [ ] Verificar que reports funcionan
- [ ] Configurar alertas en Slack
- [ ] Hacer backup manual de database
- [ ] Documentar URLs en equipo

---

## 📚 Documentación completa

- **Guía detallada**: [DEPLOY_RAILWAY.md](./DEPLOY_RAILWAY.md)
- **Troubleshooting**: [DEPLOY_RAILWAY.md#troubleshooting](./DEPLOY_RAILWAY.md#troubleshooting)
- **Railway Docs**: https://docs.railway.app

---

## ⏱️ Timeline

```
Paso 1 (Cuenta)      → 2 min  ✅
Paso 2 (Database)    → 3 min  ✅
Paso 3 (Backend)     → 5 min  ✅
Paso 4 (Frontend)    → 5 min  ✅
Paso 5 (Dominios)    → 5 min  ⏳ (DNS 5-10 min más)
─────────────────────────────
TOTAL               → 25 min + DNS
```

**⚡ En 30 minutos tienes SGIND v2 en producción**

---

**¿Listo para desplegar?** Empieza en [railway.app](https://railway.app)
