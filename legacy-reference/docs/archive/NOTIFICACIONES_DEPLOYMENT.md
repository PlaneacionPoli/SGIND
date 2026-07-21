# NOTIFICACIONES — GUÍA DE DEPLOYMENT EN PRODUCCIÓN
## PHASE 4.3: Configuración de Alertas por Email + Slack

**Fecha**: 9 de mayo de 2026  
**Estado**: Ready for Production  
**Componentes**: EmailNotifier + SlackNotifier (en scripts/etl/notifications.py)  
**Tests**: 12 tests unitarios ✅

---

## 📋 PRE-REQUISITOS

### Requerimientos
- [ ] Acceso a servidor de producción (Linux/Windows)
- [ ] Credenciales SMTP (Gmail, SendGrid, AWS SES, etc.)
- [ ] Webhook URL de Slack (si deseas alertas en Slack)
- [ ] Python 3.9+ con virtualenv activado
- [ ] Permisos para crear/modificar .env en producción

### Variables de Entorno Necesarias

```bash
# SMTP (Email)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=sgind-alerts@politecnico.edu.co
SENDER_PASSWORD=tu_contraseña_app_aqui
RECIPIENT_EMAILS=ops@politecnico.edu.co;dba@politecnico.edu.co

# Slack (Opcional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## 🔧 PASO 1: Configurar SMTP (Email)

### Opción A: Gmail (Recomendado para Testing)

1. **Habilitar contraseña de aplicación en Gmail:**
   - Ir a: https://myaccount.google.com/apppasswords
   - Seleccionar: Correo + Windows (o tu SO)
   - Copiar la contraseña de 16 caracteres

2. **Crear archivo `.env` en raíz del proyecto:**
   ```bash
   cp .env.template .env
   ```

3. **Editar `.env` con valores reales:**
   ```bash
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SENDER_EMAIL=tu_email@gmail.com
   SENDER_PASSWORD=xxxx xxxx xxxx xxxx  # Contraseña de 16 caracteres
   RECIPIENT_EMAILS=ops@example.com;dba@example.com
   ```

4. **Verificar permisos:**
   ```bash
   chmod 600 .env  # Solo lectura para usuario
   ```

### Opción B: SendGrid (Recomendado para Producción)

1. **Crear cuenta en SendGrid** (https://sendgrid.com)

2. **Generar API Key en Settings → API Keys**

3. **Configurar `.env`:**
   ```bash
   SMTP_SERVER=smtp.sendgrid.net
   SMTP_PORT=587
   SENDER_EMAIL=apikey
   SENDER_PASSWORD=SG.xxxx_tu_api_key_aqui_xxxx
   RECIPIENT_EMAILS=ops@politecnico.edu.co;dba@politecnico.edu.co
   ```

### Opción C: AWS SES (Para AWS deployments)

1. **Verificar dominio en AWS SES Console**
2. **Generar credenciales IAM (SMTP)**
3. **Configurar `.env`:**
   ```bash
   SMTP_SERVER=email-smtp.us-east-1.amazonaws.com  # Cambiar región
   SMTP_PORT=587
   SENDER_EMAIL=noreply@politecnico.edu.co
   SENDER_PASSWORD=tu_contraseña_iam_aqui
   RECIPIENT_EMAILS=ops@politecnico.edu.co;dba@politecnico.edu.co
   ```

---

## 🔔 PASO 2: Configurar Slack Notifications (Opcional)

1. **Crear Workspace en Slack** (si no tienes)

2. **Crear Canal #sgind-alerts** para alertas

3. **Ir a Slack API (https://api.slack.com/apps)**
   - Click: "Create New App"
   - From Scratch → Nombre: "SGIND Alerts"
   - Seleccionar workspace

4. **Enable Incoming Webhooks:**
   - Features → "Incoming Webhooks"
   - Click: "Add New Webhook to Workspace"
   - Seleccionar canal: #sgind-alerts
   - Copiar Webhook URL

5. **Configurar `.env`:**
   ```bash
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```

---

## ✅ PASO 3: Validar Configuración

### Test Local

```bash
# Activar virtual env
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate   # Linux/Mac

# Ejecutar script de prueba
python scripts/test_notifications_config.py

# Opciones:
python scripts/test_notifications_config.py --smtp     # Solo email
python scripts/test_notifications_config.py --slack    # Solo Slack
python scripts/test_notifications_config.py --both     # Ambos (default)
```

**Resultado esperado:**
```
✅ SMTP: PASÓ
✅ Slack: PASÓ
✅ TODAS LAS PRUEBAS PASARON
```

### Validación en Consola

```bash
# Verificar que variables están cargadas
python -c "import os; print('SMTP_SERVER:', os.getenv('SMTP_SERVER', 'NO CONFIGURADO'))"
python -c "import os; print('SLACK_WEBHOOK_URL:', os.getenv('SLACK_WEBHOOK_URL', 'NO CONFIGURADO'))"
```

---

## 🚀 PASO 4: Deploy en Producción

### Opción A: Linux/Docker

```bash
# 1. Copiar .env a servidor (vía SCP o Secrets Manager)
scp .env usuario@servidor:/home/sgind/.env

