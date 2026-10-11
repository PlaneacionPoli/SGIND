-- 006_login_otp.sql
-- Códigos de un solo uso (OTP) para el login por correo institucional.
-- Idempotente. En bases ya desplegadas aplicar a mano:
--   psql "$DATABASE_URL" -f database/migrations/006_login_otp.sql

CREATE TABLE IF NOT EXISTS login_otps (
    email       TEXT PRIMARY KEY,
    code_hash   TEXT NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    attempts    INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
