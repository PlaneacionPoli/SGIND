/**
 * Fixtures y helpers compartidos para tests E2E de SGIND v2.
 *
 * Los mocks de API permiten correr los tests sin un backend activo.
 * Cada test puede usar `mockAPI(page)` para interceptar llamadas y
 * responder con datos de referencia.
 */

import { type Page } from "@playwright/test";

const API_BASE = "/api/v1";

// ─── Datos de referencia (fixtures) ──────────────────────────────────────────

export const MOCK_HEALTH = { status: "ok", version: "2.0.0", environment: "test" };

export const MOCK_DEV_TOKEN = {
  access_token: "mock-token-e2e",
  token_type: "bearer",
  expires_in: 3600,
};

export const MOCK_KPIS = {
  anio: 2025,
  periodo: "Diciembre",
  kpis: [
    { label: "Total indicadores", value: 120 },
    { label: "Cumplimiento global", value: "82%", unit: "%" },
    { label: "En peligro", value: 14 },
    { label: "En alerta", value: 22 },
  ],
  source: "mock",
};

export const MOCK_SEMAPHORE = [
  { categoria: "Cumplimiento", count: 84, percent: 70 },
  { categoria: "Alerta", count: 22, percent: 18.3 },
  { categoria: "Peligro", count: 14, percent: 11.7 },
];

export const MOCK_FILTROS = {
  anios: [2023, 2024, 2025],
  anio_default: 2025,
  corte_default: "Diciembre",
  cortes: ["Junio", "Diciembre"],
};

export const MOCK_CMI_DASHBOARD = {
  anio: 2025,
  mes: 12,
  corte: "Diciembre",
  anios_disponibles: [2023, 2024, 2025],
  cortes: ["Junio", "Diciembre"],
  total_indicadores: 48,
  kpis: { total: 48, con_dato: 42, promedio: 83.5, top_nivel: "Cumplimiento", en_riesgo: 8, conteo_estados: {} },
  cumplimiento_por_linea: [],
  distribucion_nivel: [
    { nivel: "Cumplimiento", cantidad: 29, porcentaje: 60.4, color: "#22c55e" },
    { nivel: "Alerta", cantidad: 8, porcentaje: 16.7, color: "#f59e0b" },
    { nivel: "Peligro", cantidad: 5, porcentaje: 10.4, color: "#ef4444" },
    { nivel: "Sobrecumplimiento", cantidad: 6, porcentaje: 12.5, color: "#3b82f6" },
  ],
  vista_rapida_lineas: [],
  insights: [],
  lineas_detalle: [],
  indicadores: [],
  alertas: { peligro: 5, alerta: 8, items: [] },
};

export const MOCK_OM_LIST: unknown[] = [];

// ─── Helper: intercepta todas las llamadas a /api/v1/* ───────────────────────

