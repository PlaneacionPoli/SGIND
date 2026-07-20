import axios from "axios";
import type {
  CMIAlertasResponse,
  CMIDashboardResponse,
  CMIEstrategicoResponse,
  CMIFichaIndicador,
  CMIFiltrosResponse,
  CMILinea,
  CMIProcesosDashboardResponse,
  CMIProcesosFichaIndicador,
  CMIProcesosFiltrosResponse,
  CMIProcesosResponse,
  DashboardFiltrosResponse,
  DashboardKPIsResponse,
  DevTokenResponse,
  HealthResponse,
  IndicatorListResponse,
  NarrativaResponse,
  InformeDashboardResponse,
  OMMatrizResponse,
  PDIDashboardResponse,
  PlanMejoramientoDashboardResponse,
  RegistroOM,
  RegistroOMCerrar,
  RegistroOMCreate,
  RegistroOMUpdate,
  SeguimientoDashboardResponse,
  ResumenCompletoResponse,
  SemaphoreItem,
  SunburstNode,
  TrendItem,
  YoYRow,
} from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

export function setAuthToken(token: string | null) {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common.Authorization;
  }
}

// Interceptor: 401 → limpiar sesión y redirigir a /login
api.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (
      typeof error === "object" &&
      error !== null &&
      "response" in error &&
      (error as { response?: { status?: number } }).response?.status === 401
    ) {
      // Importar dinámicamente para evitar dependencias circulares SSR
      if (typeof window !== "undefined") {
        import("@/stores/auth-store").then(({ useAuthStore }) => {
          useAuthStore.getState().clearSession();
          window.location.replace("/login");
        });
      }
    }
    return Promise.reject(error);
  }
);

export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>("/health");
  return data;
}

export async function fetchDevToken(
  email = "dev@poligran.edu.co",
  role = "calidad"
): Promise<DevTokenResponse> {
  const { data } = await api.post<DevTokenResponse>("/auth/dev-token", undefined, {
    params: { email, role },
  });
  return data;
}

export async function fetchKPIs(params?: {
  anio?: number;
  periodo?: string;
  vista?: string;
}): Promise<DashboardKPIsResponse["kpis"]> {
  const { data } = await api.get<DashboardKPIsResponse>("/dashboard/kpis", { params });
  return data.kpis;
}

export async function fetchSemaphore(params?: {
  anio?: number;
  periodo?: string;
  vista?: string;
}): Promise<SemaphoreItem[]> {
  const { data } = await api.get<SemaphoreItem[]>("/dashboard/semaphore", { params });
  return data;
}

export async function fetchTrend(params?: { anio?: number; vista?: string }): Promise<TrendItem[]> {
  const { data } = await api.get<TrendItem[]>("/dashboard/trend", { params });
  return data;
}

export async function fetchResumenCompleto(params: {
  anio: number;
  vista?: string;
  rango?: boolean;
}): Promise<ResumenCompletoResponse> {
  const { data } = await api.get<ResumenCompletoResponse>("/dashboard/resumen-completo", { params });
  return data;
}

export async function fetchDashboardFiltros(): Promise<DashboardFiltrosResponse> {
  const { data } = await api.get<DashboardFiltrosResponse>("/dashboard/filtros");
  return data;
}

export async function fetchDashboardLineas(params?: {
  anio?: number;
  periodo?: string;
  vista?: string;
}): Promise<CMILinea[]> {
  const { data } = await api.get<CMILinea[]>("/dashboard/lineas", { params });
  return data;
}

export async function fetchSunburst(params?: {
  anio?: number;
  vista?: string;
}): Promise<SunburstNode[]> {
  const { data } = await api.get<SunburstNode[]>("/dashboard/sunburst", { params });
  return data;
}

export async function fetchYoY(params: { anio: number; vista?: string }): Promise<YoYRow[]> {
  const { data } = await api.get<YoYRow[]>("/dashboard/yoy", { params });
  return data;
}

export async function fetchNarrativa(params?: {
  anio?: number;
  vista?: string;
}): Promise<NarrativaResponse> {
  const { data } = await api.get<NarrativaResponse>("/dashboard/narrativa", { params });
  return data;
}

export async function fetchIndicators(params?: {
  anio?: number;
  periodo?: string;
  proceso?: string;
  categoria?: string;
  vista?: string;
  limit?: number;
  offset?: number;
}): Promise<IndicatorListResponse> {
  const { data } = await api.get<IndicatorListResponse>("/indicators", { params });
  return data;
}

