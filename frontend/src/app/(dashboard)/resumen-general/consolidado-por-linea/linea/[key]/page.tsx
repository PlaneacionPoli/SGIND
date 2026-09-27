"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ProyectosGanttChart } from "@/components/charts/ProyectosGanttChart";
import { CmiEstrategicoTable } from "@/components/tables/CmiEstrategicoTable";
import { RetosBadges } from "@/components/ui/RetosBadges";
import { STRATEGIC_ICON_MAP } from "@/lib/strategic-icons";
import { findStrategicLine } from "@/lib/strategic-lines";
import { fetchDashboardFiltros, fetchResumenLinea } from "@/lib/api";
import { useAuthReady } from "@/stores/auth-store";

export default function HojaLineaPage({ params }: { params: { key: string } }) {
  const { key } = params;
  const router = useRouter();
  const { ready, isAuthenticated } = useAuthReady();
  const [anio, setAnio] = useState<number | null>(null); // null = rango Cierre PDI 2022-2025

  const lineDef = findStrategicLine(key);
  const IconComponent = lineDef ? STRATEGIC_ICON_MAP[lineDef.icon] : undefined;

  const filtrosQuery = useQuery({
    queryKey: ["dashboard-filtros"],
    queryFn: fetchDashboardFiltros,
    enabled: ready && isAuthenticated,
  });
  const years = filtrosQuery.data?.anios ?? [2022, 2023, 2024, 2025];

  const lineaQuery = useQuery({
    queryKey: ["resumen-linea", key, anio],
    queryFn: () => fetchResumenLinea(key, anio ?? undefined),
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

  const proyectosGanttData = data
    ? {
        anio_min: 2022,
        anio_max: 2025,
        items: data.proyectos.map((p) => ({
          ...p,
          estado: p.stand_by ? "Stand by" : p.estado,
        })),
      }
    : null;

  return (
    <div className="space-y-6 animate-in fade-in-50 slide-in-from-bottom-2 duration-500">
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <button
          type="button"
          onClick={() => router.push("/resumen-general/consolidado-por-linea")}
          className="inline-flex items-center gap-1 font-medium text-poli-navy hover:underline"
        >
          ← Consolidado por Línea
        </button>
        <span className="text-slate-300">/</span>
        <span className="font-semibold text-slate-700">{label}</span>
      </div>

      <div
        className="flex items-center gap-3 rounded-xl px-6 py-5 text-white shadow-md"
        style={{ background: `linear-gradient(120deg, ${color}, ${color}CC)` }}
      >
        {IconComponent && (
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-white/20">
            <IconComponent size={26} strokeWidth={1.75} />
          </div>
        )}
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-widest text-white/80">
            Línea Estratégica
          </p>
          <h1 className="text-2xl font-bold">{label}</h1>
        </div>
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
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="h-64 animate-pulse rounded-xl bg-slate-200" />
          <div className="h-64 animate-pulse rounded-xl bg-slate-200" />
        </div>
      ) : (
        <>
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h3 className="mb-3 text-sm font-semibold text-slate-800">Retos</h3>
              <RetosBadges retos={data.retos} color={color} />
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h3 className="mb-3 text-sm font-semibold text-slate-800">Proyectos PMO</h3>
              {proyectosGanttData && <ProyectosGanttChart data={proyectosGanttData} />}
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <h3 className="mb-3 text-sm font-semibold text-slate-800">CMI Estratégico</h3>
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
