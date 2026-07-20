"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { SunburstPlotlyChart } from "@/components/charts/SunburstPlotlyChart";
import { ProyectosGanttChart } from "@/components/charts/ProyectosGanttChart";
import { DetailTables } from "@/components/tables/DetailTables";
import { TrendVariationTables } from "@/components/tables/TrendVariationTables";
import { ChipRow } from "@/components/ui/ChipRow";
import { ExecutiveNarrative } from "@/components/ui/ExecutiveNarrative";
import { StrategyCardGrid } from "@/components/ui/StrategyCard";
import { VistaSelector } from "@/components/ui/VistaSelector";
import { YearSegmentedControl } from "@/components/ui/YearSegmentedControl";
import { downloadResumenGeneralPdf, fetchDashboardFiltros, fetchHealth, fetchResumenCompleto } from "@/lib/api";
import { isDevLoginEnabled, useDevLogin } from "@/hooks/use-dev-login";
import { useAuthReady } from "@/stores/auth-store";

export default function ResumenGeneralPage() {
  const { ready, isAuthenticated } = useAuthReady();
  const { login, loading: loginLoading, error: loginError } = useDevLogin();
  const showDevLogin = isDevLoginEnabled();
  const [anio, setAnio] = useState<number>(2025);
  const [vista, setVista] = useState("indicadores");
  const [rango, setRango] = useState(false);

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
  const years = filtrosQuery.data?.anios ?? [2022, 2023, 2024, 2025, 2026];
  const [pdfLoading, setPdfLoading] = useState(false);

  async function handleDownloadPdf() {
    setPdfLoading(true);
    try {
      await downloadResumenGeneralPdf(anioEfectivo);
    } finally {
      setPdfLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl bg-gradient-to-r from-slate-900 to-slate-800 p-6 text-white shadow-md">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-blue-200">Sistema de Indicadores</p>
            <h2 className="mt-1 text-2xl font-bold">Plan de Desarrollo Institucional 2022–2026</h2>
            <p className="mt-1 text-sm text-slate-300">
              Seguimiento estratégico de indicadores PDI · Cuadro de Mando Integral
            </p>
            {health && (
              <p className="mt-2 text-xs text-slate-400">
                API {health.status} · v{health.version}
              </p>
            )}
          </div>
          {isAuthenticated && (
            <button
              type="button"
              onClick={handleDownloadPdf}
              disabled={pdfLoading || showLoading}
              className="flex shrink-0 items-center gap-2 rounded-lg border border-slate-600 bg-slate-700 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-600 disabled:opacity-50"
            >
              {pdfLoading ? "Generando…" : "Descargar PDF"}
            </button>
          )}
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-4">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase text-slate-500">Año</p>
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
        <div>
          <p className="mb-2 text-xs font-semibold uppercase text-slate-500">Vista</p>
          <VistaSelector
            vista={vista}
            vistas={filtrosQuery.data?.vistas}
            onChange={setVista}
          />
        </div>
        <p className="text-xs text-slate-500">
          Filtros activos: Año {rango ? "Consolidado 2022-2025" : anioEfectivo} · Vista{" "}
          {vista === "indicadores"
            ? "Indicadores"
            : vista === "proyectos"
              ? "Proyectos"
              : vista === "retos"
                ? "Plan de Retos"
                : "Consolidado"}
        </p>
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
            <SunburstPlotlyChart data={resumenQuery.data.sunburst} />
          </div>

          <ExecutiveNarrative data={resumenQuery.data.narrativa} />

          {(vista === "proyectos" || vista === "retos") && resumenQuery.data.tabla_detalle && (
            <DetailTables vista={vista} rows={resumenQuery.data.tabla_detalle} />
          )}

          {vista === "proyectos" && resumenQuery.data.gantt_proyectos && (
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h3 className="mb-1 text-sm font-semibold text-slate-800">
                Cronograma de Proyectos PDI
              </h3>
              <p className="mb-3 text-xs text-slate-500">
                Vigencia activa por proyecto entre {resumenQuery.data.gantt_proyectos.anio_min} y{" "}
                {resumenQuery.data.gantt_proyectos.anio_max}
              </p>
              <ProyectosGanttChart data={resumenQuery.data.gantt_proyectos} />
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
    </div>
  );
}