export async function fetchCMIFiltros(): Promise<CMIFiltrosResponse> {
  const { data } = await api.get<CMIFiltrosResponse>("/cmi/filtros");
  return data;
}

export async function fetchCMIDashboard(params: {
  anio: number;
  corte?: string;
  mes?: number;
}): Promise<CMIDashboardResponse> {
  const { data } = await api.get<CMIDashboardResponse>("/cmi/estrategico-dashboard", { params });
  return data;
}

export async function fetchCMIFicha(
  indicadorId: string,
  params: { anio: number; corte?: string; mes?: number }
): Promise<CMIFichaIndicador> {
  const { data } = await api.get<CMIFichaIndicador>(`/cmi/indicador/${indicadorId}`, { params });
  return data;
}

export async function fetchCMIEstrategico(
  anio?: number,
  corte?: string
): Promise<CMIEstrategicoResponse> {
  const { data } = await api.get<CMIEstrategicoResponse>("/cmi/estrategico", {
    params: { anio, corte },
  });
  return data;
}

export async function fetchCMIProcesosFiltros(anio?: number): Promise<CMIProcesosFiltrosResponse> {
  const { data } = await api.get<CMIProcesosFiltrosResponse>("/cmi/procesos/filtros", {
    params: anio ? { anio } : undefined,
  });
  return data;
}

export async function fetchCMIProcesosDashboard(params: {
  anio: number;
  mes?: number;
  unidad?: string;
  proceso?: string;
  subproceso?: string;
  clasificacion?: string;
  frecuencia?: string;
}): Promise<CMIProcesosDashboardResponse> {
  const { data } = await api.get<CMIProcesosDashboardResponse>("/cmi/procesos-dashboard", { params });
  return data;
}

export async function fetchCMIProcesosFicha(
  indicadorId: string,
  params: {
    anio: number;
    mes?: number;
    unidad?: string;
    proceso?: string;
    subproceso?: string;
  }
): Promise<CMIProcesosFichaIndicador> {
  const { data } = await api.get<CMIProcesosFichaIndicador>(`/cmi/procesos/indicador/${indicadorId}`, {
    params,
  });
  return data;
}

