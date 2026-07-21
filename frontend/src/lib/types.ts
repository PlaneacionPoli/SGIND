export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
}

export interface KPI {
  label: string;
  value: string | number;
  unit?: string;
  trend?: string;
}

export interface DashboardKPIsResponse {
  anio: number | null;
  periodo: string | null;
  kpis: KPI[];
  source: string;
}

export interface SemaphoreItem {
  categoria: string;
  count: number;
  percent: number;
}

export interface TrendItem {
  periodo: string;
  cumplimiento: number | null;
}

export interface Indicator {
  Id?: string;
  Indicador?: string;
  Proceso?: string;
  Linea?: string;
  Objetivo?: string;
  Anio?: number;
  Mes?: string;
  Periodo?: string;
  Meta?: number;
  Ejecucion?: number;
  Meta_Signo?: string;
  Ejecucion_s?: string;
  EjecS?: string;
  Decimales_Meta?: number;
  Decimales_Ejecucion?: number;
  Cumplimiento?: number;
  Cumplimiento_norm?: number;
  cumplimiento_pct?: number;
  Categoria?: string;
  "Nivel de cumplimiento"?: string;
  [key: string]: unknown;
}

export interface IndicatorListResponse {
  total: number;
  items: Indicator[];
  limit: number;
  offset: number;
  error?: string;
}

export interface CMILinea {
  linea: string;
  total_indicadores: number;
  cumplimiento_promedio: number | null;
  en_riesgo: number;
}

export interface CMIEstrategicoResponse {
  anio: number | null;
  total_indicadores: number;
  lineas: CMILinea[];
}

export interface CMIProceso {
  proceso: string;
  total_indicadores: number;
  cumplimiento_promedio: number | null;
  categorias: Record<string, number>;
}

export interface CMIProcesosResponse {
  anio: number | null;
  total_indicadores: number;
  procesos: CMIProceso[];
}

export interface CMIProcesosFiltrosResponse {
  anios: number[];
  anio_default: number;
  meses: number[];
  mes_default: number;
  meses_nombres: string[];
  unidades: string[];
  procesos: string[];
  subprocesos: string[];
  subprocesos_por_proceso: Record<string, string[]>;
  clasificaciones: string[];
  frecuencias: string[];
}

export interface CMIProcesoTipoCard {
  tipo: string;
  color: string;
  color_light: string;
  icon: string;
  cumplimiento: number | null;
  cumplimiento_anterior: number | null;
  variacion_pp: number | null;
  n_indicadores: number;
  n_riesgo: number;
}

export interface CMIProcesoBar {
  proceso: string;
  cumplimiento: number | null;
  cumplimiento_anterior: number | null;
  n_indicadores: number;
  color?: string;
  nivel?: string | null;
}

export interface CMIProcesoComparativa {
  proceso: string;
  tipo_proceso: string;
  tipo_color: string;
  cumplimiento: number | null;
  cumplimiento_anterior: number | null;
  variacion: number | null;
  n_indicadores: number;
  n_criticos: number;
  color: string;
  estado: string;
  estado_icon: string;
  estado_color: string;
}

export interface CMIAlertaCritica {
  id: string;
  indicador: string;
  proceso: string;
  tipo_proceso: string;
  tipo_color: string;
  cumplimiento: number | null;
  brecha_pp: number | null;
  nivel: string;
  diagnostico: string;
}

export interface CMIProcesoDetalle {
  proceso: string;
  unidad: string;
  tipo_proceso: string;
  total_indicadores: number;
  cumplimiento_promedio: number | null;
  categorias: Record<string, number>;
  en_riesgo: number;
  subprocesos: Array<{
    subproceso: string;
    cumplimiento: number | null;
    n_indicadores: number;
    en_riesgo: number;
  }>;
}

export interface CMIUnidadDetalle {
  unidad: string;
  cumplimiento_promedio: number | null;
  n_indicadores: number;
  n_procesos: number;
  en_riesgo: number;
  n_criticos?: number;
  color?: string;
  estado?: string;
  estado_icon?: string;
  estado_color?: string;
}

