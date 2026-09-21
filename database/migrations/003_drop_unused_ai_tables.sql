-- 003_drop_unused_ai_tables.sql
-- Oleada 4 (G-10): retira ai_configs y ai_prompts.
--
-- Ambas tablas venian del diseno original (proveedor Anthropic, prompts y
-- config de IA en BD). La integracion real de IA usa google-genai con
-- configuracion en variables de entorno/codigo (backend/app/core/config.py)
-- y nunca las consulto. ADR-009 ya las declaraba opcionales.
--
-- audit_log se conserva a proposito: se llena por trigger sobre registros_om
-- y se consulta manualmente en auditorias; no necesita endpoint.
--
-- NOTA OPERATIVA: /docker-entrypoint-initdb.d solo corre en una BD nueva.
-- En bases ya desplegadas (staging/produccion) hay que aplicar este archivo a mano:
--   psql "$DATABASE_URL" -f database/migrations/003_drop_unused_ai_tables.sql

DROP TABLE IF EXISTS ai_prompts;
DROP TABLE IF EXISTS ai_configs;