export async function downloadCMIProcesosExport(params: {
  anio: number;
  mes?: number;
  formato?: "xlsx" | "csv";
  unidad?: string;
  proceso?: string;
  subproceso?: string;
  clasificacion?: string;
  frecuencia?: string;
}): Promise<void> {
  const formato = params.formato ?? "xlsx";
  const response = await api.get("/cmi/procesos/export", {
    params: { ...params, formato },
    responseType: "blob",
  });
  const contentType = String(response.headers["content-type"] ?? "application/octet-stream");
  const blob = new Blob([response.data], { type: contentType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `cmi_procesos_${params.anio}_${params.mes ?? 12}.${formato === "csv" ? "csv" : "xlsx"}`;
  link.click();
  URL.revokeObjectURL(url);
}

export async function fetchCMIProcesos(anio?: number): Promise<CMIProcesosResponse> {
  const { data } = await api.get<CMIProcesosResponse>("/cmi/procesos", {
    params: anio ? { anio } : undefined,
  });
  return data;
}

export async function fetchCMIAlertas(
  anio?: number,
  limit = 20,
  corte?: string
): Promise<CMIAlertasResponse> {
  const { data } = await api.get<CMIAlertasResponse>("/cmi/alertas", {
    params: { anio, limit, corte },
  });
  return data;
}

export async function fetchOM(params?: {
  anio?: number;
  periodo?: string;
}): Promise<RegistroOM[]> {
  const { data } = await api.get<RegistroOM[]>("/om", { params });
  return data;
}

export async function fetchOMMatriz(params: {
  anio: number;
  mes?: string;
  proceso?: string;
  subproceso?: string;
  mostrar_alerta?: boolean;
}): Promise<OMMatrizResponse> {
  const { data } = await api.get<OMMatrizResponse>("/om/matriz", { params });
  return data;
}

export async function createOM(payload: RegistroOMCreate): Promise<RegistroOM> {
  const { data } = await api.post<RegistroOM>("/om", payload);
  return data;
}

export async function updateOM(id: number, payload: RegistroOMUpdate): Promise<RegistroOM> {
  const { data } = await api.put<RegistroOM>(`/om/${id}`, payload);
  return data;
}

export async function cerrarOM(id: number, payload?: RegistroOMCerrar): Promise<RegistroOM> {
  const { data } = await api.patch<RegistroOM>(`/om/${id}/cerrar`, payload ?? {});
  return data;
}

export async function deleteOM(id: number): Promise<void> {
  await api.delete(`/om/${id}`);
}

export async function fetchSeguimientoDashboard(params?: {
  anio?: number;
  mes?: number;
  proceso?: string;
  estado?: string;
}): Promise<SeguimientoDashboardResponse> {
  const { data } = await api.get<SeguimientoDashboardResponse>("/seguimiento/dashboard", { params });
  return data;
}

export async function downloadSeguimientoExport(params?: {
  anio?: number;
  mes?: number;
  proceso?: string;
  estado?: string;
}): Promise<void> {
  const response = await api.get("/seguimiento/export", { params, responseType: "blob" });
  const blob = new Blob([response.data], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "seguimiento_filtrado.xlsx";
  link.click();
  URL.revokeObjectURL(url);
}

export async function fetchPlanMejoramientoDashboard(params?: {
  anio?: number;
  corte?: string;
  factor?: string;
  caracteristica?: string;
  nombre?: string;
}): Promise<PlanMejoramientoDashboardResponse> {
  const { data } = await api.get<PlanMejoramientoDashboardResponse>("/plan-mejoramiento/dashboard", { params });
  return data;
}

export async function fetchInformeDashboard(params: {
  anio: number;
  mes?: number;
  unidad?: string;
  proceso?: string;
  subproceso?: string;
  clasificacion?: string;
  frecuencia?: string;
}): Promise<InformeDashboardResponse> {
  const { data } = await api.get<InformeDashboardResponse>("/informe/dashboard", { params });
  return data;
}

export async function fetchPDIDashboard(params?: {
  estado?: string;
  macro?: string;
  horizonte?: string;
}): Promise<PDIDashboardResponse> {
  const { data } = await api.get<PDIDashboardResponse>("/pdi/dashboard", { params });
  return data;
}

// ── PDF download helpers ──────────────────────────────────────────────────────

async function _downloadPdf(url: string, filename: string): Promise<void> {
  const response = await api.get(url, { responseType: "blob" });
  const blob = new Blob([response.data], { type: "application/pdf" });
  const href = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = href;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(href);
}

export async function downloadResumenGeneralPdf(anio: number): Promise<void> {
  await _downloadPdf(
    `/reports/resumen-general?anio=${anio}`,
    `resumen_general_${anio}.pdf`,
  );
}

export async function downloadInformeProcesosPdf(params: {
  anio: number;
  mes?: number;
  proceso?: string;
}): Promise<void> {
  const { anio, mes = 12, proceso } = params;
  const qs = new URLSearchParams({ anio: String(anio), mes: String(mes) });
  if (proceso && proceso !== "Todos") qs.set("proceso", proceso);
  const procesoSlug = (proceso ?? "todos").toLowerCase().replace(/\s+/g, "_").slice(0, 30);
  await _downloadPdf(
    `/reports/informe-procesos?${qs.toString()}`,
    `informe_procesos_${anio}_${String(mes).padStart(2, "0")}_${procesoSlug}.pdf`,
  );
}

export async function downloadFichaIndicadorPdf(
  indicadorId: string,
  params: {
    anio: number;
    mes?: number;
    corte?: string;
    origen?: "estrategico" | "procesos";
    unidad?: string;
    proceso?: string;
    subproceso?: string;
  },
): Promise<void> {
  const { anio, mes, corte, origen = "estrategico", unidad, proceso, subproceso } = params;
  const qs = new URLSearchParams({ anio: String(anio), origen });
  if (mes != null) qs.set("mes", String(mes));
  if (corte) qs.set("corte", corte);
  if (unidad && unidad !== "Todos") qs.set("unidad", unidad);
  if (proceso && proceso !== "Todos") qs.set("proceso", proceso);
  if (subproceso && subproceso !== "Todos") qs.set("subproceso", subproceso);
  await _downloadPdf(
    `/reports/ficha/${indicadorId}?${qs.toString()}`,
    `ficha_${indicadorId}_${anio}.pdf`,
  );
}