export interface CMIProcesosVistaGlobal {
  mes_corte: number;
  mes_nombre: string;
  kpis: CMIProcesosDashboardResponse["kpis"];
  banner: CMIProcesosDashboardResponse["banner"];
  distribucion_nivel: CMIProcesosDashboardResponse["distribucion_nivel"];
  tipo_proceso_cards: CMIProcesoTipoCard[];
  proceso_bars: CMIProcesoBar[];
  catalog_charts: CMIProcesosDashboardResponse["catalog_charts"];
  procesos_detalle: CMIProcesoDetalle[];
  unidades_detalle: CMIUnidadDetalle[];
  comparativa_procesos: CMIProcesoComparativa[];
  variacion: CMIProcesosDashboardResponse["variacion"];
  variacion_procesos: {
    mejoraron: Array<{ name: string; change: number }>;
    empeoraron: Array<{ name: string; change: number }>;
  };
  alertas_criticas: CMIAlertaCritica[];
  brecha_ambiental: {
    n_indicadores: number;
    cumplimiento_promedio: number | null;
    texto: string;
  };
}

export interface CMIProcesosDashboardResponse {
  anio: number;
  mes: number;
  mes_nombre: string;
  anios_disponibles: number[];
  meses_disponibles: number[];
  filtros_aplicados: Record<string, string>;
  total_indicadores: number;
  kpis: {
    total: number;
    con_dato: number;
    promedio: number;
    top_nivel: string;
    en_riesgo: number;
    conteo_estados: Record<string, number>;
    n_procesos: number;
    n_subprocesos: number;
    n_unidades: number;
  };
  banner: {
    titulo: string;
    anio: number;
    mes: string;
    cumplimiento_global: number | null;
    cumplimiento_base_anio: number | null;
    base_anio: number;
    base_mes: string | null;
    variacion_pp: number | null;
    total_indicadores: number;
    en_riesgo: number;
    pct_saludable: number | null;
  };
  distribucion_nivel: Array<{ nivel: string; cantidad: number; porcentaje: number; color: string }>;
  tipo_proceso_cards: CMIProcesoTipoCard[];
  proceso_bars: CMIProcesoBar[];
  catalog_charts: {
    periodicidad: Array<{ label: string; count: number }>;
    tipo_indicador: Array<{ label: string; count: number }>;
  };
  procesos_detalle: CMIProcesoDetalle[];
  unidades_detalle: CMIUnidadDetalle[];
  indicadores_summary: Record<string, number>;
  indicadores: Indicator[];
  alertas: {
    peligro: number;
    alerta: number;
    items: Indicator[];
  };
  variacion: {
    mejoraron: ResumenTrendItem[];
    empeoraron: ResumenTrendItem[];
    top_riesgo_procesos: Array<{
      proceso: string;
      n_riesgo: number;
      cumplimiento: number | null;
    }>;
  };
  meta: {
    base_anio: number;
    base_mes: number | null;
    latest_month_global: number;
  };
  analisis_avanzado: CMIProcesosAnalisisAvanzado;
  calidad: CMICalidadDashboard;
  vista_global: CMIProcesosVistaGlobal;
  ejecucion_variacion: {
    positiva: Array<{ indicador: string; ejecucion: number | null; delta: number; periodo: string }>;
    negativa: Array<{ indicador: string; ejecucion: number | null; delta: number; periodo: string }>;
  };
}

export interface CMICalidadDashboard {
  disponible: boolean;
  mensaje: string | null;
  score_global: number | null;
  dim_scores: Record<string, number>;
  dim_colors: Record<string, string>;
  kpis: {
    total_registros: number;
    total_subprocesos: number;
    promedio: number | null;
  };
  por_proceso: Array<{
    Proceso: string;
    registros: number;
    subprocesos: number;
    pct_calidad: number;
    cumple: number;
    parcial: number;
    no_cumple: number;
  }>;
  por_subproceso: Array<{
    Proceso: string;
    Subproceso: string;
    registros: number;
    pct_calidad: number;
  }>;
  alertas_dim: Array<{ dimension: string; score: number; color: string }>;
  registros: Array<{
    proceso: string;
    subproceso: string;
    tematica: string;
    pct_calidad: number | null;
    estado: string;
    criterios: Record<string, string>;
  }>;
}

export interface CMIProcesosAnalisisAvanzado {
  propuesta_accion: {
    proceso: string;
    plan_mejoramiento: string;
    pdi: string;
    sga: string;
    retos: string;
    top_criticos: Array<{
      indicador: string;
      proceso: string;
      cumplimiento: number | null;
    }>;
  };
  variacion_procesos: {
    mejoraron: Array<{ name: string; change: number }>;
    empeoraron: Array<{ name: string; change: number }>;
  };
  insights: {
    mejora_proceso: string;
    riesgo_proceso: string;
  };
  narrativa_proceso: {
    titulo: string;
    estado_color: string;
    foco_urgente: string;
    directrices: string[];
    texto_html: string;
    fuente: string;
  };
  variacion_indicadores: {
    mejoraron: ResumenTrendItem[];
    empeoraron: ResumenTrendItem[];
    top_riesgo_procesos: Array<{
      proceso: string;
      n_riesgo: number;
      cumplimiento: number | null;
    }>;
  };
  historico_indicadores: Array<{
    id: string;
    indicador: string;
    puntos: Array<{ periodo: string; cumplimiento: number }>;
  }>;
}

