"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { CmiProcesosCalidadSection } from "@/components/cmi/CmiProcesosCalidadSection";
import { CmiProcesosFichaModal } from "@/components/cmi/CmiProcesosFichaModal";
import { CmiProcesosFilters } from "@/components/cmi/CmiProcesosFilters";
import { CmiProcesosListadoTab } from "@/components/cmi/CmiProcesosListadoTab";
import { KPICard } from "@/components/ui/KPICard";
import { CmiCumplimientoHorizBarPlotly } from "@/components/cmi/CmiCumplimientoHorizBarPlotly";
import { fmtPct } from "@/components/cmi/nivelUtils";
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
  { id: "resumen", label: "Resumen Ejecutivo", icon: "📋" },
  { id: "indicadores", label: "Indicadores", icon: "📊" },
  { id: "calidad", label: "Calidad de Datos", icon: "✅" },
  { id: "auditoria", label: "Auditoría", icon: "🔍" },
  { id: "propuestas", label: "Propuestas", icon: "💡" },
  { id: "ia", label: "Análisis IA", icon: "🤖" },
] as const;

type TabId = (typeof TABS)[number]["id"];

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
    queryKey: ["informe-filtros", anio],
    queryFn: () => fetchCMIProcesosFiltros(anio ?? undefined),
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

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Informe por Procesos</h2>
          <p className="mt-1 text-slate-600">
            Resumen ejecutivo, indicadores, calidad, auditoría, propuestas y análisis heurístico.
          </p>
        </div>
        {isAuthenticated && (
          <button
            type="button"
            onClick={handleDownloadPdf}
            disabled={pdfLoading || dashQuery.isLoading}
            className="flex shrink-0 items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:opacity-50"
          >
            {pdfLoading ? "Generando…" : "Descargar PDF"}
          </button>
        )}
      </div>

      {!isAuthenticated ? (
        <p className="text-sm text-amber-700">Inicie sesión para ver el informe.</p>
      ) : (
        <>
          {isAuthenticated && filtrosQuery.data && anio != null && mes != null && (
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
          )}

          <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-1">
            {TABS.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setTab(t.id)}
                className={`rounded-t-lg px-4 py-2 text-sm font-semibold transition ${
                  tab === t.id
                    ? "border border-b-0 border-slate-200 bg-white text-poli-navy"
                    : "text-slate-500 hover:text-slate-800"
                }`}
              >
                {t.icon} {t.label}
              </button>
            ))}
          </div>

          {dashQuery.isLoading ? (
            <div className="h-48 animate-pulse rounded-lg bg-slate-200" />
          ) : (
            <>
              {tab === "resumen" && resumen && (
                <div className="space-y-6">
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <KPICard label="Score de Salud" value={String(resumen.score)} trend={resumen.label} />
                    <KPICard label="Cumplimiento Global" value={fmtPct(resumen.avg)} trend="Meta: 100%" />
                    <KPICard
                      label="Indicadores evaluados"
                      value={String(resumen.total_indicadores)}
                      trend={`${resumen.total_indicadores} activos`}
                    />
                    <KPICard
                      label="Estado de alertas"
                      value={String(resumen.alerta + resumen.peligro)}
                      trend={`${resumen.alerta} alertas · ${resumen.peligro} críticos`}
                    />
                  </div>
                  {resumen.delta != null && (
                    <p className="text-sm text-slate-600">
                      {resumen.delta >= 0 ? "+" : ""}
                      {resumen.delta}% respecto al año anterior
                    </p>
                  )}
                  {(data?.comparativa_interanual?.length ?? 0) > 0 && (
                    <div className="rounded-xl border border-slate-200 bg-white p-4">
                      <h3 className="mb-2 text-sm font-bold">Comparativa interanual</h3>
                      <CmiCumplimientoHorizBarPlotly
                        data={(data?.comparativa_interanual ?? []).map((c) => ({
                          label: String(c.anio),
                          value: c.cumplimiento,
                          color: "#1A3A5C",
                        }))}
                      />
                    </div>
                  )}
                  {(data?.criticos?.length ?? 0) > 0 && (
                    <div className="rounded-xl border border-red-100 bg-red-50 p-4">
                      <h3 className="mb-2 text-sm font-bold text-red-900">Top indicadores críticos</h3>
                      <ul className="space-y-1 text-sm text-red-800">
                        {(data?.criticos ?? []).map((c, i) => (
                          <li key={i}>
                            {String((c as Record<string, unknown>).indicador ?? (c as Record<string, unknown>).nombre)} —{" "}
                            {fmtPct((c as Record<string, unknown>).cumplimiento_pct as number)}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                    <DistCard label="Cumple" value={data?.distribucion_estado.cumple ?? 0} color="#2E7D32" />
                    <DistCard label="Alerta" value={data?.distribucion_estado.alerta ?? 0} color="#F9A825" />
                    <DistCard label="Crítico" value={data?.distribucion_estado.critico ?? 0} color="#C62828" />
                    <DistCard label="Sin dato" value={data?.distribucion_estado.sin_dato ?? 0} color="#6E7781" />
                  </div>
                </div>
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
                <section className="space-y-6">
                  {data?.auditoria_error ? (
                    <p className="text-sm text-amber-700">{data.auditoria_error}</p>
                  ) : (
                    (data?.auditoria ?? []).map((sec) => (
                      <div key={sec.tipo}>
                        <h3 className="mb-4 text-lg font-semibold text-slate-800">{sec.titulo}</h3>
                        {sec.fichas.length === 0 ? (
                          <p className="text-sm text-slate-500">Sin fichas para este filtro.</p>
                        ) : (
                          <div className="space-y-4">
                            {sec.fichas.map((ficha, i) => (
                              <div key={i} className="rounded-xl border border-slate-200 bg-white p-4">
                                <h4 className="mb-3 font-bold text-slate-800">{ficha.proceso}</h4>
                                <div className="space-y-2">
                                  {ficha.categorias.map((cat, j) => (
                                    <div
                                      key={j}
                                      className="rounded-lg p-3 text-sm"
                                      style={{ backgroundColor: cat.pill_bg, color: cat.pill_text }}
                                    >
                                      <span className="font-bold">
                                        {cat.emoji} {cat.label}
                                      </span>
                                      <p className="mt-1 whitespace-pre-wrap">{cat.valor}</p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </section>
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

              {tab === "ia" && data?.analisis_ia && (
                <section className="space-y-4">
                  <p className="text-sm text-slate-700">
                    <strong>{data.analisis_ia.conteos.peligro}</strong> en peligro ·{" "}
                    <strong>{data.analisis_ia.conteos.alerta}</strong> en alerta ·{" "}
                    <strong>{data.analisis_ia.conteos.saludables}</strong> saludables
                  </p>
                  <IATable title="Top riesgos (peligro)" rows={data.analisis_ia.top_peligro} />
                  <IATable title="Top alertas" rows={data.analisis_ia.top_alerta} />
                </section>
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
    </div>
  );
}

function DistCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 text-center">
      <p className="text-2xl font-bold" style={{ color }}>
        {value}
      </p>
      <p className="text-xs font-medium text-slate-500">{label}</p>
    </div>
  );
}

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
    <div className="space-y-6">
      {Object.entries(byProceso).map(([proc, items]) => (
        <div key={proc}>
          <h4 className="mb-2 font-bold text-slate-800">{proc}</h4>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {["Retos", "Proyectos", "Plan de mejoramiento", "Calidad"].map((fuente) => {
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
                  <ul className="space-y-1 text-xs">
                    {subset.map((s, i) => (
                      <li key={i}>
                        <span className="text-slate-500">{s.subproceso}:</span> {s.indicador}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

function IATable({ title, rows }: { title: string; rows: Array<Record<string, unknown>> }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <h4 className="border-b px-4 py-2 text-sm font-bold">{title}</h4>
      <table className="min-w-full text-sm">
        <thead className="bg-slate-50 text-xs uppercase text-slate-500">
          <tr>
            <th className="px-3 py-2 text-left">Indicador</th>
            <th className="px-3 py-2 text-left">Proceso</th>
            <th className="px-3 py-2 text-left">Cumplimiento</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {rows.map((r, i) => (
            <tr key={i}>
              <td className="px-3 py-2">{String(r.indicador ?? "")}</td>
              <td className="px-3 py-2">{String(r.proceso ?? "")}</td>
              <td className="px-3 py-2">{r.cumplimiento_pct != null ? `${r.cumplimiento_pct}%` : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
