-- SGIND v2 — Queries críticas del dashboard (Fase 2)
-- Ejecutar contra PostgreSQL después de migración

-- Q1: KPIs OM por año y periodo
-- Uso: GET /api/v1/dashboard/kpis (complemento OM)
SELECT
    COUNT(*) AS total_registros,
    COUNT(*) FILTER (WHERE tiene_om = 1) AS con_om,
    COUNT(DISTINCT id_indicador) AS indicadores_unicos
FROM registros_om
WHERE anio = :anio AND periodo = :periodo;

-- Q2: Listado OM paginado (Gestión OM)
SELECT
    id, id_indicador, nombre_indicador, proceso, periodo, anio,
    tiene_om, tipo_accion, numero_om, comentario, registrado_por, fecha_registro
FROM registros_om
WHERE (:anio IS NULL OR anio = :anio)
  AND (:periodo IS NULL OR periodo = :periodo)
ORDER BY fecha_registro DESC NULLS LAST, id DESC
LIMIT :limit OFFSET :offset;

-- Q3: UPSERT OM (verificado en TP-2.2)
INSERT INTO registros_om (
    id_indicador, nombre_indicador, proceso, periodo, anio,
    tiene_om, tipo_accion, numero_om, comentario, registrado_por, fecha_registro
) VALUES (
    :id_indicador, :nombre_indicador, :proceso, :periodo, :anio,
    :tiene_om, :tipo_accion, :numero_om, :comentario, :registrado_por, :fecha_registro
)
ON CONFLICT ON CONSTRAINT registros_om_unique_key DO UPDATE SET
    nombre_indicador = EXCLUDED.nombre_indicador,
    proceso          = EXCLUDED.proceso,
    tiene_om         = EXCLUDED.tiene_om,
    tipo_accion      = EXCLUDED.tipo_accion,
    numero_om        = EXCLUDED.numero_om,
    comentario       = EXCLUDED.comentario,
    registrado_por   = EXCLUDED.registrado_por,
    fecha_registro   = EXCLUDED.fecha_registro,
    updated_at       = NOW()
RETURNING *;

-- Q4: Acciones por estado (Plan de Mejoramiento)
SELECT estado, COUNT(*) AS total
FROM acciones
GROUP BY estado
ORDER BY total DESC;

-- Q5: Auditoría reciente de cambios OM
SELECT
    al.created_at,
    al.action,
    al.entity_id,
    al.details,
    u.email AS usuario
FROM audit_log al
LEFT JOIN users u ON u.id = al.user_id
WHERE al.entity = 'registros_om'
ORDER BY al.created_at DESC
LIMIT 50;
