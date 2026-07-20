# Opciones de despliegue para SGIND v2

Esta documentación compara las 3 principales opciones de despliegue configuradas para tu proyecto.

---

## 📊 Comparativa rápida

| Aspecto | **Railway** | Netlify | Render |
|---------|-----------|---------|--------|
| **Frontend** | ✅ Next.js | ✅ Next.js | ✅ Next.js |
| **Backend** | ✅ FastAPI | ❌ | ✅ FastAPI |
| **Database** | ✅ PostgreSQL | ❌ | ✅ PostgreSQL |
| **Full-stack** | ✅ TODO EN UNO | ❌ Separado | ✅ TODO EN UNO |
| **Facilidad** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Costo** | $15/mes | $19/mes (free tier) | $20/mes |
| **Curva aprendizaje** | ⭐ Muy fácil | ⭐ Muy fácil | ⭐⭐ Fácil |
| **Ideal para** | Full-stack Python | SPA estáticas | Full-stack Python |
| **Recomendación** | 🏆 MEJOR | Alternativa | Alternativa |

---

## 🎯 Recomendación

### ✅ **RAILWAY es la mejor opción para SGIND v2**

**Por qué**:
1. ✅ **Todo en un lugar**: Frontend, Backend, Database
2. ✅ **Más simple**: Dashboard visual, auto-deployment
3. ✅ **Mejor precio**: $15/mes vs $20-30 en Render/Netlify
4. ✅ **Mejor DX**: Auto-staging, rollback 1-click, logs excelentes
5. ✅ **Soporte Python**: FastAPI funciona perfecto
6. ✅ **Rápido**: Deploy en ~25-30 minutos

---

## 📋 Documentación por plataforma

### 🚀 Railway (RECOMENDADO)

**Para empezar rápido**: [RAILWAY_QUICKSTART.md](./RAILWAY_QUICKSTART.md) (5 pasos, 30 min)

**Guía completa**: [DEPLOY_RAILWAY.md](./DEPLOY_RAILWAY.md) (con troubleshooting)

**Flujo**:
```
1. Crear cuenta (2 min)
2. Database PostgreSQL (3 min)
3. Backend FastAPI (5 min)
4. Frontend Next.js (5 min)
5. Configurar dominios (5-10 min)
─────────────────────────────
= 25-30 minutos total
```

---

### 🌐 Netlify

**Guía**: [DEPLOY_NETLIFY.md](./frontend/DEPLOY_NETLIFY.md)

**Limitaciones para SGIND v2**:
- ❌ No soporta backend Python (FastAPI)
- ❌ No incluye database
- ✅ Frontend (Next.js) funciona excelente

**Caso de uso**: Si solo quieres desplegar el frontend y tienes el backend en otro lugar.

**Flujo**:
```
1. Crear cuenta (2 min)
2. Conectar repositorio (2 min)
3. Configurar variables (3 min)
4. Deploy frontend (3 min)
5. Desplegar backend por separado (Render/Railway)
─────────────────────────────
= 10+ minutos + tiempo backend
```

---

### 🎨 Render

**Documentación**: [DEPLOY_COMPLETE.md](./DEPLOY_COMPLETE.md)

**Características**:
- ✅ Full-stack (frontend + backend + database)
- ✅ Similar a Railway
- ⚠️ Más complejo en configuración
- ⚠️ Más caro ($20+/mes)

**Caso de uso**: Alternativa viable si prefieres Render sobre Railway.

---

## 🗂️ Archivos de configuración incluidos

### Para Railway

```
sgind-v2/
├── DEPLOY_RAILWAY.md          # Guía detallada (30 pasos)
├── RAILWAY_QUICKSTART.md      # Guía rápida (5 pasos)
├── backend/
│   └── Dockerfile             # Ya existe, listo para Railway
└── frontend/
    ├── netlify.toml           # Compatible con Railway
    ├── .env.example
    └── next.config.mjs        # Railway-ready
```

### Para Netlify

```
sgind-v2/
├── DEPLOY_NETLIFY.md          # Guía Netlify
├── frontend/
│   ├── netlify.toml           # ✅ Configurado
│   ├── .env.example           # ✅ Incluido
│   └── next.config.mjs        # ✅ Actualizado
```

### Para Render

```
sgind-v2/
├── DEPLOY_COMPLETE.md         # Guía full-stack
├── backend/
│   └── Dockerfile             # ✅ Incluido
└── frontend/
    ├── next.config.mjs        # Compatible
    └── .env.example
```

---

## 🎓 Guía por escenario

### Escenario 1: "Quiero lo más fácil y rápido"

→ **Railway** + [RAILWAY_QUICKSTART.md](./RAILWAY_QUICKSTART.md)

```
Tiempo: 30 minutos
Costo: $15/mes
Complejidad: ⭐ Muy fácil
```

### Escenario 2: "Solo quiero desplegar el frontend"

→ **Netlify** + [DEPLOY_NETLIFY.md](./frontend/DEPLOY_NETLIFY.md)

```
Tiempo: 10 minutos
Costo: $19/mes (frontend) + $15+ (backend en Railway)
Complejidad: ⭐ Muy fácil
```

