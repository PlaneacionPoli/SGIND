"use client";

import { Activity, BarChart3, ListOrdered, PieChart as PieIcon } from "lucide-react";
import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Pie,
  PieChart,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type {
  SeguimientoKpis,
  SeguimientoPorPeriodicidad,
  SeguimientoProcesoCumplimiento,
  SeguimientoTendenciaPunto,
} from "@/lib/types";
import { COLOR } from "./constants";
import { Panel, Vacio } from "./Panel";

const EJE = { fontSize: 11, fill: COLOR.texto } as const;

function TooltipCaja({ children }: { children: React.ReactNode }) {
  return <div className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs shadow-elevated">{children}</div>;
}

// ─── Tendencia por corte ─────────────────────────────────────────────────────

interface TendenciaProps {
  datos: SeguimientoTendenciaPunto[];
  /** Corte seleccionado (para resaltarlo); null = todos. */
  seleccionado: { anio: number; mes: number } | null;
  onSeleccionar: (anio: number, mes: number) => void;
  proceso: string;
}

export function TendenciaChart({ datos, seleccionado, onSeleccionar, proceso }: TendenciaProps) {
  const sel = seleccionado ? datos.find((d) => d.anio === seleccionado.anio && d.mes === seleccionado.mes) : undefined;
  return (
    <Panel
      titulo="Cumplimiento por corte"
      subtitulo={`${proceso === "Todos" ? "Toda la institución" : proceso} · haga clic en un punto para ver ese corte`}
      icono={Activity}
    >
      {datos.length === 0 ? (
        <Vacio texto="Sin histórico para este filtro." />
      ) : (
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={datos}
              margin={{ top: 10, right: 8, bottom: 0, left: -12 }}
              onClick={(estado) => {
                // Recharts 3: el evento trae el índice del punto activo (ya no `activePayload`).
                const i = Number((estado as { activeIndex?: number | string | null }).activeIndex);
                const p = Number.isInteger(i) ? datos[i] : undefined;
                if (p) onSeleccionar(p.anio, p.mes);
              }}
              style={{ cursor: "pointer" }}
            >
              <defs>
                <linearGradient id="gradCumpl" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={COLOR.acento} stopOpacity={0.28} />
                  <stop offset="100%" stopColor={COLOR.acento} stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke={COLOR.rejilla} strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="corte" tick={EJE} tickLine={false} axisLine={{ stroke: COLOR.rejilla }} interval="preserveStartEnd" minTickGap={18} />
              <YAxis yAxisId="pct" domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} tickFormatter={(v) => `${v}%`} tick={EJE} tickLine={false} axisLine={false} width={44} />
              <YAxis yAxisId="n" orientation="right" tick={EJE} tickLine={false} axisLine={false} width={34} allowDecimals={false} />
              <Tooltip
                cursor={{ stroke: COLOR.acento, strokeOpacity: 0.25 }}
                content={({ active, payload }) => {
                  const p = active ? (payload?.[0]?.payload as SeguimientoTendenciaPunto | undefined) : undefined;
                  if (!p) return null;
                  return (
                    <TooltipCaja>
                      <p className="mb-1 font-bold text-slate-900">{p.corte}</p>
                      <p>
                        Cumplimiento: <strong>{p.cumplimiento_pct === null ? "—" : `${p.cumplimiento_pct}%`}</strong>
                      </p>
                      <p className="text-emerald-700">Reportados: {p.reportados}</p>
                      <p className="text-amber-700">Pendientes: {p.pendientes}</p>
                    </TooltipCaja>
                  );
                }}
              />
              <Bar yAxisId="n" dataKey="pendientes" name="Pendientes" fill={COLOR.pendiente} fillOpacity={0.45} radius={[4, 4, 0, 0]} maxBarSize={22} />
              <Area yAxisId="pct" type="monotone" dataKey="cumplimiento_pct" name="Cumplimiento" stroke={COLOR.acento} strokeWidth={2.5} fill="url(#gradCumpl)" dot={{ r: 3, fill: "#fff", stroke: COLOR.acento, strokeWidth: 2 }} activeDot={{ r: 5 }} connectNulls />
              {sel && sel.cumplimiento_pct !== null && (
                <ReferenceDot yAxisId="pct" x={sel.corte} y={sel.cumplimiento_pct} r={8} fill={COLOR.marca} stroke="#fff" strokeWidth={3} />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
      <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-slate-500">
        <span className="inline-flex items-center gap-1.5"><span className="h-0.5 w-4 rounded bg-poli-blue" /> % cumplimiento (eje izq.)</span>
        <span className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-amber-400/60" /> Pendientes (eje der.)</span>
      </div>
    </Panel>
  );
}

// ─── Distribución por estado ─────────────────────────────────────────────────

export function EstadoDonut({ kpis }: { kpis: SeguimientoKpis }) {
  const partes = [
    { nombre: "Reportados", valor: kpis.reportados, color: COLOR.reportado },
    { nombre: "Pendientes", valor: kpis.pendientes, color: COLOR.pendiente },
    { nombre: "No aplica", valor: kpis.no_aplica, color: COLOR.noAplica },
  ];
  const total = partes.reduce((a, p) => a + p.valor, 0);
  return (
    <Panel titulo="Estado de los reportes" subtitulo="Distribución del corte seleccionado" icono={PieIcon}>
      {total === 0 ? (
        <Vacio texto="Sin registros para este filtro." />
      ) : (
        <div className="flex flex-col items-center gap-4">
          <div className="relative h-48 w-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={partes} dataKey="valor" nameKey="nombre" innerRadius={62} outerRadius={88} paddingAngle={2} stroke="none" isAnimationActive={false}>
                  {partes.map((p) => (
                    <Cell key={p.nombre} fill={p.color} />
                  ))}
                </Pie>
                <Tooltip
                  content={({ active, payload }) =>
                    active && payload?.[0] ? (
                      <TooltipCaja>
                        <strong>{String(payload[0].name)}</strong>: {String(payload[0].value)}
                      </TooltipCaja>
                    ) : null
                  }
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-bold text-slate-900" style={{ fontVariantNumeric: "tabular-nums" }}>
                {kpis.cumplimiento_pct === null ? "—" : `${Math.round(kpis.cumplimiento_pct)}%`}
              </span>
              <span className="text-[11px] text-slate-500">cumplimiento</span>
            </div>
          </div>
          <ul className="w-full space-y-1.5 text-sm">
            {partes.map((p) => (
              <li key={p.nombre} className="flex items-center justify-between gap-3">
                <span className="inline-flex items-center gap-2 text-slate-600">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: p.color }} />
                  {p.nombre}
                </span>
                <span className="font-semibold text-slate-900" style={{ fontVariantNumeric: "tabular-nums" }}>
                  {p.valor}
                  <span className="ml-1.5 text-xs font-normal text-slate-400">{Math.round((p.valor / total) * 100)}%</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Panel>
  );
}

// ─── Por frecuencia ──────────────────────────────────────────────────────────

export function FrecuenciaChart({ datos }: { datos: SeguimientoPorPeriodicidad[] }) {
  return (
    <Panel titulo="Avance por frecuencia" subtitulo="Qué tan al día va cada tipo de periodicidad" icono={BarChart3}>
      {datos.length === 0 ? (
        <Vacio texto="Sin datos para este filtro." />
      ) : (
        <div style={{ height: Math.max(180, datos.length * 54) }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={datos} layout="vertical" margin={{ top: 0, right: 48, bottom: 0, left: 8 }} barSize={20}>
              <CartesianGrid stroke={COLOR.rejilla} strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tick={EJE} tickLine={false} axisLine={false} allowDecimals={false} />
              <YAxis type="category" dataKey="periodicidad" tick={{ ...EJE, fill: "#334155", fontWeight: 600 }} tickLine={false} axisLine={false} width={84} />
              <Tooltip
                cursor={{ fill: "#f8fafc" }}
                content={({ active, payload }) => {
                  const p = active ? (payload?.[0]?.payload as SeguimientoPorPeriodicidad | undefined) : undefined;
                  if (!p) return null;
                  return (
                    <TooltipCaja>
                      <p className="mb-1 font-bold text-slate-900">{p.periodicidad}</p>
                      <p className="text-emerald-700">Reportados: {p.reportados}</p>
                      <p className="text-amber-700">Pendientes: {p.pendientes}</p>
                      <p className="text-slate-500">No aplica: {p.no_aplica}</p>
                      <p className="mt-1 font-semibold">Cumplimiento: {p.cumplimiento_pct === null ? "—" : `${p.cumplimiento_pct}%`}</p>
                    </TooltipCaja>
                  );
                }}
              />
              <Bar dataKey="reportados" stackId="e" fill={COLOR.reportado} name="Reportados" />
              <Bar dataKey="pendientes" stackId="e" fill={COLOR.pendiente} name="Pendientes" />
              <Bar dataKey="no_aplica" stackId="e" fill={COLOR.noAplica} name="No aplica" radius={[0, 6, 6, 0]} label={false} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      <div className="mt-2 flex flex-wrap gap-4 text-xs text-slate-500">
        {[
          ["Reportados", COLOR.reportado],
          ["Pendientes", COLOR.pendiente],
          ["No aplica", COLOR.noAplica],
        ].map(([n, c]) => (
          <span key={n} className="inline-flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-sm" style={{ background: c }} />
            {n}
          </span>
        ))}
      </div>
    </Panel>
  );
}

// ─── Procesos con más pendientes ─────────────────────────────────────────────

export function TopPendientesChart({
  procesos,
  seleccionado,
  onSeleccionar,
}: {
  procesos: SeguimientoProcesoCumplimiento[];
  seleccionado: string;
  onSeleccionar: (proceso: string) => void;
}) {
  const top = [...procesos]
    .filter((p) => p.pendientes > 0)
    .sort((a, b) => b.pendientes - a.pendientes || a.proceso.localeCompare(b.proceso))
    .slice(0, 8)
    .map((p) => ({ proceso: p.proceso, pendientes: p.pendientes, pct: p.cumplimiento_pct }));
  return (
    <Panel titulo="Procesos con más pendientes" subtitulo="Los 8 con más indicadores por reportar · clic para filtrar" icono={ListOrdered}>
      {top.length === 0 ? (
        <Vacio texto="Ningún proceso tiene pendientes en este corte." />
      ) : (
        <div style={{ height: Math.max(180, top.length * 40) }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={top} layout="vertical" margin={{ top: 0, right: 30, bottom: 0, left: 8 }} barSize={18} style={{ cursor: "pointer" }}>
              <CartesianGrid stroke={COLOR.rejilla} strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tick={EJE} tickLine={false} axisLine={false} allowDecimals={false} />
              <YAxis
                type="category"
                dataKey="proceso"
                width={190}
                tickLine={false}
                axisLine={false}
                tick={(props: { x?: number | string; y?: number | string; payload?: { value?: string } }) => {
                  const nombre = String(props.payload?.value ?? "");
                  return (
                    <text x={Number(props.x ?? 0) - 4} y={Number(props.y ?? 0)} dy={4} textAnchor="end" fontSize={11} fill={nombre === seleccionado ? COLOR.marca : "#475569"} fontWeight={nombre === seleccionado ? 700 : 500}>
                      {nombre.length > 28 ? `${nombre.slice(0, 27)}…` : nombre}
                    </text>
                  );
                }}
              />
              <Tooltip
                cursor={{ fill: "#f8fafc" }}
                content={({ active, payload }) => {
                  const p = active ? (payload?.[0]?.payload as (typeof top)[number] | undefined) : undefined;
                  return p ? (
                    <TooltipCaja>
                      <p className="mb-1 font-bold text-slate-900">{p.proceso}</p>
                      <p className="text-amber-700">Pendientes: {p.pendientes}</p>
                      <p>Cumplimiento: {p.pct === null ? "—" : `${p.pct}%`}</p>
                    </TooltipCaja>
                  ) : null;
                }}
              />
              <Bar dataKey="pendientes" radius={[0, 6, 6, 0]} onClick={(d) => onSeleccionar(String((d as unknown as { proceso: string }).proceso))} label={{ position: "right", fontSize: 11, fill: "#475569" }}>
                {top.map((p) => (
                  <Cell key={p.proceso} fill={p.proceso === seleccionado ? COLOR.marca : COLOR.pendiente} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </Panel>
  );
}
