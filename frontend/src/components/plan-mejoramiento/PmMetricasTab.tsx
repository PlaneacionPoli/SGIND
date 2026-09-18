"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { KPICard } from "@/components/ui/KPICard";
import { fetchPlanMetricasDashboard } from "@/lib/api";
import { useAuthReady } from "@/stores/auth-store";
import { PmFactorBarChart } from "./PmFactorBarChart";
import { PmMetricaModal } from "./PmMetricaModal";
import { PmSparkline } from "./PmSparkline";

const TENDENCIA_BADGE: Record<string, string> = {
  Creciente: "bg-emerald-50 text-emerald-700",
  Decreciente: "bg-rose-50 text-rose-700",
  Estable: "bg-slate-100 text-slate-600",
  "—": "bg-slate-50 text-slate-400",
};

/** Pestaña "Métricas" del Plan de Mejoramiento — paridad con
 * pages/plan_mejoramiento.py::_render_tab_metricas (ver
 * docs/migration/PLAN_MIGRACION_PRIORIZADO.md ítem 0). */
export function PmMetricasTab() {
  const { isAuthenticated } = useAuthReady();
  const [factor, setFactor] = useState("Todos");
  const [tendencia, setTendencia] = useState("Toda tendencia");
  const [nombre, setNombre] = useState("");
  const [seleccion, setSeleccion] = useState<{
    factor: string;
    indicador: string;
    subindicador: string | null;
  } | null>(null);

  const query = useQuery({
    queryKey: ["plan-metricas", factor, tendencia, nombre],
    queryFn: () =>
      fetchPlanMetricasDashboard({
        ...(factor !== "Todos" ? { factor } : {}),
        ...(tendencia !== "Toda tendencia" ? { tendencia } : {}),
        ...(nombre.trim() ? { nombre: nombre.trim() } : {}),
      }),
    enabled: isAuthenticated,
  });

  const data = query.data;
  const tabla = data?.tabla ?? [];

  return (
    <div className="space-y-6">
      {!isAuthenticated ? (
        <p className="text-sm text-amber-700">Inicie sesión para ver el plan de mejoramiento.</p>
      ) : query.isLoading ? (
        <div className="h-40 animate-pulse rounded-lg bg-slate-200" />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KPICard label="Métricas con histórico" value={data?.kpis.total ?? 0} unit="series 2019–2026" />
            <KPICard
              label="Factores cubiertos"
              value={data?.kpis.factores_cubiertos ?? 0}
              unit="de 12 del modelo CNA"
            />
            <KPICard
              label="En tendencia creciente"
              value={data?.kpis.n_creciente ?? 0}
              unit={`${data?.kpis.pct_creciente ?? 0}% del total`}
            />
            <KPICard
              label="En tendencia decreciente"
              value={data?.kpis.n_decreciente ?? 0}
              unit={`${data?.kpis.pct_decreciente ?? 0}% del total`}
            />
          </div>

          <div>
            <h3 className="mb-1 text-sm font-bold text-slate-800">Resultados por factor</h3>
            <p className="mb-2 text-xs text-slate-500">
              Número de métricas con serie histórica registrada, por factor del modelo CNA. Clic en una
              barra para filtrar.
            </p>
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <PmFactorBarChart
                data={(data?.grafico_por_factor ?? []).map((f) => ({ factor: f.factor, value: f.cantidad }))}
                onFactorClick={setFactor}
              />
            </div>
          </div>

          <div>
            <h3 className="mb-1 text-sm font-bold text-slate-800">Resultados, tendencia y variaciones</h3>
            <p className="mb-2 text-xs text-slate-500">
              Selecciona un factor para filtrar. Haz clic en una métrica para ver su gráfica completa.
            </p>
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <div className="grid gap-3 sm:grid-cols-3">
                <select
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  value={factor}
                  onChange={(e) => setFactor(e.target.value)}
                >
                  <option value="Todos">Todos</option>
                  {(data?.filtros.factores ?? []).map((f) => (
                    <option key={f} value={f}>
                      {f}
                    </option>
                  ))}
                </select>
                <select
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  value={tendencia}
                  onChange={(e) => setTendencia(e.target.value)}
                >
                  {(data?.filtros.tendencias ?? ["Toda tendencia"]).map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
                <input
                  type="search"
                  placeholder="Buscar métrica…"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                />
              </div>
              {factor !== "Todos" ? (
                <p className="mt-2 text-xs text-slate-500">
                  Filtrando por: <strong>{factor}</strong>
                </p>
              ) : null}
            </div>
          </div>

          {!tabla.length ? (
            <p className="text-sm text-slate-500">No hay métricas que coincidan con el filtro.</p>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    {["Factor", "Métrica", "Proceso", "Último año", "Resultado", "Variación último año", "Tendencia", "Serie"].map(
                      (h) => (
                        <th key={h} className="px-3 py-2">
                          {h}
                        </th>
                      )
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {tabla.map((row, i) => (
                    <tr
                      key={i}
                      className="cursor-pointer hover:bg-slate-50"
                      onClick={() =>
                        setSeleccion({ factor: row.factor, indicador: row.indicador, subindicador: row.subindicador })
                      }
                    >
                      <td className="px-3 py-2">{row.factor_num != null ? `F${row.factor_num}` : "—"}</td>
                      <td className="max-w-xs truncate px-3 py-2">{row.metrica}</td>
                      <td className="px-3 py-2">{row.proceso ?? "—"}</td>
                      <td className="px-3 py-2">{row.ultimo_anio ?? "—"}</td>
                      <td className="px-3 py-2">{row.ultimo_valor != null ? row.ultimo_valor.toFixed(2) : "—"}</td>
                      <td className="px-3 py-2">
                        {row.variacion_ultima_pct != null
                          ? `${row.variacion_ultima_pct > 0 ? "+" : ""}${row.variacion_ultima_pct.toFixed(1)}%`
                          : "—"}
                      </td>
                      <td className="px-3 py-2">
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                            TENDENCIA_BADGE[row.tendencia] ?? TENDENCIA_BADGE["—"]
                          }`}
                        >
                          {row.tendencia}
                        </span>
                      </td>
                      <td className="px-3 py-2">
                        <PmSparkline values={row.serie} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      <PmMetricaModal seleccion={seleccion} onClose={() => setSeleccion(null)} />
    </div>
  );
}
