# Configuración de Despliegue - SGIND v2

## 📋 Resumen de cambios

Se ha configurado el proyecto para despliegue en Netlify (frontend) + Render (backend).

### Archivos creados

#### Frontend (`sgind-v2/frontend/`)

| Archivo | Propósito |
|---------|-----------|
| `netlify.toml` | Configuración de build, headers y redirects para Netlify |
| `.env.example` | Variables de entorno públicas (documentación) |
| `.env.local` | Variables de entorno locales (desarrollo) |
| `next.config.mjs` | **Actualizado** con optimizaciones Netlify-ready |

#### Documentación

| Archivo | Propósito |
|---------|-----------|
| `DEPLOY_NETLIFY.md` | Guía paso a paso para despliegue en Netlify |
| `DEPLOY_COMPLETE.md` | Arquitectura completa y guía de despliegue full-stack |
| `DEPLOYMENT_CONFIG.md` | Este archivo - resumen de configuración |

#### Scripts

| Archivo | Propósito |
|---------|-----------|
| `scripts/deploy.sh` | Script automatizado para verificación y despliegue |

---

## 🚀 Despliegue rápido

### Opción 1: Netlify Dashboard (más fácil)

```bash
# 1. Asegúrate de que los cambios estén en GitHub
git add .
git commit -m "chore: configure Netlify deployment"
git push origin main

# 2. Ve a https://app.netlify.com
# 3. "New site from Git" → Selecciona el repositorio
# 4. Base directory: sgind-v2/frontend
# 5. Build command: npm run build
# 6. Publish directory: .next/standalone
# 7. Configura variables de entorno
# 8. Deploy
```

### Opción 2: CLI (más automatizado)

```bash
cd sgind-v2/frontend
npm install -g netlify-cli
netlify login
netlify connect  # Configurar sitio
netlify deploy --prod
```

### Opción 3: Script automático

```bash
cd sgind-v2
./scripts/deploy.sh check       # Verificar requisitos
./scripts/deploy.sh build       # Construir
./scripts/deploy.sh deploy      # Desplegar
```

---

## 📝 Configuración de variables de entorno

### En Netlify Dashboard

**Staging**:
```
NEXT_PUBLIC_API_URL=https://api-staging.sgind.poligran.edu.co
NEXT_PUBLIC_ENV=staging
```

**Producción**:
```
NEXT_PUBLIC_API_URL=https://api.sgind.poligran.edu.co
NEXT_PUBLIC_ENV=production
```

### Backend (Render)

Variables que debe tener en Render:

```
ENVIRONMENT=staging|production
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/sgind
SECRET_KEY=<generado>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480
CORS_ORIGINS=https://sgind.netlify.app,https://sgind.poligran.edu.co
AZURE_TENANT_ID=<tu-tenant-id>
AZURE_CLIENT_ID=<tu-client-id>
AZURE_CLIENT_SECRET=<tu-client-secret>
AZURE_REDIRECT_URI=https://api.sgind.poligran.edu.co/api/v1/auth/callback
```

---

## 🔍 Verificación post-configuración

### 1. Verificar que netlify.toml es válido

```bash
cd sgind-v2/frontend

# Netlify debería validar automáticamente
netlify status
```

### 2. Verificar que next.config.mjs no tiene errores

```bash
cd sgind-v2/frontend
npm run build
```

Resultado esperado: `.next/standalone/` directorio creado

### 3. Verificar variables de entorno

```bash
# Desarrollo local
cd sgind-v2/frontend
cat .env.local

# Debe tener NEXT_PUBLIC_API_URL apuntando a tu backend
```

### 4. Test de rutas SPA

```bash
# Después de deploy en Netlify
curl https://tu-sitio.netlify.app/dashboard
# Debe redirigir a index.html, no retornar 404
```

---

## 🎯 Flujo de despliegue recomendado

