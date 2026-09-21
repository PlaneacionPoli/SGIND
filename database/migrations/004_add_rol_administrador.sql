-- 004_add_rol_administrador.sql
-- Agrega el rol "administrador". Se asigna por la variable de entorno
-- ADMIN_EMAILS al iniciar sesion (ver backend/app/services/auth_service.py).
--
-- NOTA OPERATIVA: /docker-entrypoint-initdb.d solo corre en una BD nueva.
-- En bases ya desplegadas hay que aplicar este archivo a mano:
--   psql "$DATABASE_URL" -f database/migrations/004_add_rol_administrador.sql

INSERT INTO roles (name, description) VALUES
    ('administrador', 'Acceso total: todas las pantallas y edicion de OM')
ON CONFLICT (name) DO NOTHING;