export interface CMIProcesosFichaIndicador extends Indicator {
  proceso_padre?: string;
  subproceso_final?: string;
  unidad?: string;
  tipo_proceso?: string;
  tipo_proceso_color?: string;
  tendencia?: string;
  narrativa_ia?: {
    diagnostico: string;
    riesgo: string;
    recomendacion: string;
    texto_html: string;
    fuente: string;
  };
  historico?: Array<{
    periodo: string;
    meta?: number;
    ejecucion?: number;
    cumplimiento?: number;
  }>;
  Descripcion?: string;
}

export interface CMIAlertasResponse {
  anio: number | null;
  mes?: number | null;
  total: number;
  peligro?: number;
  alerta?: number;
  alertas: Indicator[];
}

export interface CMIFiltrosResponse {
  anios: number[];
  anio_default: number;
  corte_default: string;
  cortes: string[];
}

export interface CMIInsight {
  tipo: string;
  titulo: string;
  mensaje: string;
}

export interface CMIVistaRapidaLinea {
  linea: string;
  linea_display?: string;
  linea_key: string;
  color: string;
  cumplimiento: number;
  estado: string;
  estado_color: string;
  estado_label?: string;
  estado_icon?: string;
  estado_bg?: string;
  estado_text?: string;
  progress_meta_label?: string;
  progress_width?: number;
  total_indicadores: number;
  n_objetivos: number;
  n_sobrecumplimiento: number;
  n_cumplimiento: number;
  n_alerta: number;
  n_riesgo: number;
  tiene_datos: boolean;
}

export interface CMILineaNarrativa {
  titulo: string;
  estado: string;
  estado_color: string;
  estado_icon: string;
  foco_urgente: string;
  directrices: string[];
  texto_html: string;
  fuente: string;
}

export interface CMILineaAnalisis {
  historico: Array<{ periodo: string; cumplimiento: number }>;
  cumplimiento_actual: number;
  cumplimiento_anterior: number | null;
  variacion_pp: number | null;
  periodo_comparacion: string;
  mejoraron: Array<{ indicador: string; variacion: number; positive?: boolean }>;
  empeoraron: Array<{ indicador: string; variacion: number; positive?: boolean }>;
  indicadores_riesgo: Indicator[];
  narrativa: CMILineaNarrativa;
}

export interface CMILineaDetalle {
  linea: string;
  linea_key: string;
  color: string;
  cumplimiento_promedio: number;
  total_indicadores: number;
  n_objetivos: number;
  n_metas: number;
  n_sobrecumplimiento: number;
  n_cumplimiento: number;
  n_alerta: number;
  n_riesgo: number;
  top_indicadores: Array<{
    Indicador?: string;
    cumplimiento_pct?: number;
    "Nivel de cumplimiento"?: string;
  }>;
  objetivos: Array<{
    objetivo: string;
    metas: Array<{
      meta: string | null;
      indicadores: Indicator[];
    }>;
  }>;
  historico: Array<{ periodo: string; cumplimiento: number }>;
  analisis?: CMILineaAnalisis;
}

export interface CMIDashboardResponse {
  anio: number;
  mes: number;
  corte: string;
  anios_disponibles: number[];
  cortes: string[];
  total_indicadores: number;
  kpis: {
    total: number;
    con_dato: number;
    promedio: number;
    top_nivel: string;
    en_riesgo: number;
    conteo_estados: Record<string, number>;
  };
  cumplimiento_por_linea: Array<{ linea: string; cumplimiento: number; color: string }>;
  distribucion_nivel: Array<{ nivel: string; cantidad: number; porcentaje: number; color: string }>;
  vista_rapida_lineas: CMIVistaRapidaLinea[];
  insights: CMIInsight[];
  lineas_detalle: CMILineaDetalle[];
  indicadores: Indicator[];
  alertas: {
    peligro: number;
    alerta: number;
    items: Indicator[];
  };
}

export interface CMIFichaIndicador extends Indicator {
  Descripcion?: string;
  historico?: Array<{
    periodo: string;
    meta?: number;
    ejecucion?: number;
    cumplimiento?: number;
  }>;
  linea_color?: string;
  tendencia?: string;
  "Responsable del calculo"?: string;
  "Fuente V1"?: string;
  Formula?: string;
  Frecuencia?: string;
  narrativa_ia?: {
    diagnostico: string;
    riesgo: string;
    recomendacion: string;
    texto_html: string;
    fuente: string;
  };
}

