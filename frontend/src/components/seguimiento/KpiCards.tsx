"use client";

import { CircleCheck, Clock, CircleMinus, TrendingDown, TrendingUp, Minus } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Area, AreaChart, ResponsiveContainer } from "recharts";
import type { SeguimientoKpis, SeguimientoTendenciaPunto } from "@/lib/types";
import { COLOR } from "./constants";

function Anillo({ pct }: { pct: number | null }) {
  const r = 34;
  const c = 2 * Math.PI * r;
  const valor = Math.max(0, Math.min(100, pct ?? 0));
  const color = pct === null ? COLOR.noAplica : pct >= 100 ? COLOR.reportado : pct >= 80 ? COLOR.pendiente : COLOR.critico;
  return (
    <svg width="84" height="84" viewBox="0 0 84 84" role="img" aria-label={`Cumplimiento ${pct ?? "sin dato"}%`} className="shrink-0">
      <circle cx="42" cy="42" r={r} fill="none" stroke="#f1f5f9" strokeWidth="9" />
      <circle
        cx="42"
        cy="42"
        r={r}
        fill="none"
        stroke={color}
        strokeWidth="9"
        strokeLinecap="round"
        strokeDasharray={`${(valor / 100) * c} ${c}`}
        transform="rotate(-90 42 42)"
      />
      <text x="42" y="47" textAnchor="middle" className="fill-slate-900 text-[17px] font-bold" style={{ fontVariantNumeric: "tabular-nums" }}>
        {pct === null ? "—" : `${Math.round(pct)}%`}
      </text>
    </svg>
  );
}

function Variacion({ pp }: { pp: number | null }) {
  if (pp === null) return <span className="text-xs text-slate-400">Sin corte previo</span>;
  const Icono = pp > 0 ? TrendingUp : pp < 0 ? TrendingDown : Minus;
  const clase = pp > 0 ? "bg-emerald-50 text-emerald-700" : pp < 0 ? "bg-rose-50 text-rose-700" : "bg-slate-100 text-slate-600";
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${clase}`}>
      <Icono className="h-3 w-3" aria-hidden />
      {pp > 0 ? "+" : ""}
      {pp} pp
      <span className="font-normal opacity-70">vs. corte anterior</span>
    </span>
  );
}

function Mini({
  etiqueta,
  valor,
  detalle,
  icono: Icono,
  tono,
}: {
  etiqueta: string;
  valor: number;
  detalle: string;
  icono: LucideIcon;
  tono: "emerald" | "amber" | "slate";
}) {
  const t = {
    emerald: { chip: "bg-emerald-50 text-emerald-600", barra: "bg-emerald-500" },
    amber: { chip: "bg-amber-50 text-amber-600", barra: "bg-amber-400" },
    slate: { chip: "bg-slate-100 text-slate-500", barra: "bg-slate-300" },
  }[tono];
  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-5 shadow-card">
      <span className={`absolute inset-x-0 top-0 h-1 ${t.barra}`} aria-hidden />
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">{etiqueta}</p>
        <span className={`flex h-9 w-9 items-center justify-center rounded-xl ${t.chip}`}>
          <Icono className="h-5 w-5" aria-hidden />
        </span>
      </div>
      <p className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl" style={{ fontVariantNumeric: "tabular-nums" }}>
        {valor.toLocaleString("es-CO")}
      </p>
      <p className="mt-1 text-xs text-slate-500">{detalle}</p>
    </div>
  );
}

export function KpiCards({ kpis, tendencia }: { kpis: SeguimientoKpis; tendencia: SeguimientoTendenciaPunto[] }) {
  const serie = tendencia.slice(-10).map((t) => ({ corte: t.corte, v: t.cumplimiento_pct ?? 0 }));
  const exigibles = kpis.registros - kpis.no_aplica;
  return (
    <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
      <div className="col-span-2 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-card xl:col-span-1">
        <div className="flex items-center gap-4">
          <Anillo pct={kpis.cumplimiento_pct} />
          <div className="min-w-0">
            <p className="text-sm font-medium text-slate-500">Cumplimiento del corte</p>
            <div className="mt-1.5">
              <Variacion pp={kpis.variacion_pp} />
            </div>
          </div>
        </div>
        {serie.length > 1 && (
          <div className="mt-3 h-10" aria-hidden>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={serie} margin={{ top: 2, right: 0, bottom: 0, left: 0 }}>
                <defs>
                  <linearGradient id="spark" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={COLOR.acento} stopOpacity={0.35} />
                    <stop offset="100%" stopColor={COLOR.acento} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Area type="monotone" dataKey="v" stroke={COLOR.acento} strokeWidth={2} fill="url(#spark)" isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
      <Mini etiqueta="Reportados" valor={kpis.reportados} detalle={`de ${exigibles.toLocaleString("es-CO")} indicadores exigibles`} icono={CircleCheck} tono="emerald" />
      <Mini
        etiqueta="Pendientes"
        valor={kpis.pendientes}
        detalle={kpis.pendientes === 0 ? "Nada por reportar" : `en ${kpis.procesos_con_pendientes} ${kpis.procesos_con_pendientes === 1 ? "proceso" : "procesos"}`}
        icono={Clock}
        tono="amber"
      />
      <Mini etiqueta="No aplica" valor={kpis.no_aplica} detalle={`${kpis.registros.toLocaleString("es-CO")} registros en el corte`} icono={CircleMinus} tono="slate" />
    </div>
  );
}
