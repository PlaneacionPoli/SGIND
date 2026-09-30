"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  LayoutDashboard,
  Activity,
  ShieldCheck,
  ClipboardCheck,
  Lightbulb,
  Brain,
  FileDown,
  Trophy,
  Zap,
  AlertTriangle,
} from "lucide-react";
import { CmiAuditoriaTab } from "@/components/cmi/CmiAuditoriaTab";
import { CmiProcesosCalidadSection } from "@/components/cmi/CmiProcesosCalidadSection";
import { CmiProcesosAnalisisTab } from "@/components/cmi/CmiProcesosAnalisisTab";
import { DataFreshnessFooter } from "@/components/layout/DataFreshnessFooter";
import { CmiProcesosFichaModal } from "@/components/cmi/CmiProcesosFichaModal";
import { CmiProcesosFilters } from "@/components/cmi/CmiProcesosFilters";
import { CmiProcesosListadoTab } from "@/components/cmi/CmiProcesosListadoTab";
import { fmtPct, NIVEL_STYLES } from "@/components/cmi/nivelUtils";
import {
  downloadFichaIndicadorPdf,
  downloadInformeProcesosPdf,
  fetchCMIProcesosFicha,
  fetchCMIProcesosFiltros,
  fetchInformeDashboard,
} from "@/lib/api";
import type { InformeDashboardResponse } from "@/lib/types";
import { useAuthReady } from "@/stores/auth-store";

const TABS = [
  { id: "resumen", label: "Resumen Ejecutivo", icon: LayoutDashboard },
  { id: "indicadores", label: "Indicadores", icon: Activity },
  { id: "calidad", label: "Calidad de Datos", icon: ShieldCheck },
  { id: "auditoria", label: "Auditoría", icon: ClipboardCheck },
  { id: "propuestas", label: "Propuestas", icon: Lightbulb, hidden: true },
  { id: "ia", label: "Análisis IA", icon: Brain },
] as const;

const VISIBLE_TABS = TABS.filter((t) => !("hidden" in t && t.hidden));

type TabId = (typeof TABS)[number]["id"];

const YEAR_BAR_COLORS = ["#1a2b4a", "#2563eb", "#7c3aed", "#0d9488", "#c9a227"];

const SCORE_LABEL_STYLES: Record<string, { border: string; bg: string; text: string; pill: string }> = {
  Saludable: { border: "border-emerald-300", bg: "bg-emerald-50/40", text: "text-emerald-900", pill: "bg-emerald-500" },
  Estable: { border: "border-amber-300", bg: "bg-amber-50/40", text: "text-amber-900", pill: "bg-amber-500" },
  "En riesgo": { border: "border-red-300", bg: "bg-red-50/40", text: "text-red-900", pill: "bg-red-600" },
};

export default function InformeProcesosPage() {
  return (
    <Suspense fallback={<p className="text-sm text-slate-500">Cargando informe…</p>}>
      <InformeContent />
    </Suspense>
  );
}