export interface RegistroOM {
  id: number;
  id_indicador: string;
  nombre_indicador?: string;
  proceso?: string;
  periodo?: string;
  anio?: number;
  sede?: string;
  tiene_om: number;
  tipo_accion?: string;
  numero_om?: string;
  comentario?: string;
  registrado_por?: string;
  fecha_registro?: string;
}

export interface DevTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface SunburstNode {
  id: string;
  label: string;
  parent: string;
  value: number;
  color?: string;
}

export interface YoYRow {
  linea: string;
  anio_actual: number;
  cumplimiento_actual: number | null;
  cumplimiento_anterior: number | null;
  variacion_pp: number | null;
  en_riesgo: number;
}

export interface NarrativaResponse {
  titulo: string;
  parrafos: string[];
}

export interface DashboardFiltrosResponse {
  anios: number[];
  periodos: string[];
  anio_default: number | null;
  vistas: string[];
}

export interface ResumenChip {
  value: number | string;
  label: string;
  color: string;
}

export interface ResumenFicha {
  linea: string;
  icon: string;
  color: string;
  count: number;
  cumplimiento: number;
  unit_label: string;
  historico: { anio: number; cumplimiento: number }[];
  n_indicadores?: number;
  n_proyectos?: number;
  n_retos?: number;
}

export interface ResumenSunburst {
  ids?: string[];
  labels: string[];
  parents: string[];
  values: number[];
  colors: string[];
  text: string[];
  customdata?: number[][];
}

export interface ResumenNarrativa {
  texto: string;
  estado_color: string;
  estado_icon: string;
  health_rate?: number;
}

export interface ResumenTrendItem {
  indicador: string;
  linea: string;
  linea_color: string;
  variacion: number;
  positive: boolean;
}

export interface ProyectoGanttItem {
  id: string;
  nombre: string;
  linea: string;
  linea_color: string;
  anio_inicio: number;
  anio_fin: number;
  duracion_anios: number;
  anios_activos: number[];
  cumplimiento: number;
  estado: string;
}

export interface ProyectosGanttData {
  anio_min: number;
  anio_max: number;
  items: ProyectoGanttItem[];
}

export interface ResumenCompletoResponse {
  anio: number;
  vista: string;
  chips: ResumenChip[];
  fichas: ResumenFicha[];
  sunburst: ResumenSunburst;
  narrativa: ResumenNarrativa;
  mejoraron: ResumenTrendItem[];
  en_riesgo: ResumenTrendItem[];
  periodo_comparacion: string;
  gantt_proyectos?: ProyectosGanttData;
  total_indicadores: number;
  tabla_detalle?: Array<{
    linea: string;
    id?: string;
    nombre?: string;
    cumplimiento: number;
    estado?: string;
    nivel: string;
  }>;
}

export interface SeguimientoDashboardResponse {
  error?: string;
  filtros: {
    anios: number[];
    anio_default: number | null;
    meses: number[];
    mes_default: number;
    meses_nombres: string[];
    procesos: string[];
    estados: string[];
  };
  filtros_aplicados: Record<string, string | number | null>;
  kpis: { registros: number; reportados: number; pendientes: number; no_aplica: number };
  alertas: {
    vencidos_total: number;
    por_vencer_total: number;
    vencidos: Array<Record<string, string | number | null>>;
    por_vencer: Array<Record<string, string | number | null>>;
  };
  estado_por_proceso: Array<{
    proceso: string;
    estados: Array<{ estado: string; cantidad: number; color: string }>;
  }>;
  detalle: Array<Record<string, string | number | null>>;
  estado_colores: Record<string, string>;
}

export interface PlanMejoramientoDashboardResponse {
  error?: string;
  anio: number;
  mes: number;
  corte: string;
  filtros_corte: { anios: number[]; anio_default: number | null; corte_default: string; cortes: string[] };
  filtros_cna: { factores: string[]; caracteristicas: string[] };
  filtros_aplicados: Record<string, string | number>;
  kpis: {
    indicadores_cna: number;
    factores_visibles: number;
    caracteristicas_visibles: number;
    con_cumplimiento: number;
    promedio_cumplimiento: number;
    catalogo_factores: number;
    catalogo_caracteristicas: number;
  };
  graficos: {
    factor_bars: Array<{ factor: string; cumplimiento: number | null; color: string }>;
    nivel_donut: Array<{ nivel: string; cantidad: number; color: string; emoji: string }>;
    factor_nivel_stacked: Array<{ factor: string; niveles: Array<{ nivel: string; cantidad: number; color: string }>; color: string }>;
    treemap: Array<{ factor: string; cantidad: number; children: Array<{ caracteristica: string; cantidad: number }>; color: string }>;
  };
  tabla_cna: Array<Record<string, string | number | null>>;
  acciones: {
    kpis: Record<string, number>;
    avance_por_estado: Array<{ estado: string; avance: number | null }>;
    tabla: Array<Record<string, string | number | null>>;
  };
  total_indicadores: number;
}

