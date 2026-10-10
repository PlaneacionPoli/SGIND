-- 005_alertas_seguimiento.sql
-- Alertas de Seguimiento Operativo (borradores .eml para Outlook): parametros, plazos por proceso,
-- destinatarios por proceso e historial de envios. Idempotente (se puede
-- volver a aplicar).
--
-- NOTA OPERATIVA: /docker-entrypoint-initdb.d solo corre en una BD nueva.
-- En bases ya desplegadas hay que aplicar este archivo a mano:
--   psql "$DATABASE_URL" -f database/migrations/005_alertas_seguimiento.sql

CREATE TABLE IF NOT EXISTS alertas_config (
    id          INTEGER PRIMARY KEY,
    activo      BOOLEAN NOT NULL DEFAULT FALSE,
    dias_antes  INTEGER NOT NULL DEFAULT 5,
    plazo_dias  INTEGER NOT NULL DEFAULT 15,   -- plazo general (dias tras cerrar el mes)
    hora_envio  INTEGER NOT NULL DEFAULT 7,
    asunto      TEXT NOT NULL DEFAULT 'Recordatorio: reporte de indicadores {proceso} — corte {corte}',
    cuerpo      TEXT NOT NULL DEFAULT '',
    copia_a     TEXT NOT NULL DEFAULT '',
    updated_by  TEXT NOT NULL DEFAULT '',
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT alertas_config_singleton CHECK (id = 1)
);

-- Aviso de apertura: dia 1..apertura_dias de cada mes, a todos los procesos.
ALTER TABLE alertas_config ADD COLUMN IF NOT EXISTS apertura_activo BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE alertas_config ADD COLUMN IF NOT EXISTS apertura_dias   INTEGER NOT NULL DEFAULT 3;
ALTER TABLE alertas_config ADD COLUMN IF NOT EXISTS apertura_asunto TEXT NOT NULL DEFAULT 'Inicia el reporte de indicadores — corte {corte} ({proceso})';
ALTER TABLE alertas_config ADD COLUMN IF NOT EXISTS apertura_cuerpo TEXT NOT NULL DEFAULT '';

-- Plazo propio por proceso. Los procesos que no figuran usan alertas_config.plazo_dias.
CREATE TABLE IF NOT EXISTS alertas_plazos (
    proceso     TEXT PRIMARY KEY,
    plazo_dias  INTEGER NOT NULL CHECK (plazo_dias BETWEEN 0 AND 120)
);

INSERT INTO alertas_plazos (proceso, plazo_dias) VALUES
    ('Planeación Financiera', 25),
    ('Contabilidad',          25),
    ('Tesorería',             25),
    ('Planeación Estratégica', 20),
    ('GESTIÓN AMBIENTAL',      20)
ON CONFLICT (proceso) DO NOTHING;

CREATE TABLE IF NOT EXISTS alertas_destinatarios (
    id          SERIAL PRIMARY KEY,
    proceso     TEXT NOT NULL,
    email       TEXT NOT NULL,
    activo      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_alerta_proceso_email UNIQUE (proceso, email)
);

CREATE TABLE IF NOT EXISTS alertas_envios (
    id                 SERIAL PRIMARY KEY,
    proceso            TEXT NOT NULL,
    anio               INTEGER NOT NULL,
    mes                INTEGER NOT NULL,
    estado             TEXT NOT NULL,          -- listo | descargado
    destinatarios      TEXT NOT NULL DEFAULT '',
    total_indicadores  INTEGER NOT NULL DEFAULT 0,
    detalle            TEXT,
    origen             TEXT NOT NULL DEFAULT 'automatico',
    enviado_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE alertas_envios ADD COLUMN IF NOT EXISTS tipo TEXT NOT NULL DEFAULT 'recordatorio';  -- recordatorio | apertura

CREATE INDEX IF NOT EXISTS idx_alertas_envios_corte
    ON alertas_envios (proceso, anio, mes, tipo, estado);
