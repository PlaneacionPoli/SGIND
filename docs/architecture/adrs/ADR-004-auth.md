# ADR-004: Autenticación — Microsoft Entra ID

**Estado:** Aceptado  
**Fecha:** 2026-06-13

## Decisión

Microsoft OIDC vía `msal` + JWT (Bearer) + whitelist de emails.

## Roles RBAC

| Rol | Lectura | OM CRUD | Admin |
|-----|---------|---------|-------|
| procesos | ✅ | ❌ | ❌ |
| calidad | ✅ | ✅ | ✅ |
| desempeno | ✅ | ✅ | ✅ |