### Escenario 3: "Quiero máximo control y opciones"

→ **Render** + [DEPLOY_COMPLETE.md](./DEPLOY_COMPLETE.md)

```
Tiempo: 45 minutos
Costo: $20+/mes
Complejidad: ⭐⭐⭐ Intermedia
```

### Escenario 4: "Tengo presupuesto y quiero lo mejor"

→ **AWS Lambda** (no documentado, pero Netlify/Vercel sirven como fronts)

```
Tiempo: 2+ horas
Costo: Variable, potencialmente menos con free tier
Complejidad: ⭐⭐⭐⭐⭐ Difícil
```

---

## 💰 Análisis de costos (12 meses)

### Railway (RECOMENDADO)

```
Frontend (512MB)     $60/año
Backend (512MB)      $60/año
PostgreSQL (1GB)     $60/año
─────────────────────────
TOTAL               $180/año ($15/mes)

Créditos gratis      -$60 (primer mes)
NETO                $120/año
```

### Netlify + Render

```
Netlify (frontend)   $228/año
Render (backend)     $240/año
Render (database)    $240/año
─────────────────────────
TOTAL               $708/año ($59/mes)

DIFERENCIA: +$528/año vs Railway
```

### Render (alternativa)

```
Render (frontend)    $60/año
Render (backend)     $240/año
Render (database)    $240/año
─────────────────────────
TOTAL               $540/año ($45/mes)

DIFERENCIA: +$360/año vs Railway
```

---

## 🚀 Recomendación final

### Para SGIND v2: **RAILWAY**

**Razones**:

1. **Precio**: 3x más barato que Netlify/Render para full-stack
2. **Velocidad**: Deploy en 30 minutos vs 45-60 en otros
3. **Facilidad**: UI visual, no requiere CLI (opcional)
4. **Soporte**: FastAPI + PostgreSQL + Next.js todo soportado
5. **DX**: Logs excelentes, rollback 1-click, auto-staging
6. **Documentación**: Excelente, muy activa comunidad

### Pasos para empezar

```
1. Abre: https://railway.app
2. Haz clic en "Start Free"
3. Conecta GitHub
4. Sigue: RAILWAY_QUICKSTART.md (5 pasos)
5. En 30 min: sgind.poligran.edu.co ✅ en vivo
```

---

## ✅ Pre-deployment checklist

Antes de desplegar con cualquier opción:

- [ ] Código en GitHub
- [ ] `.gitignore` correctamente configurado (no incluye `.env`)
- [ ] Backend `requirements.txt` actualizado
- [ ] Frontend `package.json` actualizado
- [ ] Dockerfile del backend existe
- [ ] Variables de entorno documentadas (`.env.example`)
- [ ] Credenciales Azure AD obtenidas
- [ ] Dominio registrado y accesible

---

## 📚 Referencia rápida

### URLs importantes

| Plataforma | URL |
|-----------|-----|
| Railway | https://railway.app |
| Netlify | https://netlify.com |
| Render | https://render.com |
| Azure AD | https://portal.azure.com |

### Comandos útiles

```bash
# Verificar que el proyecto está listo
cd sgind-v2/frontend
npm run build
# Debe crear .next/standalone/

cd sgind-v2/backend
pip install -r requirements.txt
# Debe instalar sin errores
```

### Documentación por archivo

| Archivo | Propósito | Para quién |
|---------|-----------|-----------|
| RAILWAY_QUICKSTART.md | 5 pasos en 30 min | Todos |
| DEPLOY_RAILWAY.md | Guía detallada + troubleshooting | Railway |
| DEPLOY_NETLIFY.md | Guía para Netlify | Netlify |
| DEPLOY_COMPLETE.md | Full-stack architecture | Todos (referencia) |
| DEPLOYMENT_CONFIG.md | Resumen de config | Todos |

---

## 🎯 Siguientes pasos

### Opción A: Empezar ahora con Railway (RECOMENDADO)

1. Abre [RAILWAY_QUICKSTART.md](./RAILWAY_QUICKSTART.md)
2. Abre [railway.app](https://railway.app)
3. Sigue los 5 pasos
4. **En 30 minutos tienes SGIND v2 en producción**

### Opción B: Evaluar opciones

1. Compara la tabla de arriba
2. Lee la sección de escenarios
3. Elige la que mejor se adapte
4. Abre la guía correspondiente

### Opción C: Configuración avanzada

1. Lee [DEPLOY_COMPLETE.md](./DEPLOY_COMPLETE.md)
2. Configura CI/CD con GitHub Actions
3. Configura alertas y monitoreo
4. Configura backups automáticos

---

## 📞 Soporte

Si tienes dudas:

1. **Railway**: https://docs.railway.app
2. **Netlify**: https://docs.netlify.com
3. **Render**: https://render.com/docs
4. **Este proyecto**: Consulta los archivos `.md`

---

**Última actualización**: 2026-06-21

**Decisión recomendada**: 🏆 Railway - 30 minutos, $15/mes, todo en un lugar
