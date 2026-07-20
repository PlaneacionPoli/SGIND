"use client";

import { useState } from "react";
import type { CMILineaDetalle } from "@/lib/types";
import { CmiLineaAnalisisPanel } from "@/components/cmi/CmiLineaAnalisis";
import { fmtPct, NivelBadge } from "@/components/cmi/nivelUtils";
import { fmtMeta, fmtEjecucion } from "@/lib/formatValor";

interface CmiLineasTabProps {
  lineas: CMILineaDetalle[];
  expandLineaKey?: string | null;
}

type SubTab = "resumen" | "objetivos" | "analisis";

export function CmiLineasTab({ lineas, expandLineaKey }: CmiLineasTabProps) {
  const [openKeys, setOpenKeys] = useState<Set<string>>(() => {
    if (expandLineaKey) return new Set([expandLineaKey]);
    return new Set();
  });
  const [subTabs, setSubTabs] = useState<Record<string, SubTab>>({});

  const toggle = (key: string) => {
    setOpenKeys((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  if (!lineas.length) {
    return (
      <p className="rounded-lg border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
        No hay líneas estratégicas para mostrar.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-slate-800">Líneas Estratégicas y Objetivos</h3>
      {lineas.map((linea) => {
        const isOpen = openKeys.has(linea.linea_key);
        const subTab = subTabs[linea.linea_key] ?? "resumen";
        return (
          <div key={linea.linea_key} className="overflow-hidden rounded-2xl border border-slate-200 shadow-sm">
            <div
              className="flex items-center justify-between gap-4 px-5 py-4"
              style={{
                background: `linear-gradient(90deg, ${linea.color}ee 0%, ${linea.color}99 50%, ${linea.color}55 100%)`,
              }}
            >
              <div className="flex min-w-0 items-center gap-3">
                <span className="h-14 w-3 rounded-full" style={{ backgroundColor: linea.color }} />
                <div className="min-w-0">
                  <p className="truncate text-lg font-bold text-white">{linea.linea.replace(/_/g, " ")}</p>
                  <p className="text-sm text-white/90">
                    {linea.total_indicadores} indicadores · {linea.n_objetivos} objetivos · {linea.n_metas} metas
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="rounded-full bg-white/90 px-3 py-1 text-sm font-bold text-slate-900">
                  {fmtPct(linea.cumplimiento_promedio)}
                </span>
                <button
                  type="button"
                  onClick={() => toggle(linea.linea_key)}
                  className="rounded-lg bg-white/90 px-4 py-2 text-sm font-semibold text-poli-navy hover:bg-white"
                >
                  {isOpen ? "Cerrar" : "Ver"}
                </button>
              </div>
            </div>

            {isOpen && (
              <div className="border-t border-slate-200 bg-white p-5">
                <div className="mb-4 flex gap-2 border-b border-slate-200">
                  {(["resumen", "objetivos", "analisis"] as SubTab[]).map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setSubTabs((s) => ({ ...s, [linea.linea_key]: t }))}
                      className={`px-3 py-2 text-sm font-medium capitalize ${
                        subTab === t
                          ? "border-b-2 border-poli-blue text-poli-blue"
                          : "text-slate-500 hover:text-slate-700"
                      }`}
                    >
                      {t === "objetivos" ? "Objetivos, Metas e Indicadores" : t === "analisis" ? "Análisis" : "Resumen"}
                    </button>
                  ))}
                </div>

                {subTab === "resumen" && <LineaResumen linea={linea} />}
                {subTab === "objetivos" && <LineaObjetivos linea={linea} />}
                {subTab === "analisis" && <CmiLineaAnalisisPanel linea={linea} />}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function LineaResumen({ linea }: { linea: CMILineaDetalle }) {
  const n_pendiente =
    linea.total_indicadores -
    linea.n_sobrecumplimiento -
    linea.n_cumplimiento -
    linea.n_alerta -
    linea.n_riesgo;

  const metrics: [string, string, string][] = [
    ["Cumplimiento Promedio", fmtPct(linea.cumplimiento_promedio), linea.color],
    ["Sobrecumplimiento", String(linea.n_sobrecumplimiento), "#1D4ED8"],
    ["Cumplimiento", String(linea.n_cumplimiento), "#166534"],
    ["Alerta", String(linea.n_alerta), "#B45309"],
    ["Peligro", String(linea.n_riesgo), "#B71C1C"],
    ...(n_pendiente > 0
      ? [["Pendiente de reporte", String(n_pendiente), "#475569"] as [string, string, string]]
      : []),
    ["Total indicadores", String(linea.total_indicadores), "#334155"],
  ];

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-7">
        {metrics.map(([title, value, color]) => (
          <div key={title} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-xs text-slate-500">{title}</p>
            <p className="mt-2 text-2xl font-bold text-slate-900">{value}</p>
            <div className="mt-3 h-1 w-10 rounded-full" style={{ backgroundColor: color }} />
          </div>
        ))}
      </div>
      <AllIndicadoresTable linea={linea} />
    </div>
  );
}

function AllIndicadoresTable({ linea }: { linea: CMILineaDetalle }) {
  const indicadores = linea.objetivos
    .flatMap((obj) => obj.metas.flatMap((m) => m.indicadores))
    .sort((a, b) => {
      const pa = ((a as Record<string, unknown>).cumplimiento_pct as number) ?? -1;
      const pb = ((b as Record<string, unknown>).cumplimiento_pct as number) ?? -1;
      return pb - pa;
    });
  if (!indicadores.length) return null;

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <p className="mb-3 text-sm font-semibold text-slate-800">
        Todos los indicadores ({indicadores.length})
      </p>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-200 text-slate-500">
              <th className="px-2 py-2 font-semibold">Indicador</th>
              <th className="px-2 py-2 font-semibold">Meta</th>
              <th className="px-2 py-2 font-semibold">Ejecución</th>
              <th className="px-2 py-2 font-semibold">% Cumplimiento</th>
              <th className="px-2 py-2 font-semibold">Estado</th>
            </tr>
          </thead>
          <tbody>
            {indicadores.map((ind, i) => (
              <tr key={(ind.Id as string) ?? i} className="border-b border-slate-100 hover:bg-white">
                <td className="px-2 py-2 text-slate-700">{ind.Indicador as string}</td>
                <td className="px-2 py-2 font-medium text-slate-800">
                  {fmtMeta(ind as Record<string, unknown>)}
                </td>
                <td className="px-2 py-2 font-medium text-slate-800">
                  {fmtEjecucion(ind as Record<string, unknown>)}
                </td>
                <td className="px-2 py-2 font-bold text-slate-900">
                  {fmtPct((ind as Record<string, unknown>).cumplimiento_pct as number | undefined)}
                </td>
                <td className="px-2 py-2">
                  <NivelBadge nivel={(ind as Record<string, unknown>)["Nivel de cumplimiento"] as string | undefined} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function LineaObjetivos({ linea }: { linea: CMILineaDetalle }) {
  return (
    <div className="space-y-4">
      {linea.objetivos.map((obj) => (
        <details key={obj.objetivo} className="rounded-lg border border-slate-200 bg-slate-50 p-3" open>
          <summary className="cursor-pointer font-semibold text-slate-800">
            Objetivo estratégico: {obj.objetivo}
          </summary>
          <div className="mt-3 space-y-3 pl-2">
            {obj.metas.map((meta, idx) => (
              <details key={`${obj.objetivo}-${idx}`} className="rounded-lg border border-slate-200 bg-white p-3">
                <summary className="cursor-pointer text-sm font-medium text-slate-700">
                  {meta.meta ? `Meta Estratégica: ${meta.meta}` : "Indicadores del objetivo"}
                </summary>
                <div className="mt-2 overflow-x-auto">
                  <table className="min-w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-500">
                        <th className="px-2 py-2">Indicador</th>
                        <th className="px-2 py-2">Meta</th>
                        <th className="px-2 py-2">Ejecución</th>
                        <th className="px-2 py-2">% Cumplimiento</th>
                        <th className="px-2 py-2">Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {meta.indicadores.map((ind) => (
                        <tr key={ind.Id ?? ind.Indicador} className="border-b border-slate-100">
                          <td className="px-2 py-2">{ind.Indicador}</td>
                          <td className="px-2 py-2">{fmtMeta(ind as Record<string, unknown>)}</td>
                          <td className="px-2 py-2">{fmtEjecucion(ind as Record<string, unknown>)}</td>
                          <td className="px-2 py-2 font-semibold">
                            {fmtPct(ind.cumplimiento_pct as number | undefined)}
                          </td>
                          <td className="px-2 py-2">
                            <NivelBadge nivel={ind["Nivel de cumplimiento"] as string | undefined} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
            ))}
          </div>
        </details>
      ))}
    </div>
  );
}
