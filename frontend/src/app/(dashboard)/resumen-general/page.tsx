"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { PdiMindmap } from "@/components/charts/PdiMindmap";
import { ProyectosGanttChart } from "@/components/charts/ProyectosGanttChart";
import { DataFreshnessFooter } from "@/components/layout/DataFreshnessFooter";
import { DetailTables } from "@/components/tables/DetailTables";
import { TrendVariationTables } from "@/components/tables/TrendVariationTables";
import { ChipRow } from "@/components/ui/ChipRow";
import { ExecutiveNarrative } from "@/components/ui/ExecutiveNarrative";
import { StrategyCardGrid } from "@/components/ui/StrategyCard";
import { VistaSelector } from "@/components/ui/VistaSelector";
import { YearSegmentedControl } from "@/components/ui/YearSegmentedControl";
import { downloadInformeEjecutivoPdf, fetchDashboardFiltros, fetchHealth, fetchResumenCompleto } from "@/lib/api";
import { isDevLoginEnabled, useDevLogin } from "@/hooks/use-dev-login";
import { useAuthReady } from "@/stores/auth-store";

export default function ResumenGeneralPage() {
  const router = useRouter();
  const { ready, isAuthenticated } = useAuthReady();
  const { login, loading: loginLoading, error: loginError } = useDevLogin();
  const showDevLogin = isDevLoginEnabled();
  const [anio, setAnio] = useState<number>(2025);
  const [vista, setVista] = useState("indicadores");
  const [rango, setRango] = useState(true);
  const [subTab, setSubTab] = useState<"listado" | "gantt">("listado");

  const filtrosQuery = useQuery({
    queryKey: ["dashboard-filtros"],
    queryFn: fetchDashboardFiltros,
    enabled: ready && isAuthenticated,
  });

  useEffect(() => {
    if (filtrosQuery.data?.anio_default) {
      setAnio(filtrosQuery.data.anio_default);
    }
  }, [filtrosQuery.data?.anio_default]);

  const anioEfectivo = anio;

  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
  });

  const resumenQuery = useQuery({
    queryKey: ["resumen-completo", anioEfectivo, vista, rango],
    queryFn: () => fetchResumenCompleto({ anio: anioEfectivo, vista, rango }),
    enabled: ready && isAuthenticated,
  });

  const needsAuth = ready && !isAuthenticated;
  const showLoading = !ready || (isAuthenticated && resumenQuery.isFetching && !resumenQuery.data);
  const years = filtrosQuery.data?.anios ?? [2022, 2023, 2024, 2025];
  const [pdfLoading, setPdfLoading] = useState(false);

  async function handleDownloadPdf() {
    setPdfLoading(true);
    try {
      await downloadInformeEjecutivoPdf();
    } finally {
      setPdfLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl bg-gradient-to-r from-slate-900 to-slate-800 px-6 py-5 text-white shadow-md">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-widest text-blue-200">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              Sistema de Indicadores Institucionales
            </p>
            <h2 className="mt-2 text-2xl font-bold text-white">Plan de Desarrollo Institucional 2022–2026</h2>
            <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-slate-300">
              Seguimiento estratégico de indicadores PDI · Cuadro de Mando Integral
              {health && (
                <span className="rounded bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-300">
                  API {health.status} · v{health.version}
                </span>
              )}
            </p>
          </div>
          {isAuthenticated && (
            <div className="flex shrink-0 items-center gap-2">
              <button
                type="button"
                onClick={() => router.push("/resumen-general/consolidado-por-linea")}
                className="flex items-center gap-2 rounded-lg border border-blue-400/40 bg-blue-500/20 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-500/30"
              >
                Consolidado por Línea
              </button>
              <button
                type="button"
                onClick={handleDownloadPdf}
                disabled={pdfLoading}
                className="flex items-center gap-2 rounded-lg border border-slate-600 bg-slate-700 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-600 disabled:opacity-50"
              >
                {pdfLoading ? "Generando…" : "Informe Ejecutivo"}
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-slate-200 bg-white p-4">
        <div className="flex flex-wrap items-center gap-3">
          <p className="text-xs font-semibold uppercase text-slate-500">Año</p>
          <YearSegmentedControl
            years={years}
            anio={anioEfectivo}
            rango={rango}
            onChange={(y) => {
              setRango(false);
              setAnio(y);
            }}
            onSelectRango={() => setRango(true)}
          />
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <p className="text-xs font-semibold uppercase text-slate-500">Vista</p>
          <VistaSelector
            vista={vista}
            vistas={filtrosQuery.data?.vistas}
            onChange={setVista}
          />
        </div>
      </div>

      {showLoading ? (
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-5">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-24 animate-pulse rounded-xl bg-slate-200" />
            ))}
          </div>
          <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-36 animate-pulse rounded-xl bg-slate-200" />
            ))}
          </div>
        </div>
      ) : needsAuth ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <p>Inicie sesión para ver el Resumen General.</p>
          {loginError && <p className="mt-2 text-red-700">{loginError}</p>}
          {showDevLogin && (
            <button
              type="button"
              onClick={() => login()}
              disabled={loginLoading}
              className="mt-3 rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              {loginLoading ? "Conectando…" : "Acceso desarrollo"}
            </button>
          )}
        </div>
      ) : resumenQuery.isError ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <p>Error al cargar datos. Verifique que el backend esté activo.</p>
          <p className="mt-1 text-xs text-red-600">
            {resumenQuery.error instanceof Error ? resumenQuery.error.message : "Error desconocido"}
          </p>
        </div>
      ) : resumenQuery.data ? (
        <>
          <ChipRow chips={resumenQuery.data.chips} />
          <StrategyCardGrid cards={resumenQuery.data.fichas} />

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <h3 className="mb-3 text-sm font-semibold text-slate-800">
              Alineación de Objetivos Estratégicos
            </h3>
            <PdiMindmap data={resumenQuery.data.mindmap} />
          </div>

          <ExecutiveNarrative data={resumenQuery.data.narrativa} />

          {vista === "retos" && resumenQuery.data.tabla_detalle && (
            <DetailTables vista={vista} rows={resumenQuery.data.tabla_detalle} />
          )}

          {vista === "proyectos" && (
            <div className="space-y-3">
              <div className="inline-flex rounded-lg bg-slate-100 p-1">
                {(["listado", "gantt"] as const).map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setSubTab(t)}
                    className={`rounded-md px-4 py-1.5 text-sm font-semibold transition ${
                      subTab === t ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"
                    }`}
                  >
                    {t === "listado" ? "Listado" : "Gantt"}
                  </button>
                ))}
              </div>
              {subTab === "listado" && resumenQuery.data.tabla_detalle && (
                <DetailTables
                  vista={vista}
                  rows={resumenQuery.data.tabla_detalle}
                  lineColors={Object.fromEntries(resumenQuery.data.fichas.map((f) => [f.linea, f.color]))}
                />
              )}
              {subTab === "gantt" && resumenQuery.data.gantt_proyectos && (
                <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                  <h3 className="mb-1 text-sm font-semibold text-slate-800">Cronograma de Proyectos PDI</h3>
                  <p className="mb-3 text-xs text-slate-500">
                    Vigencia activa por proyecto entre {resumenQuery.data.gantt_proyectos.anio_min} y{" "}
                    {resumenQuery.data.gantt_proyectos.anio_max}
                  </p>
                  <ProyectosGanttChart data={resumenQuery.data.gantt_proyectos} />
                </div>
              )}
            </div>
          )}

          {vista === "indicadores" && (
            <TrendVariationTables
              mejoraron={resumenQuery.data.mejoraron}
              enRiesgo={resumenQuery.data.en_riesgo}
              periodoComparacion={resumenQuery.data.periodo_comparacion}
            />
          )}
        </>
      ) : null}

      <DataFreshnessFooter />
    </div>
  );
}