# 2. En el servidor, permisos restrictivos
ssh usuario@servidor
chmod 600 /home/sgind/.env

# 3. Ejecutar pytest para validar
cd /home/sgind/Sistema_Indicadores_Poli
.venv/bin/python -m pytest tests/test_notifications.py -v

# 4. Ejecutar script de test
.venv/bin/python scripts/test_notifications_config.py --both
```

### Opción B: Manejo de Secrets (Recomendado)

En lugar de archivo `.env` en prod, usar:

```bash
# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id sgind-notifications
# → Descarga JSON con variables

# O Azure Key Vault
az keyvault secret show --name sgind-smtp-password

# O Variables de entorno del servidor
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SENDER_EMAIL=alerts@politecnico.edu.co
export SENDER_PASSWORD=xxxxx
export RECIPIENT_EMAILS=ops@politecnico.edu.co
```

### Opción C: Docker Secrets (Si usan Compose)

En `docker-compose.yml`:
```yaml
services:
  sgind:
    environment:
      SMTP_SERVER: ${SMTP_SERVER}
      SMTP_PORT: ${SMTP_PORT}
      SENDER_EMAIL: ${SENDER_EMAIL}
      SENDER_PASSWORD: ${SENDER_PASSWORD}
      RECIPIENT_EMAILS: ${RECIPIENT_EMAILS}
    secrets:
      - smtp_password

secrets:
  smtp_password:
    external: true  # Cargado de host
```

---

## 📊 PASO 5: Verificación Post-Deploy

### Checklist

- [ ] Archivo `.env` existe y tiene permisos 600
- [ ] Variables SMTP_* están configuradas
- [ ] Test `python scripts/test_notifications_config.py` retorna ✅
- [ ] Email de prueba recibido en bandeja de entrada
- [ ] (Opcional) Slack webhook envía mensaje a #sgind-alerts
- [ ] Pipeline actual se ejecutó sin errores relacionados

### Monitoreo Contínuo

```bash
# Verificar que las alertas se envían en cada consolidación
grep "send_pipeline_failure_alert\|send_recovery_success_alert" scripts/etl/actualizar_consolidado.py

# Ver logs de notificaciones
tail -f .logs/notifications.log  # Si lo configuraste

# Ejecutar consolidado y monitorear
python scripts/actualizar_consolidado.py
# Esperar a que se complete
# Verificar email/Slack recibidos
```

---

## 🔒 SEGURIDAD

### Checklist de Seguridad

- [ ] `.env` NO está en `.gitignore` ← VERIFICAR QUE SÍ ESTÉ
- [ ] `.env` tiene permisos restrictivos (600)
- [ ] Contraseña SMTP es token de app, NO contraseña maestra
- [ ] SMTP_PASSWORD NO está hardcodeado en scripts
- [ ] Logs NO muestran contraseñas (usar `***` en logs)
- [ ] SMTP_PORT=587 (TLS) en lugar de puerto inseguro

### Rotación de Contraseñas

```bash
# Cada 90 días (política recomendada)
# 1. Generar nueva contraseña en proveedor (Gmail, SendGrid, etc.)
# 2. Actualizar SENDER_PASSWORD en .env
# 3. Verificar con script de test
# 4. Documentar en changelog
```

---

## 🐛 TROUBLESHOOTING

### Error: "SMTPAuthenticationError"
- Causa: Credenciales incorrectas
- Solución: Verificar SENDER_PASSWORD (Gmail requiere contraseña de app, no maestra)

### Error: "SMTPServerDisconnected"
- Causa: SMTP_SERVER o SMTP_PORT incorrecto
- Solución: Verificar con `telnet SMTP_SERVER SMTP_PORT`

### Error: "Connection refused"
- Causa: Firewall bloquea puerto 587
- Solución: Contactar admin de red, permitir outbound 587 a SMTP_SERVER

### Slack webhook "invalid_token"
- Causa: Webhook URL incorreta o expirada
- Solución: Regenerar webhook en https://api.slack.com/apps/

### Email nunca llega
- Verificar: carpeta Spam/Junk
- Verificar: RECIPIENT_EMAILS está correctamente escrito
- Verificar: SENDER_EMAIL es dominio verificado (si SES)

---

## 📞 SOPORTE

**Si algo falla en producción:**

1. Ejecutar: `python scripts/test_notifications_config.py --both`
2. Revisar logs: `cat logs/notifications.log | tail -100`
3. Verificar `.env` está bien formado: `python -c "from dotenv import load_dotenv; load_dotenv()"`
4. Ejecutar tests: `pytest tests/test_notifications.py -v`
5. Contactar: ops@politecnico.edu.co

---

## ✅ CHECKLIST FINAL

- [x] Instrucciones de setup claras
- [x] Script de test disponible
- [x] 3 opciones SMTP (Gmail, SendGrid, AWS SES)
- [x] Setup Slack (opcional)
- [x] Guía de seguridad
- [x] Troubleshooting
- [x] Monitoreo contínuo

**READY FOR PRODUCTION** ✅

---

*Sistema de Indicadores Institucionales — Politécnico Grancolombiano*  
*9 de mayo de 2026*
