"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ProyectosPmoTimeline } from "@/components/charts/ProyectosPmoTimeline";
import { CmiEstrategicoTable } from "@/components/tables/CmiEstrategicoTable";
import { RetosBadges } from "@/components/ui/RetosBadges";
import { findStrategicLine } from "@/lib/strategic-lines";
import { fetchDashboardFiltros, fetchResumenLinea } from "@/lib/api";
import { PDI_VISTAS_POR_LINEA } from "@/lib/pdi";
import { useAuthReady } from "@/stores/auth-store";

export default function HojaLineaPage({ params }: { params: { key: string } }) {
  const { key } = params;
  const router = useRouter();
  const { ready, isAuthenticated } = useAuthReady();
  const [anio, setAnio] = useState<number | null>(null); // null = rango Cierre PDI 2022-2025

  const lineDef = findStrategicLine(key);

  const filtrosQuery = useQuery({
    queryKey: ["dashboard-filtros"],
    queryFn: () => fetchDashboardFiltros(PDI_VISTAS_POR_LINEA),
    enabled: ready && isAuthenticated,
  });
  const years = filtrosQuery.data?.anios ?? [2022, 2023, 2024, 2025];

  const lineaQuery = useQuery({
    queryKey: ["resumen-linea", key, anio],
    queryFn: () => fetchResumenLinea(key, anio ?? undefined, PDI_VISTAS_POR_LINEA),
    enabled: ready && isAuthenticated,
  });

  useEffect(() => {
    if (lineaQuery.isError) {
      // Línea inexistente o slug incorrecto: volver al portal.
      router.replace("/resumen-general/consolidado-por-linea");
    }
  }, [lineaQuery.isError, router]);

  const data = lineaQuery.data;
  const color = data?.color ?? lineDef?.color ?? "#0F385A";
  const label = data?.linea ?? lineDef?.label ?? key;

  function volver() {
    router.push("/resumen-general/consolidado-por-linea");
  }

  return (
    <div className="space-y-4 animate-in fade-in-50 slide-in-from-bottom-2 duration-500">
      {/* Header: réplica del header de línea del proyecto de referencia
          (barra sólida del color de línea, ícono 🎯 en círculo punteado,
          botón ✕ que vuelve al portal — equivalente a goBack()). */}
      <div
        className="flex items-center gap-3.5 rounded-xl px-5 py-3 shadow-md"
        style={{ backgroundColor: color }}
      >
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border-2 border-dashed border-white/60 text-2xl">
          🎯
        </div>
        <h1 className="flex-1 text-lg font-black uppercase tracking-wide text-white sm:text-2xl">
          {label}
        </h1>
        <button
          type="button"
          onClick={volver}
          aria-label="Volver a Consolidado por Línea"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-white/20 text-lg text-white transition hover:bg-white/40"
        >
          ✕
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-3 rounded-lg border border-slate-200 bg-white p-4">
        <p className="text-xs font-semibold uppercase text-slate-500">Año</p>
        <div className="flex flex-wrap gap-2">
          {years.map((y) => (
            <button
              key={y}
              type="button"
              onClick={() => setAnio(y)}
              className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                anio === y ? "bg-poli-navy text-white shadow-sm" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {y}
            </button>
          ))}
          <button
            type="button"
            onClick={() => setAnio(null)}
            className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
              anio === null ? "bg-poli-navy text-white shadow-sm" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            Cierre PDI 2022-2025
          </button>
        </div>
      </div>

      {lineaQuery.isLoading || !data ? (
        <div className="grid gap-4 lg:grid-cols-[1fr_1.6fr]">
          <div className="h-64 animate-pulse rounded-xl bg-slate-200" />
          <div className="h-64 animate-pulse rounded-xl bg-slate-200" />
        </div>
      ) : (
        <>
          <div className="grid gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm lg:grid-cols-[1fr_1.6fr]">
            <div className="border-slate-100 lg:border-r lg:pr-4">
              <h3 className="mb-3 text-center text-xs font-black uppercase tracking-wide text-[#0F385A]">
                Retos
              </h3>
              <RetosBadges retos={data.retos} color={color} />
            </div>
            <div>
              <h3 className="mb-3 text-sm font-bold text-slate-800">Proyectos PMO</h3>
              <ProyectosPmoTimeline items={data.proyectos} />
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <CmiEstrategicoTable objetivos={data.objetivos} color={color} />
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <h3 className="mb-2 text-sm font-semibold text-slate-800">Análisis Integrado</h3>
            <p className="text-sm text-slate-600">
              La línea <strong style={{ color }}>{label}</strong> registra un cumplimiento de retos del{" "}
              <strong>{data.retos.cumplimiento.toFixed(1)}%</strong> sobre {data.retos.n_areas} área(s),
              con <strong>{data.proyectos.length}</strong> proyecto(s) PMO en el cronograma y{" "}
              <strong>
                {data.objetivos.reduce((acc, o) => acc + o.indicadores.length, 0)}
              </strong>{" "}
              indicador(es) del CMI Estratégico monitoreados.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
