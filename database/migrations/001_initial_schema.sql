-- SGIND v2 — Esquema inicial PostgreSQL
-- Fase 2: Modelo de Datos
-- Compatible con migración desde SQLite (registros_om)

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Roles ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS roles (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO roles (name, description) VALUES
    ('procesos',  'Lectura de dashboards e indicadores'),
    ('calidad',   'Administración y gestión OM'),
    ('desempeno', 'Administración y gestión OM')
ON CONFLICT (name) DO NOTHING;

-- ── Usuarios ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT NOT NULL UNIQUE,
    name        TEXT,
    role_id     INTEGER NOT NULL REFERENCES roles(id),
    azure_oid   TEXT UNIQUE,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users (role_id);

-- ── Registros OM (migrado desde SQLite) ──────────────────────────
CREATE TABLE IF NOT EXISTS registros_om (
    id                SERIAL PRIMARY KEY,
    id_indicador      TEXT NOT NULL,
    nombre_indicador  TEXT,
    proceso           TEXT,
    periodo           TEXT,
    anio              INTEGER,
    sede              TEXT,
    tiene_om          INTEGER DEFAULT 0,
    tipo_accion       TEXT DEFAULT 'OM Kawak',
    numero_om         TEXT,
    comentario        TEXT,
    registrado_por    TEXT DEFAULT '',
    fecha_registro    TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT registros_om_unique_key UNIQUE (id_indicador, periodo, anio),
    CONSTRAINT chk_registros_om_tiene_om CHECK (tiene_om IN (0, 1)),
    CONSTRAINT chk_registros_om_anio CHECK (anio IS NULL OR (anio >= 2018 AND anio <= 2035))
);

CREATE INDEX IF NOT EXISTS idx_registros_om_anio_periodo
    ON registros_om (anio, periodo);
CREATE INDEX IF NOT EXISTS idx_registros_om_proceso
    ON registros_om (proceso);
CREATE INDEX IF NOT EXISTS idx_registros_om_id_indicador
    ON registros_om (id_indicador);
CREATE INDEX IF NOT EXISTS idx_registros_om_tiene_om
    ON registros_om (tiene_om) WHERE tiene_om = 1;

-- ── Acciones de mejora (migrado desde SQLite dinámico) ───────────
CREATE TABLE IF NOT EXISTS acciones (
    id              BIGSERIAL PRIMARY KEY,
    accion          TEXT,
    responsable     TEXT,
    estado          TEXT,
    marker_col      TEXT,
    marker_value    TEXT,
    payload         JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_acciones_estado ON acciones (estado);
CREATE INDEX IF NOT EXISTS idx_acciones_marker ON acciones (marker_col, marker_value);

-- ── Auditoría ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_log (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID REFERENCES users(id) ON DELETE SET NULL,
    action      TEXT NOT NULL,
    entity      TEXT NOT NULL,
    entity_id   TEXT,
    details     JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log (user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log (entity, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log (created_at DESC);

-- ── Configuración IA ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ai_configs (
    id                SERIAL PRIMARY KEY,
    provider          TEXT NOT NULL DEFAULT 'anthropic',
    model             TEXT NOT NULL,
    api_key_encrypted TEXT,
    temperature       NUMERIC(3,2) DEFAULT 0.3,
    max_tokens        INTEGER DEFAULT 1024,
    is_active         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Prompts IA ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ai_prompts (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    template    TEXT NOT NULL,
    max_tokens  INTEGER DEFAULT 1024,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Trigger: auditoría en registros_om ───────────────────────────
CREATE OR REPLACE FUNCTION audit_registros_om_changes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (action, entity, entity_id, details)
    VALUES (
        TG_OP,
        'registros_om',
        COALESCE(NEW.id_indicador, OLD.id_indicador),
        jsonb_build_object(
            'periodo', COALESCE(NEW.periodo, OLD.periodo),
            'anio', COALESCE(NEW.anio, OLD.anio),
            'tiene_om', COALESCE(NEW.tiene_om, OLD.tiene_om)
        )
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_registros_om_audit ON registros_om;
CREATE TRIGGER trg_registros_om_audit
AFTER INSERT OR UPDATE OR DELETE ON registros_om
FOR EACH ROW EXECUTE FUNCTION audit_registros_om_changes();

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN SELECT unnest(ARRAY['users', 'registros_om', 'ai_configs', 'ai_prompts'])
    LOOP
        EXECUTE format(
            'DROP TRIGGER IF EXISTS trg_%s_updated_at ON %I;
             CREATE TRIGGER trg_%s_updated_at
             BEFORE UPDATE ON %I
             FOR EACH ROW EXECUTE FUNCTION set_updated_at();',
            t, t, t, t
        );
    END LOOP;
END;
$$;