```
┌─────────────────────────────────────────────────────┐
│  Desarrollo local (main branch)                     │
│  npm run dev                                        │
└────────────┬────────────────────────────────────────┘
             │ git push origin develop
             ▼
┌─────────────────────────────────────────────────────┐
│  Staging (develop branch)                           │
│  Auto-deploy en Netlify: sgind-staging.netlify.app  │
│  Backend en Render: api-staging.sgind.render.app    │
└────────────┬────────────────────────────────────────┘
             │ QA/Testing
             │ Pull request a main
             ▼
┌─────────────────────────────────────────────────────┐
│  Producción (main branch)                           │
│  Auto-deploy en Netlify: sgind.poligran.edu.co      │
│  Backend en Render: api.sgind.poligran.edu.co       │
└─────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuraciones importantes

### `netlify.toml`

Especifica:

1. **Build**:
   - Comando: `npm run build`
   - Directorio de salida: `.next/standalone`

2. **Variables de entorno**: Por environment (production/staging/development)

3. **Redirects**: Para SPA routing y API proxy

4. **Headers**: Seguridad (CORS, X-Frame-Options, etc.)

5. **Cache**: Assets estáticos con TTL de 1 año

### `next.config.mjs`

Actualizado con:

1. `output: "standalone"` - Optimizado para Netlify
2. SWC minification
3. Gzip compression
4. Security headers
5. Image optimization
6. Webpack optimization
7. Environment variables públicas

### `.env.local`

Configuración local (NO subir a GitHub):

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000  # Tu backend local
NEXT_PUBLIC_ENV=development
NEXT_PUBLIC_APP_NAME=SGIND v2
NEXT_PUBLIC_APP_VERSION=0.1.0
```

---

## 🔐 Checklist de seguridad

Antes de desplegar:

- [ ] `NEXT_PUBLIC_API_URL` apunta a HTTPS en producción
- [ ] Backend tiene CORS configurado correctamente
- [ ] Variables sensibles (SECRET_KEY, AZURE_CLIENT_SECRET) están en Netlify Secrets
- [ ] SSL/TLS activo en ambos frontend y backend
- [ ] Headers de seguridad configurados (en netlify.toml)
- [ ] Rate limiting en API
- [ ] CSRF protection en formularios
- [ ] Database backups habilitados

---

## 🆘 Solución de problemas comunes

### Error: "Cannot connect to API"

**Causa**: CORS no está configurado o NEXT_PUBLIC_API_URL es incorrecto

**Solución**:
```bash
# 1. Verificar variable de entorno en Netlify
# Debe ser la URL correcta del backend

# 2. Verificar CORS en backend
curl -H "Origin: https://tu-sitio.netlify.app" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS https://tu-api.com

# 3. Backend .env debe tener
CORS_ORIGINS=https://tu-sitio.netlify.app
```

### Error: "Build failed"

**Causa**: Node.js version, dependencies, o build script

**Solución**:
```bash
# 1. Crear .nvmrc para especificar Node.js version
echo "20" > sgind-v2/frontend/.nvmrc

# 2. Limpiar cache de Netlify
# Netlify dashboard → Settings → Build & deploy → Clear site cache

# 3. Reinstalar dependencies localmente
cd sgind-v2/frontend
rm -rf node_modules package-lock.json
npm ci
npm run build
```

### Error: "Routes returning 404"

**Causa**: SPA routing no configurado

**Solución**: Verificar que netlify.toml tiene:
```toml
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

---

## 📊 Monitoreo post-despliegue

### Netlify Analytics

```bash
netlify status
netlify logs --tail
```

### Métricas importantes

1. **Core Web Vitals**: Netlify Dashboard → Analytics
2. **Error Rate**: Monitoring en Render
3. **API Latency**: Backend logs
4. **Database Connections**: Database provider

---

## 🔄 CI/CD con GitHub Actions (opcional)

Crear `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Netlify

on:
  push:
    branches: [main, develop]
    paths:
      - "sgind-v2/frontend/**"

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: "20"
      - run: cd sgind-v2/frontend && npm ci && npm run build
      - uses: netlify/actions/cli@master
        env:
          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}
          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
```

---

## 📚 Referencias

- [Documentación de Netlify](https://docs.netlify.com/)
- [Guía Next.js en Netlify](https://docs.netlify.com/frameworks/next-js/overview/)
- [CLI de Netlify](https://docs.netlify.com/cli/get-started/)
- [Environment variables en Netlify](https://docs.netlify.com/configure-builds/environment-variables/)

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs en Netlify Dashboard
2. Verifica que backend está funcionando
3. Comprueba variables de entorno
4. Consulta `DEPLOY_NETLIFY.md` para guía detallada
5. Abre un issue en el repositorio

---

**Última actualización**: 2026-06-21
**Versión**: 1.0
