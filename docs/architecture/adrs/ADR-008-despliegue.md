# ADR-008: Despliegue — Docker → Azure Container Apps

**Estado:** Aceptado | **Fecha:** 2026-06-13

## Decisión
- Desarrollo: Docker Compose local
- MVP: Render/VPS o Azure Container Apps
- Producción: Azure Container Apps + PostgreSQL managed

## Consecuencias
- Multi-stage Dockerfiles ya configurados
- CI/CD GitHub Actions en Fase 11