export async function mockAPI(page: Page) {
  await page.route(`**${API_BASE}/health`, (r) =>
    r.fulfill({ json: MOCK_HEALTH })
  );
  await page.route(`**${API_BASE}/auth/dev-token**`, (r) =>
    r.fulfill({ json: MOCK_DEV_TOKEN })
  );
  await page.route(`**${API_BASE}/dashboard/kpis**`, (r) =>
    r.fulfill({ json: MOCK_KPIS })
  );
  await page.route(`**${API_BASE}/dashboard/semaphore**`, (r) =>
    r.fulfill({ json: MOCK_SEMAPHORE })
  );
  await page.route(`**${API_BASE}/dashboard/filtros**`, (r) =>
    r.fulfill({ json: MOCK_FILTROS })
  );
  await page.route(`**${API_BASE}/dashboard/trend**`, (r) =>
    r.fulfill({ json: [] })
  );
  await page.route(`**${API_BASE}/dashboard/resumen-completo**`, (r) =>
    r.fulfill({ json: { anio: 2025, vista: "general", chips: [], fichas: [], sunburst: { labels: [], parents: [], values: [], colors: [], text: [] }, narrativa: { texto: "", estado_color: "#22c55e", estado_icon: "✓" }, mejoraron: [], en_riesgo: [], periodo_comparacion: "2024", total_indicadores: 120 } })
  );
  await page.route(`**${API_BASE}/cmi/filtros**`, (r) =>
    r.fulfill({ json: MOCK_FILTROS })
  );
  await page.route(`**${API_BASE}/cmi/estrategico-dashboard**`, (r) =>
    r.fulfill({ json: MOCK_CMI_DASHBOARD })
  );
  await page.route(`**${API_BASE}/cmi/procesos/filtros**`, (r) =>
    r.fulfill({
      json: {
        anios: [2025],
        anio_default: 2025,
        meses: [12],
        mes_default: 12,
        meses_nombres: ["Diciembre"],
        unidades: [],
        procesos: [],
        subprocesos: [],
        clasificaciones: [],
        frecuencias: [],
      },
    })
  );
  await page.route(`**${API_BASE}/cmi/procesos-dashboard**`, (r) =>
    r.fulfill({ json: { anio: 2025, mes: 12, mes_nombre: "Diciembre", anios_disponibles: [2025], meses_disponibles: [12], filtros_aplicados: {}, total_indicadores: 0, kpis: { total: 0, con_dato: 0, promedio: 0, top_nivel: "Sin dato", en_riesgo: 0, conteo_estados: {}, n_procesos: 0, n_subprocesos: 0, n_unidades: 0 }, banner: { titulo: "", anio: 2025, mes: "Diciembre", cumplimiento_global: null, cumplimiento_base_anio: null, base_anio: 2024, base_mes: null, variacion_pp: null, total_indicadores: 0, en_riesgo: 0 }, distribucion_nivel: [], tipo_proceso_cards: [], proceso_bars: [], catalog_charts: { periodicidad: [], tipo_indicador: [] }, procesos_detalle: [], unidades_detalle: [], indicadores_summary: {}, indicadores: [], alertas: { peligro: 0, alerta: 0, items: [] }, variacion: { mejoraron: [], empeoraron: [], top_riesgo_procesos: [] }, meta: { base_anio: 2024, base_mes: null, latest_month_global: 12 }, analisis_avanzado: { propuesta_accion: { proceso: "", plan_mejoramiento: "", pdi: "", sga: "", retos: "", top_criticos: [] }, variacion_procesos: { mejoraron: [], empeoraron: [] }, insights: { mejora_proceso: "", riesgo_proceso: "" }, narrativa_proceso: { titulo: "", estado_color: "#22c55e", foco_urgente: "", directrices: [], texto_html: "", fuente: "" }, variacion_indicadores: { mejoraron: [], empeoraron: [], top_riesgo_procesos: [] }, historico_indicadores: [] }, calidad: { disponible: false, mensaje: null, score_global: null, dim_scores: {}, dim_colors: {}, kpis: { total_registros: 0, total_subprocesos: 0, promedio: null }, por_proceso: [], por_subproceso: [], alertas_dim: [], registros: [] }, vista_global: { mes_corte: 12, mes_nombre: "Diciembre", kpis: { total: 0, con_dato: 0, promedio: 0, top_nivel: "Sin dato", en_riesgo: 0, conteo_estados: {}, n_procesos: 0, n_subprocesos: 0, n_unidades: 0 }, banner: { titulo: "", anio: 2025, mes: "Diciembre", cumplimiento_global: null, cumplimiento_base_anio: null, base_anio: 2024, base_mes: null, variacion_pp: null, total_indicadores: 0, en_riesgo: 0 }, distribucion_nivel: [], tipo_proceso_cards: [], proceso_bars: [], catalog_charts: { periodicidad: [], tipo_indicador: [] }, procesos_detalle: [], unidades_detalle: [], comparativa_procesos: [], variacion: { mejoraron: [], empeoraron: [], top_riesgo_procesos: [] }, alertas_criticas: [] }, ejecucion_variacion: { positiva: [], negativa: [] } } })
  );
  await page.route(`**${API_BASE}/om**`, (r) =>
    r.fulfill({ json: MOCK_OM_LIST })
  );
  await page.route(`**${API_BASE}/om/matriz**`, (r) =>
    r.fulfill({ json: { anio: 2025, mes: "Diciembre", filtros: { anios: ["2025"], anio_default: "2025", meses: [], mes_default: "Diciembre", procesos: [], subprocesos: [] }, filtros_aplicados: {}, kpis: { peligro: 0, alerta: 0, con_om: 0, total: 0, avance_om_promedio: null }, filas: [], tipo_accion_colores: {} } })
  );
  await page.route(`**${API_BASE}/seguimiento/**`, (r) =>
    r.fulfill({ json: { error: null, filtros: { anios: [], anio_default: null, meses: [], mes_default: 12, meses_nombres: [], procesos: [], estados: [] }, filtros_aplicados: {}, kpis: { registros: 0, reportados: 0, pendientes: 0, no_aplica: 0 }, alertas: { vencidos_total: 0, por_vencer_total: 0, vencidos: [], por_vencer: [] }, estado_por_proceso: [], detalle: [], estado_colores: {} } })
  );
  await page.route(`**${API_BASE}/plan-mejoramiento/**`, (r) =>
    r.fulfill({ json: { error: null, anio: 2025, mes: 12, corte: "Diciembre", filtros_corte: { anios: [2025], anio_default: 2025, corte_default: "Diciembre", cortes: ["Junio", "Diciembre"] }, filtros_cna: { factores: [], caracteristicas: [] }, filtros_aplicados: {}, kpis: { indicadores_cna: 0, factores_visibles: 0, caracteristicas_visibles: 0, con_cumplimiento: 0, promedio_cumplimiento: 0, catalogo_factores: 0, catalogo_caracteristicas: 0 }, graficos: { factor_bars: [], nivel_donut: [], factor_nivel_stacked: [], treemap: [] }, tabla_cna: [], acciones: { kpis: {}, avance_por_estado: [], tabla: [] }, total_indicadores: 0 } })
  );
  await page.route(`**${API_BASE}/informe/**`, (r) =>
    r.fulfill({ json: {} })
  );
  await page.route(`**${API_BASE}/pdi/**`, (r) =>
    r.fulfill({ json: { error: null, filtros: { estados: [], macros: [], horizontes: [], horizonte_default: "" }, filtros_aplicados: {}, kpis: { total: 0, cumplimiento_promedio: null, brecha_promedio: null }, treemap: [], benchmark: [], evolucion_brechas: [], tabla: [] } })
  );
}

/** Realiza el flujo de dev-login desde la página /login y espera que el dashboard cargue. */
export async function devLogin(page: Page) {
  await page.goto("/login");
  await page.waitForLoadState("networkidle");

  // Busca el botón de acceso de desarrollo en la página de login
  const loginBtn = page.getByRole("button", { name: /acceso de desarrollo/i });
  if (await loginBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
    await loginBtn.click();
    // Espera que la autenticación se resuelva y redirija
    await page.waitForTimeout(800);
  }
}