function InformeContent() {
  const { isAuthenticated } = useAuthReady();
  const [anio, setAnio] = useState<number | null>(null);
  const [mes, setMes] = useState<number | null>(null);
  const [unidad, setUnidad] = useState("Todos");
  const [proceso, setProceso] = useState("Todos");
  const [subproceso, setSubproceso] = useState("Todos");
  const [clasificacion, setClasificacion] = useState("Todos");
  const [frecuencia, setFrecuencia] = useState("Todos");
  const [tab, setTab] = useState<TabId>("resumen");
  const [fichaId, setFichaId] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [downloadingFichaPdf, setDownloadingFichaPdf] = useState(false);

  const filtrosQuery = useQuery({
    queryKey: ["informe-filtros", anio, mes],
    queryFn: () => fetchCMIProcesosFiltros(anio ?? undefined, mes ?? undefined),
    enabled: isAuthenticated,
  });

  useEffect(() => {
    if (anio == null && filtrosQuery.data?.anio_default) {
      setAnio(filtrosQuery.data.anio_default);
      setMes(filtrosQuery.data.mes_default);
    }
  }, [anio, filtrosQuery.data]);

  const anioEff = anio ?? filtrosQuery.data?.anio_default ?? new Date().getFullYear();
  const mesEff = mes ?? filtrosQuery.data?.mes_default ?? 12;

  const subprocesosFiltrados: string[] =
    proceso !== "Todos" && filtrosQuery.data?.subprocesos_por_proceso
      ? (filtrosQuery.data.subprocesos_por_proceso[proceso] ?? [])
      : (filtrosQuery.data?.subprocesos ?? []);

  const dashQuery = useQuery({
    queryKey: ["informe-dashboard", anioEff, mesEff, unidad, proceso, subproceso, clasificacion, frecuencia],
    queryFn: () =>
      fetchInformeDashboard({
        anio: anioEff,
        mes: mesEff,
        unidad: unidad !== "Todos" ? unidad : undefined,
        proceso: proceso !== "Todos" ? proceso : undefined,
        subproceso: subproceso !== "Todos" ? subproceso : undefined,
        clasificacion: clasificacion !== "Todos" ? clasificacion : undefined,
        frecuencia: frecuencia !== "Todos" ? frecuencia : undefined,
      }),
    enabled: isAuthenticated && anioEff > 0,
  });

  const fichaQuery = useQuery({
    queryKey: ["informe-ficha", fichaId, anioEff, mesEff],
    queryFn: () =>
      fetchCMIProcesosFicha(fichaId!, {
        anio: anioEff,
        mes: mesEff,
        unidad: unidad !== "Todos" ? unidad : undefined,
        proceso: proceso !== "Todos" ? proceso : undefined,
        subproceso: subproceso !== "Todos" ? subproceso : undefined,
      }),
    enabled: !!fichaId && isAuthenticated,
  });

  const data = dashQuery.data;
  const resumen = data?.resumen_ejecutivo;

  const handleReset = useCallback(() => {
    if (filtrosQuery.data) {
      setAnio(filtrosQuery.data.anio_default);
      setMes(filtrosQuery.data.mes_default);
    }
    setUnidad("Todos");
    setProceso("Todos");
    setSubproceso("Todos");
    setClasificacion("Todos");
    setFrecuencia("Todos");
  }, [filtrosQuery.data]);

  async function handleDownloadPdf() {
    setPdfLoading(true);
    try {
      await downloadInformeProcesosPdf({
        anio: anioEff,
        mes: mesEff,
        proceso: proceso !== "Todos" ? proceso : undefined,
      });
    } finally {
      setPdfLoading(false);
    }
  }

  async function handleDownloadFichaPdf() {
    if (!fichaId) return;
    setDownloadingFichaPdf(true);
    try {
      await downloadFichaIndicadorPdf(fichaId, {
        anio: anioEff,
        mes: mesEff,
        origen: "procesos",
        unidad: unidad !== "Todos" ? unidad : undefined,
        proceso: proceso !== "Todos" ? proceso : undefined,
        subproceso: subproceso !== "Todos" ? subproceso : undefined,
      });
    } finally {
      setDownloadingFichaPdf(false);
    }
  }

  const tabCounts: Partial<Record<TabId, string>> = {
    indicadores: data ? String(data.indicadores.length) : undefined,
    calidad: data?.calidad.score_global != null ? `${Math.round(data.calidad.score_global)}%` : undefined,
    propuestas: data?.propuestas.length ? String(data.propuestas.length) : undefined,
  } as Partial<Record<TabId, string>>;

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 pb-2 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="mb-1 flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-poli-navy px-2.5 py-0.5 text-[11px] font-bold text-white shadow-sm">
              SIGP Institucional
            </span>
            {resumen && (
              <span className="flex items-center gap-1.5 rounded-full border border-emerald-300 bg-emerald-100 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-800">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-600" />
                Corte vigente: {anioEff}
                {filtrosQuery.data?.meses_nombres?.[mesEff - 1] ? ` (${filtrosQuery.data.meses_nombres[mesEff - 1]})` : ""}
              </span>
            )}
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-900">Informe por Procesos</h2>
          <p className="mt-0.5 text-sm text-slate-600">
            Resumen ejecutivo, indicadores, calidad, auditoría, propuestas y análisis heurístico.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          {proceso !== "Todos" && (
            <span className="inline-flex items-center gap-2 rounded-xl border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-900 shadow-sm">
              <span className="h-2 w-2 animate-pulse rounded-full bg-poli-navy" />
              Proceso: {proceso}
            </span>
          )}
          {isAuthenticated && (
            <button
              type="button"
              onClick={handleDownloadPdf}
              disabled={pdfLoading || dashQuery.isLoading}
              className="flex shrink-0 items-center gap-1.5 rounded-xl bg-poli-navy px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-poli-navy-700 disabled:opacity-50"
            >
              <FileDown className="h-4 w-4" />
              {pdfLoading ? "Generando…" : "Descargar PDF"}
            </button>
          )}
        </div>
      </div>

      {!isAuthenticated ? (
        <p className="text-sm text-amber-700">Inicie sesión para ver el informe.</p>
      ) : (
        <>
          {isAuthenticated && filtrosQuery.data && anio != null && mes != null && (
            <div className="space-y-3">
              <CmiProcesosFilters
                anio={anioEff}
                mes={mesEff}
                anios={filtrosQuery.data.anios}
                meses={filtrosQuery.data.meses}
                mesesNombres={filtrosQuery.data.meses_nombres}
                unidades={filtrosQuery.data.unidades}
                procesos={filtrosQuery.data.procesos}
                subprocesos={subprocesosFiltrados}
                clasificaciones={filtrosQuery.data.clasificaciones}
                frecuencias={filtrosQuery.data.frecuencias}
                unidad={unidad}
                proceso={proceso}
                subproceso={subproceso}
                clasificacion={clasificacion}
                frecuencia={frecuencia}
                onAnioChange={setAnio}
                onMesChange={setMes}
                onUnidadChange={setUnidad}
                onProcesoChange={(v) => { setProceso(v); setSubproceso("Todos"); }}
                onSubprocesoChange={setSubproceso}
                onClasificacionChange={setClasificacion}
                onFrecuenciaChange={setFrecuencia}
                onReset={handleReset}
              />
              {resumen && (
                <div className="flex flex-wrap items-center justify-end gap-2 text-xs font-semibold">
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-red-200 bg-red-100 px-2.5 py-0.5 text-red-800">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-red-600" />
                    {resumen.peligro} en peligro
                  </span>
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-100 px-2.5 py-0.5 text-amber-900">
                    <span className="h-2 w-2 rounded-full bg-amber-500" />
                    {resumen.alerta} en alerta
                  </span>
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-300 bg-emerald-100 px-2.5 py-0.5 text-emerald-800">
                    <span className="h-2 w-2 rounded-full bg-emerald-600" />
                    {resumen.cumple} saludables
                  </span>
                </div>
              )}
            </div>
          )}

          <div className="flex flex-wrap items-center gap-2 overflow-x-auto border-b border-slate-200 pb-1">
            {VISIBLE_TABS.map((t) => {
              const Icon = t.icon;
              const active = tab === t.id;
              const count = tabCounts[t.id];
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setTab(t.id)}
                  className={`flex shrink-0 items-center gap-2 rounded-t-xl px-4 py-2.5 text-sm font-semibold transition-all ${
                    active
                      ? "border-b-2 border-poli-navy bg-white text-poli-navy shadow-xs"
                      : "text-slate-500 hover:bg-slate-50 hover:text-poli-navy"
                  }`}
                >
                  <Icon className={`h-4 w-4 ${active ? "text-poli-navy" : ""}`} />
                  {t.label}
                  {count && (
                    <span
                      className={`ml-0.5 rounded-full px-1.5 py-0.5 text-[10px] font-bold shadow-xs ${
                        active ? "bg-poli-navy text-white" : "bg-slate-200 text-slate-600"
                      }`}
                    >
                      {count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {dashQuery.isLoading ? (
            <div className="h-48 animate-pulse rounded-lg bg-slate-200" />
          ) : (
            <>
              {tab === "resumen" && resumen && (
                <ResumenEjecutivoTab
                  resumen={resumen}
                  data={data ?? null}
                  proceso={proceso}
                  onVerPropuestas={() => setTab("indicadores")}
                />
              )}

              {tab === "indicadores" && data && (
                <CmiProcesosListadoTab
                  indicadores={data.indicadores}
                  summary={data.indicadores_summary}
                  onOpenFicha={setFichaId}
                />
              )}

              {tab === "calidad" && data && <CmiProcesosCalidadSection calidad={data.calidad} />}

              {tab === "auditoria" && (
                <CmiAuditoriaTab secciones={data?.auditoria ?? []} error={data?.auditoria_error ?? null} />
              )}

              {tab === "propuestas" && (
                <section className="space-y-4">
                  {data?.propuestas_error ? (
                    <p className="text-sm text-amber-700">{data.propuestas_error}</p>
                  ) : !data?.propuestas.length ? (
                    <p className="text-sm text-slate-500">No hay indicadores propuestos para el filtro.</p>
                  ) : (
                    <PropuestasGrid propuestas={data.propuestas} />
                  )}
                </section>
              )}

              {tab === "ia" && data && (
                <CmiProcesosAnalisisTab
                  data={data}
                  narrativaIaProceso={data.narrativa_ia_proceso}
                  narrativaIaPendiente={data.narrativa_ia_pendiente}
                />
              )}
            </>
          )}

          <CmiProcesosFichaModal
            ficha={fichaQuery.data ?? null}
            loading={fichaQuery.isLoading}
            onClose={() => setFichaId(null)}
            onDownloadPdf={handleDownloadFichaPdf}
            downloadingPdf={downloadingFichaPdf}
          />
        </>
      )}

      <DataFreshnessFooter />
    </div>
  );
}

type Resumen = NonNullable<InformeDashboardResponse["resumen_ejecutivo"]>;

function ResumenEjecutivoTab({
  resumen,
  data,
  proceso,
  onVerPropuestas,
}: {
  resumen: Resumen;
  data: InformeDashboardResponse | null;
  proceso: string;
  onVerPropuestas: () => void;
}) {
  const scoreStyle = SCORE_LABEL_STYLES[resumen.label] ?? SCORE_LABEL_STYLES["En riesgo"];
  const topCritico = data?.criticos?.[0] as Record<string, unknown> | undefined;
  const summary = data?.indicadores_summary ?? {};
  const comparativa = [...(data?.comparativa_interanual ?? [])].reverse();
  const maxComparativa = Math.max(100, ...comparativa.map((c) => c.cumplimiento ?? 0)) * 1.05 || 100;
  const mejora = data?.vista_global?.variacion_procesos?.mejoraron?.[0];
  const comparativaProcesos = data?.vista_global?.comparativa_procesos ?? [];
  const baseAnio = data?.meta?.base_anio;
  const baseMes = data?.meta?.base_mes;

  return (
    <div className="space-y-6">
      {topCritico && (
        <div className="flex items-start justify-between gap-4 rounded-xl border border-red-300 bg-red-50/80 p-4">
          <div className="flex items-start gap-3">
            <div className="shrink-0 rounded-lg bg-red-100 p-2 text-red-600">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-bold text-red-950">Top indicador crítico detectado</p>
              <p className="mt-0.5 text-sm text-red-800">
                <span className="font-bold">{String(topCritico.indicador ?? "—")}</span>
                {topCritico.proceso ? ` (${String(topCritico.proceso)})` : ""} — Ejecución al{" "}
                <span className="font-bold underline">{fmtPct(topCritico.cumplimiento_pct as number)}</span>{" "}
                respecto a la meta institucional.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onVerPropuestas}
            className="shrink-0 rounded-lg border border-red-300 bg-white px-3 py-1.5 text-xs font-semibold text-red-600 shadow-xs hover:bg-red-50"
          >
            Ver plan de acción
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className={`flex flex-col justify-between rounded-xl border-2 ${scoreStyle.border} ${scoreStyle.bg} bg-white p-5 shadow-sm`}>
          <div className="flex items-center justify-between">
            <span className={`text-[11px] font-bold uppercase tracking-wider ${scoreStyle.text}`}>Score de Salud</span>
            <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-bold text-white ${scoreStyle.pill}`}>
              {resumen.label}
            </span>
          </div>
          <div className={`my-3 flex items-baseline gap-1 ${scoreStyle.text}`}>
            <span className="text-3xl font-extrabold">{resumen.score}</span>
            <span className="text-sm font-bold opacity-70">/ 100</span>
          </div>
          <div className="flex items-center justify-between border-t border-black/5 pt-2 text-xs">
            {resumen.delta != null ? (
              <span className={`font-bold ${resumen.delta >= 0 ? "text-emerald-700" : "text-red-600"}`}>
                {resumen.delta >= 0 ? "+" : ""}
                {resumen.delta}% vs año anterior
              </span>
            ) : (
              <span className="text-slate-400">Sin histórico</span>
            )}
          </div>
        </div>

        <div className="flex flex-col justify-between rounded-xl border-2 border-blue-300 bg-blue-50/20 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-primary">Cumplimiento Global</span>
            <span className="rounded-full bg-poli-navy px-2.5 py-0.5 text-xs font-bold text-white">Meta: 100%</span>
          </div>
          <p className="my-3 text-3xl font-extrabold text-poli-navy">{fmtPct(resumen.avg)}</p>
          <div className="space-y-1.5 border-t border-blue-200 pt-1">
            <div className="h-2 w-full overflow-hidden rounded-full bg-blue-100">
              <div className="h-full rounded-full bg-poli-navy" style={{ width: `${Math.min(100, resumen.avg)}%` }} />
            </div>
            <p className="flex justify-between text-[11px] font-semibold text-blue-900">
              <span>Rango meta {resumen.avg >= 100 ? "alcanzado" : "en progreso"}</span>
              {resumen.avg >= 100 && (
                <span className="rounded bg-blue-100 px-1.5 py-0.5 font-bold text-poli-navy">
                  +{(resumen.avg - 100).toFixed(1)}% superávit
                </span>
              )}
            </p>
          </div>
        </div>

        <div className="flex flex-col justify-between rounded-xl border-2 border-purple-200 bg-purple-50/20 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-purple-900">Indicadores Evaluados</span>
            <span className="rounded-full bg-purple-600 px-2 py-0.5 text-xs font-bold text-white">
              {resumen.total_indicadores} activos
            </span>
          </div>
          <div className="my-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-purple-950">{resumen.total_indicadores}</span>
            <span className="text-xs font-medium text-purple-800">métricas vigentes</span>
          </div>
          <div className="flex flex-wrap items-center gap-1.5 border-t border-purple-200 pt-2">
            <span className="rounded-lg border border-blue-200 bg-blue-100 px-2 py-0.5 text-[11px] font-bold text-blue-900">
              {summary.sobrecumplimiento ?? 0} Sobrecumple
            </span>
            <span className="rounded-lg border border-emerald-200 bg-emerald-100 px-2 py-0.5 text-[11px] font-bold text-emerald-900">
              {summary.cumplimiento ?? 0} Cumple
            </span>
            <span className="rounded-lg border border-red-200 bg-red-100 px-2 py-0.5 text-[11px] font-bold text-red-900">
              {resumen.peligro} Crítico
            </span>
          </div>
        </div>

        <div className="flex flex-col justify-between rounded-xl border-2 border-red-300 bg-red-50/30 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-red-950">Estado de Alertas</span>
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-red-100 text-red-600">
              <AlertTriangle className="h-4 w-4" />
            </span>
          </div>
          <div className="my-3 flex items-baseline gap-1">
            <span className="text-3xl font-extrabold text-red-600">{resumen.peligro}</span>
            <span className="ml-1 text-xs font-bold text-red-900">en criticidad alta</span>
          </div>
          <div className="flex items-center justify-between border-t border-red-200 pt-2 text-xs">
            <span className="font-semibold text-amber-700">{resumen.alerta} alertas moderadas</span>
            {resumen.peligro > 0 && (
              <span className="rounded bg-red-600 px-2 py-0.5 font-bold text-white shadow-xs">Requiere revisión</span>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm lg:col-span-7">
          <div>
            <h3 className="text-base font-bold text-slate-900">Comparativa interanual</h3>
            <p className="text-xs text-slate-500">Evolución de cumplimiento porcentual anual consolidado</p>
          </div>
          {comparativa.length === 0 ? (
            <p className="text-sm text-slate-500">Sin histórico disponible para el filtro seleccionado.</p>
          ) : (
            <div className="space-y-3 pt-1">
              {comparativa.map((c, i) => {
                const width = Math.max(4, ((c.cumplimiento ?? 0) / maxComparativa) * 100);
                const current = i === 0;
                const barColor = YEAR_BAR_COLORS[i % YEAR_BAR_COLORS.length];
                return (
                  <div key={c.anio} className="space-y-1">
                    <div className={`flex justify-between text-xs font-bold ${current ? "text-poli-navy" : "text-slate-600"}`}>
                      <span className="flex items-center gap-1.5">
                        <span className="h-2 w-2 rounded-full" style={{ backgroundColor: barColor }} />
                        {c.anio}
                        {current ? " (Corte actual)" : ""}
                      </span>
                      <span
                        className="rounded px-2 py-0.5 font-extrabold text-white shadow-xs"
                        style={{ backgroundColor: barColor }}
                      >
                        {fmtPct(c.cumplimiento)}
                      </span>
                    </div>
                    <div className={`w-full overflow-hidden rounded-lg border border-blue-100 bg-blue-50 p-0.5 ${current ? "h-7" : "h-6"}`}>
                      <div
                        className="h-full rounded-md transition-all duration-500"
                        style={{ width: `${width}%`, backgroundColor: barColor }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="space-y-4 lg:col-span-5">
          {mejora && (
            <div className="rounded-xl border-2 border-emerald-300 border-l-4 border-l-emerald-600 bg-emerald-50/60 p-5 shadow-sm">
              <div className="mb-2 flex items-center gap-2.5">
                <div className="rounded-xl bg-emerald-600 p-2 text-white shadow-xs">
                  <Trophy className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-emerald-950">Mayor mejora institucional</h4>
                  <p className="text-[11px] font-bold text-emerald-800">Variación positiva destacada</p>
                </div>
              </div>
              <p className="text-sm leading-relaxed text-emerald-950">
                <span className="font-bold text-poli-navy">{mejora.name}</span> registra el mayor incremento con{" "}
                <span className="rounded border border-emerald-300 bg-emerald-100 px-1.5 py-0.5 font-bold text-emerald-800">
                  {mejora.change >= 0 ? "+" : ""}
                  {mejora.change} pp
                </span>{" "}
                {baseAnio ? `respecto al histórico ${baseAnio}.` : "respecto al periodo anterior."}
              </p>
            </div>
          )}

          {topCritico && (
            <div className="rounded-xl border-2 border-red-300 border-l-4 border-l-red-600 bg-red-50/60 p-5 shadow-sm">
              <div className="mb-2 flex items-center gap-2.5">
                <div className="rounded-xl bg-red-600 p-2 text-white shadow-xs">
                  <Zap className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-red-950">Foco de mayor riesgo</h4>
                  <p className="text-[11px] font-bold text-red-800">Alerta de dispersión en subprocesos</p>
                </div>
              </div>
              <p className="text-sm leading-relaxed text-red-950">
                El indicador <span className="font-bold">{String(topCritico.indicador ?? "—")}</span> cayó al{" "}
                <span className="rounded bg-red-600 px-1.5 py-0.5 font-bold text-white shadow-xs">
                  {fmtPct(topCritico.cumplimiento_pct as number)}
                </span>{" "}
                de meta{topCritico.proceso ? ` en ${String(topCritico.proceso)}` : ""}.
              </p>
            </div>
          )}

          <div className="grid grid-cols-4 gap-2 rounded-xl border border-blue-200 bg-white p-3.5 text-center shadow-xs">
            <DistCard label="Cumple" value={data?.distribucion_estado.cumple ?? 0} bg="bg-emerald-50/70" border="border-emerald-200" color="text-emerald-700" />
            <DistCard label="Alerta" value={data?.distribucion_estado.alerta ?? 0} bg="bg-amber-50/70" border="border-amber-200" color="text-amber-700" />
            <DistCard label="Crítico" value={data?.distribucion_estado.critico ?? 0} bg="bg-red-50/70" border="border-red-200" color="text-red-700" />
            <DistCard label="Sin dato" value={data?.distribucion_estado.sin_dato ?? 0} bg="bg-slate-100" border="border-slate-200" color="text-slate-500" />
          </div>
        </div>
      </div>

      {comparativaProcesos.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Comparativa de procesos (vista global)</h3>
              <p className="text-xs text-slate-500">Desempeño actual vs vigencia anterior y puntos porcentuales de variación</p>
            </div>
            {baseAnio && (
              <span className="text-xs text-slate-500">
                Base comparativa: {baseAnio}
                {baseMes ? ` (mes ${baseMes})` : ""}
              </span>
            )}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  <th className="px-6 py-3">Proceso Institucional</th>
                  <th className="px-6 py-3 text-right">Actual</th>
                  <th className="px-6 py-3 text-right">Anterior</th>
                  <th className="px-6 py-3 text-right">Variación</th>
                  <th className="px-6 py-3 text-center">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {comparativaProcesos.map((row) => {
                  const isActive = proceso !== "Todos" && row.proceso === proceso;
                  const nivelStyle = NIVEL_STYLES[row.estado] ?? { text: "#334155", bg: "#F8FAFC" };
                  return (
                    <tr key={row.proceso} className={`transition-colors hover:bg-slate-50 ${isActive ? "bg-blue-50/30" : ""}`}>
                      <td className="px-6 py-3 font-semibold text-slate-900">
                        {isActive && <span className="mr-2 inline-block h-4 w-1.5 rounded bg-poli-navy align-middle" />}
                        {row.proceso}
                      </td>
                      <td className="px-6 py-3 text-right font-bold text-poli-navy">{fmtPct(row.cumplimiento)}</td>
                      <td className="px-6 py-3 text-right text-slate-500">{fmtPct(row.cumplimiento_anterior)}</td>
                      <td className={`px-6 py-3 text-right font-bold ${(row.variacion ?? 0) >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                        {row.variacion != null ? `${row.variacion >= 0 ? "+" : ""}${row.variacion} pp` : "—"}
                      </td>
                      <td className="px-6 py-3 text-center">
                        {isActive ? (
                          <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-800">
                            Filtro Activo
                          </span>
                        ) : (
                          <span
                            className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold"
                            style={{ color: nivelStyle.text, backgroundColor: nivelStyle.bg }}
                          >
                            {row.estado}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function DistCard({
  label,
  value,
  color,
  bg = "bg-white",
  border = "border-slate-200",
}: {
  label: string;
  value: number;
  color: string;
  bg?: string;
  border?: string;
}) {
  return (
    <div className={`rounded-lg border p-2 ${bg} ${border}`}>
      <p className={`text-xl font-extrabold ${color}`}>{value}</p>
      <p className="text-[10px] font-bold uppercase text-slate-500">{label}</p>
    </div>
  );
}

const PROPUESTAS_FUENTES = ["Retos", "Proyectos", "Plan de mejoramiento", "Calidad"] as const;

function PropuestasGrid({
  propuestas,
}: {
  propuestas: InformeDashboardResponse["propuestas"];
}) {
  const byProceso = propuestas.reduce<Record<string, typeof propuestas>>((acc, p) => {
    (acc[p.proceso] ??= []).push(p);
    return acc;
  }, {});
  return (
    <div className="space-y-8">
      {Object.entries(byProceso).map(([proc, procItems]) => {
        const bySubproceso = procItems.reduce<Record<string, typeof procItems>>((acc, p) => {
          (acc[p.subproceso] ??= []).push(p);
          return acc;
        }, {});
        return (
          <div key={proc}>
            <h4 className="mb-3 text-base font-bold text-slate-900">{proc}</h4>
            <div className="space-y-5 border-l-2 border-slate-200 pl-4">
              {Object.entries(bySubproceso).map(([sub, items]) => (
                <div key={sub}>
                  <h5 className="mb-2 text-sm font-semibold text-slate-700">{sub}</h5>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    {PROPUESTAS_FUENTES.map((fuente) => {
                      const subset = items.filter((i) => i.fuente === fuente);
                      const style = subset[0]?.style ?? {};
                      return (
                        <div
                          key={fuente}
                          className="rounded-xl border-2 p-3"
                          style={{ backgroundColor: style.bg, borderColor: style.border }}
                        >
                          <p className="mb-2 text-sm font-bold" style={{ color: style.title }}>
                            {fuente}
                          </p>
                          {subset.length === 0 ? (
                            <p className="text-xs text-slate-400">Sin propuestas</p>
                          ) : (
                            <ul className="space-y-1 text-xs">
                              {subset.map((s, i) => (
                                <li key={i}>{s.indicador}</li>
                              ))}
                            </ul>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