export interface OMMatrizResponse {
  error?: string;
  anio: number;
  mes: string;
  filtros: {
    anios: string[];
    anio_default: string;
    meses: string[];
    mes_default: string;
    procesos: string[];
    subprocesos: string[];
  };
  filtros_aplicados: Record<string, string | number | boolean>;
  kpis: {
    peligro: number;
    alerta: number;
    con_om: number;
    total: number;
    avance_om_promedio: number | null;
  };
  filas: Array<{
    id: string;
    indicador: string;
    proceso: string;
    subproceso: string;
    periodicidad: string;
    meta: number | null;
    ejecucion: number | null;
    cumplimiento_pct: number | null;
    categoria: string;
    categoria_color: string;
    tipo_accion: string;
    tipo_accion_color: string;
    tiene_om: number;
    numero_om: string;
    comentario: string;
    om_id: number | null;
    avance_om: number | null;
    row_bg: string;
  }>;
  tipo_accion_colores: Record<string, string>;
}

export interface InformeDashboardResponse extends CMIProcesosDashboardResponse {
  resumen_ejecutivo: {
    score: number;
    avg: number;
    label: string;
    total_indicadores: number;
    cumple: number;
    alerta: number;
    peligro: number;
    sin_dato: number;
    delta: number | null;
  };
  comparativa_interanual: Array<{ anio: number; cumplimiento: number }>;
  criticos: Array<Record<string, unknown>>;
  distribucion_estado: { cumple: number; alerta: number; critico: number; sin_dato: number };
  propuestas: Array<{
    proceso: string;
    subproceso: string;
    indicador: string;
    fuente: string;
    style: Record<string, string>;
  }>;
  propuestas_error: string | null;
  auditoria: Array<{
    tipo: string;
    titulo: string;
    fichas: Array<{
      proceso: string;
      categorias: Array<{
        campo: string;
        label: string;
        valor: string;
        items: string[];
        pill_bg: string;
        pill_text: string;
        dot_color: string;
        emoji: string;
      }>;
    }>;
  }>;
  auditoria_error: string | null;
  analisis_ia: {
    conteos: { peligro: number; alerta: number; saludables: number };
    top_peligro: Array<Record<string, unknown>>;
    top_alerta: Array<Record<string, unknown>>;
    mostrados_peligro: number;
    mostrados_alerta: number;
  };
}

export interface PDIDashboardResponse {
  error: string | null;
  filtros: {
    estados: string[];
    macros: string[];
    horizontes: string[];
    horizonte_default: string;
  };
  filtros_aplicados: Record<string, string>;
  kpis: {
    total: number;
    cumplimiento_promedio: number | null;
    brecha_promedio: number | null;
  };
  treemap: Array<{
    id: string;
    label: string;
    parent: string;
    value: number;
    color?: string;
    color_value?: number | null;
  }>;
  benchmark: Array<{
    proceso: string;
    cumplimiento: number;
    benchmark: number;
  }>;
  evolucion_brechas: Array<{
    periodo: string;
    proceso: string;
    brecha: number;
  }>;
  tabla: Array<Record<string, string | number | null>>;
}

export interface RegistroOMCreate {
  id_indicador: string;
  nombre_indicador?: string;
  proceso?: string;
  periodo?: string;
  anio?: number;
  tiene_om?: number;
  tipo_accion?: string;
  numero_om?: string;
  comentario?: string;
}

export interface RegistroOMUpdate {
  nombre_indicador?: string;
  proceso?: string;
  periodo?: string;
  anio?: number;
  sede?: string;
  tiene_om?: number;
  tipo_accion?: string;
  numero_om?: string;
  comentario?: string;
}

export interface RegistroOMCerrar {
  comentario?: string;
}

export interface OMPlanAccionActividad {
  id_accion: string;
  accion: string;
  responsable: string;
  avance: string;
  estado_plan: string;
  estado_om: string;
}
