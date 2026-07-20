# Guía de Despliegue: SGIND v2 Frontend en Netlify

## Requisitos previos

- Cuenta de Netlify ([netlify.com](https://netlify.com))
- Repositorio en GitHub con acceso a `sgind-v2/frontend`
- Backend API desplegado en una URL accesible

## Pasos de despliegue

### 1. Preparación local

```bash
cd sgind-v2/frontend

# Instalar dependencias
npm install

# Verificar que la build funcione
npm run build

# Limpiar cache (si es necesario)
rm -rf .next node_modules
npm ci
npm run build
```

### 2. Conectar con GitHub

1. Asegúrate de que el código está en GitHub
2. Haz push de los cambios a la rama main o develop

```bash
git add .
git commit -m "chore: configure Netlify deployment"
git push origin main
```

### 3. Crear sitio en Netlify

#### Opción A: Desde Netlify Dashboard (recomendado)

1. Ve a [app.netlify.com](https://app.netlify.com)
2. Haz clic en "New site from Git"
3. Conecta tu repositorio de GitHub
4. Selecciona el repositorio del proyecto
5. Configura:
   - **Base directory**: `sgind-v2/frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `.next/standalone`
6. Haz clic en "Deploy site"

#### Opción B: Usando Netlify CLI

```bash
# Instalar CLI
npm install -g netlify-cli

# Autenticar
netlify login

# Navegar al directorio del frontend
cd sgind-v2/frontend

# Conectar y desplegar
netlify connect
netlify deploy --prod
```

### 4. Configurar variables de entorno

En **Netlify Dashboard → Settings → Build & deploy → Environment**:

#### Para **Staging**:

```
NEXT_PUBLIC_API_URL=https://api-staging.sgind.poligran.edu.co
NEXT_PUBLIC_ENV=staging
```

#### Para **Producción**:

```
NEXT_PUBLIC_API_URL=https://api.sgind.poligran.edu.co
NEXT_PUBLIC_ENV=production
```

### 5. Configurar dominio personalizado

1. En Netlify → Settings → Domain management
2. Haz clic en "Add custom domain"
3. Ingresa tu dominio (ej: `sgind.poligran.edu.co`)
4. Sigue las instrucciones para actualizar los DNS records

### 6. Configurar SSL/TLS

Netlify proporciona certificados HTTPS gratuitos automáticamente. No requiere configuración adicional.

### 7. Verificar despliegue

```bash
# Ver estado de builds
netlify status

# Ver logs de la última build
netlify logs
```

## Variables de entorno en Netlify

### `netlify.toml`

El archivo `netlify.toml` en la raíz del frontend especifica:

- **Build command**: `npm run build`
- **Publish directory**: `.next/standalone`
- **Funciones**: Soporte para Netlify Functions (opcional)
- **Headers de seguridad**: X-Frame-Options, X-Content-Type-Options, etc.
- **Caché**: Assets estáticos con cache de 1 año

### Redirecciones

El archivo `netlify.toml` redirige todas las solicitudes de `/api/*` a las Netlify Functions o al backend remoto.

Para modificar el proxy de API, edita:

```toml
[[redirects]]
  from = "/api/v1/*"
  to = "https://tu-api.com/:splat"
  status = 200
```

## Solución de problemas

### Error 404 en rutas SPA

**Problema**: Al acceder a rutas internas (ej: `/dashboard`), devuelve 404.

**Solución**: El archivo `netlify.toml` incluye una redirección que envía todas las rutas no encontradas a `/index.html`. Verifica que esté presente:

```toml
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

### Error de CORS

**Problema**: Solicitudes a la API fallan con "CORS error".

**Solución**:

1. Verifica que `NEXT_PUBLIC_API_URL` sea correcto
2. En el backend, configura `CORS_ORIGINS` para incluir tu dominio Netlify:

```bash
CORS_ORIGINS=https://tu-sitio.netlify.app,https://sgind.poligran.edu.co
```

3. Si usas Netlify Functions como proxy:

```javascript
// netlify/functions/api-proxy.js
exports.handler = async (event) => {
  const response = await fetch(`${process.env.BACKEND_URL}${event.path}`, {
    method: event.httpMethod,
    headers: event.headers,
    body: event.body,
  });
  
  return {
    statusCode: response.status,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Content-Type": "application/json",
    },
    body: await response.text(),
  };
};
```

### Build fallando

**Problema**: Build falla en Netlify pero funciona localmente.

**Soluciones**:

1. Verifica que `node_modules` no esté en el repositorio (debe estar en `.gitignore`)
2. Verifica que la versión de Node.js sea compatible:

   ```bash
   # En Netlify, establece Node.js 20+
   echo "20" > .nvmrc
   ```

3. Revisa los logs de build en Netlify Dashboard

4. Intenta limpiar el cache de build:
   - Netlify → Settings → Build & deploy → Clear site cache

### Despliegue lento

**Soluciones**:

1. **Usar cache de dependencias**:

   En `netlify.toml`:

   ```toml
   [build.cache]
     npm = ["node_modules"]
   ```

2. **Optimizar imágenes**: Asegúrate de que las imágenes estén optimizadas
3. **Usar CDN**: Netlify proporciona CDN global automáticamente

## Monitoreo post-despliegue

### Analytics

1. Ve a Netlify → Analytics
2. Monitorea:
   - Visitas
   - Errores de build
   - Uso de bandwidth

### Logs

```bash
netlify logs
netlify logs --tail  # Ver logs en tiempo real
```

### Health checks

Crea un endpoint de health check en el backend:

```javascript
// pages/api/health.ts
export default function handler(req, res) {
  res.status(200).json({ status: "healthy" });
}
```

Configura en Netlify → Settings → Health checks:

```
https://tu-sitio.netlify.app/api/health
```

## CI/CD con GitHub Actions

Netlify se integra automáticamente con GitHub, pero puedes crear un workflow personalizado:

```yaml
# .github/workflows/deploy.yml
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
          cache: "npm"
      - run: cd sgind-v2/frontend && npm ci
      - run: cd sgind-v2/frontend && npm run build
      - uses: netlify/actions/cli@master
        with:
          args: deploy --prod --dir=sgind-v2/frontend/.next/standalone
        env:
          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}
          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
```

## Rollback

Si necesitas revertir a una versión anterior:

1. Netlify → Deploys → Haz clic en el deploy anterior
2. Haz clic en "Trigger deploy"

O usando CLI:

```bash
netlify deploy --alias=staging --prod --dir=sgind-v2/frontend/.next/standalone
```

## Checklist de despliegue

- [ ] Variables de entorno configuradas
- [ ] Backend API accesible y CORS configurado
- [ ] Build funciona localmente (`npm run build`)
- [ ] Código pusheado a GitHub
- [ ] Sitio creado en Netlify
- [ ] Dominio personalizado configurado (opcional)
- [ ] SSL/TLS verificado
- [ ] Rutas SPA funcionando (sin 404s)
- [ ] API funcionando desde el frontend
- [ ] Analytics habilitado
- [ ] Logs monitoreados

## Referencias

- [Documentación de Netlify](https://docs.netlify.com/)
- [Guía de Next.js en Netlify](https://docs.netlify.com/frameworks/next-js/overview/)
- [CLI de Netlify](https://docs.netlify.com/cli/get-started/)
