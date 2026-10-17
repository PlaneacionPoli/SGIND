"use client";

import type { CMIProcesosVistaGlobal } from "@/lib/types";
import { CmiDonutNivelPlotly } from "@/components/cmi/CmiDonutNivelPlotly";
import { CmiMetricCard } from "@/components/cmi/CmiMetricCard";
import { CmiProcesosMixNiveles } from "@/components/cmi/CmiProcesosMixNiveles";
import { CmiProcesosTendenciaMensual } from "@/components/cmi/CmiProcesosTendenciaMensual";
import { fmtNum, fmtPct } from "@/components/cmi/nivelUtils";

interface CmiProcesosResumenTabProps {
  vista: CMIProcesosVistaGlobal;
  /** Mezcla del semáforo por año (cierre anual) del Mapa de procesos. */
  mixNiveles?: Record<string, Record<string, number>>;
  anioParcial?: number | null;
}

/**
 * Resumen ejecutivo: ¿cómo vamos? Una cifra global, su semáforo, cómo se reparte por tipo de proceso
 * y cómo evoluciona (12 meses del año en curso y mezcla por año). El detalle por proceso vive en el
 * Mapa de procesos; los indicadores en riesgo, en Alertas.
 */
export function CmiProcesosResumenTab({ vista, mixNiveles, anioParcial = null }: CmiProcesosResumenTabProps) {
  const { kpis, banner, distribucion_nivel, tipo_proceso_cards, variacion_procesos, brecha_ambiental } = vista;
  const mejoraronProcesos = (variacion_procesos?.mejoraron ?? []).map((r) => ({
    indicador: r.name,
    variacion: r.change,
  }));
  const empeoraronProcesos = (variacion_procesos?.empeoraron ?? []).map((r) => ({
    indicador: r.name,
    variacion: r.change,
  }));

  const conteo = kpis.conteo_estados ?? {};
  const nAlerta = conteo["Alerta"] ?? 0;
  const nPeligro = conteo["Peligro"] ?? 0;

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="rounded-2xl bg-gradient-to-br from-[#173a63] to-[#2d5a8a] p-5 text-white shadow-lg sm:p-6">
        <p className="text-[10px] font-bold uppercase tracking-widest text-white/60">CMI por Procesos</p>
        <h3 className="text-xl font-bold text-white sm:text-2xl">
          {banner.pct_saludable != null
            ? `${fmtNum(banner.pct_saludable)}% de los indicadores opera en niveles saludables`
            : `${banner.anio}`}
        </h3>
        <p className="mt-0.5 text-xs text-white/60">
          {banner.anio} · último reporte de cada indicador (el más reciente, {banner.mes})
        </p>
        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <BannerStat label="Cumplimiento global" value={fmtPct(banner.cumplimiento_global)} large />
          <BannerStat
            label={`vs cierre ${banner.base_anio}`}
            value={banner.variacion_pp != null ? `${banner.variacion_pp > 0 ? "+" : ""}${fmtNum(banner.variacion_pp)} pp` : "—"}
          />
          <BannerStat label="Indicadores" value={String(banner.total_indicadores)} />
          <BannerStat label="En riesgo" value={String(banner.en_riesgo)} />
        </div>
      </div>

      {/* KPIs */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <CmiMetricCard
          title="Indicadores con reporte"
          value={String(kpis.total)}
          subtitle={`${kpis.n_procesos} procesos · ${kpis.n_subprocesos} subprocesos · ${kpis.n_unidades} unidades`}
          icon="📌"
          color="#1D4ED8"
        />
        <CmiMetricCard title="Cumplimiento promedio" value={fmtPct(kpis.promedio)} subtitle="Promedio de indicadores" icon="✔️" color="#047857" />
        <CmiMetricCard title="En alerta" value={String(nAlerta)} subtitle="80% – 99%" icon="⚠️" color="#B45309" />
        <CmiMetricCard title="En peligro" value={String(nPeligro)} subtitle="Menor a 80%" icon="🚨" color="#B71C1C" />
      </div>

      {/* Semáforo + tipo de proceso */}
      <div className="grid gap-5 lg:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <h4 className="mb-3 text-sm font-bold text-slate-800">Distribución por nivel</h4>
          <CmiDonutNivelPlotly data={distribucion_nivel} total={kpis.total} />
        </div>
        <div className="lg:col-span-2">
          <h4 className="mb-3 text-sm font-bold text-slate-800">Cumplimiento por tipo de proceso</h4>
          <div className="grid gap-3 sm:grid-cols-2">
            {tipo_proceso_cards.map((card) => (
              <div
                key={card.tipo}
                className="rounded-2xl border border-slate-200 p-4 shadow-sm"
                style={{ backgroundColor: card.color_light, borderTopWidth: 4, borderTopColor: card.color }}
              >
                <div className="flex items-center gap-2">
                  <span className="text-xl">{card.icon}</span>
                  <span className="text-sm font-bold" style={{ color: card.color }}>
                    {card.tipo}
                  </span>
                </div>
                <p className="mt-3 text-2xl font-bold text-slate-900">{fmtPct(card.cumplimiento)}</p>
                <p className="text-xs text-slate-600">
                  {card.n_indicadores} indicadores · {card.n_riesgo} en riesgo
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Evolución: 12 meses del año en curso (filtro de mes propio) y mezcla por año */}
      <CmiProcesosTendenciaMensual />
      {mixNiveles && <CmiProcesosMixNiveles mix={mixNiveles} anioParcial={anioParcial} />}

      {/* Procesos que más cambian frente al cierre anterior + insight ambiental */}
      {(mejoraronProcesos.length > 0 || empeoraronProcesos.length > 0 || brecha_ambiental) && (
        <div className="grid gap-4 lg:grid-cols-3">
          <VarTable title="Procesos con mayor mejora" rows={mejoraronProcesos} positive />
          <VarTable title="Procesos en mayor riesgo" rows={empeoraronProcesos} positive={false} />
          {brecha_ambiental && (
            <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-3 shadow-sm">
              <div className="mb-1 flex items-center gap-1.5">
                <span className="text-sm">🌱</span>
                <h4 className="text-xs font-bold text-emerald-800">Brecha ambiental crítica</h4>
              </div>
              <p className="text-[11px] leading-snug text-emerald-900/80">{brecha_ambiental.texto}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function BannerStat({ label, value, large }: { label: string; value: string; large?: boolean }) {
  return (
    <div className="rounded-xl bg-white/10 px-3 py-2.5">
      <p className="text-[10px] font-bold uppercase tracking-wider text-white/55">{label}</p>
      <p className={`mt-0.5 font-bold ${large ? "text-2xl" : "text-lg"}`}>{value}</p>
    </div>
  );
}

function VarTable({
  title,
  rows,
  positive,
}: {
  title: string;
  rows: Array<{ indicador: string; variacion: number }>;
  positive: boolean;
}) {
  if (!rows.length) return null;
  const accent = positive ? "#166534" : "#B71C1C";
  const bg = positive ? "#F0FDF4" : "#FFF1F2";
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
      <div className="mb-2 flex items-center gap-1.5 rounded-lg px-2 py-1" style={{ backgroundColor: bg }}>
        <span className="text-xs font-bold" style={{ color: accent }}>
          {positive ? "▲" : "▼"}
        </span>
        <h4 className="text-xs font-bold" style={{ color: accent }}>
          {title}
        </h4>
      </div>
      <ul className="space-y-1.5">
        {rows.slice(0, 5).map((r) => (
          <li key={r.indicador} className="flex items-start justify-between gap-2">
            <span className="truncate text-[11px] leading-tight text-slate-600" title={r.indicador}>
              {r.indicador}
            </span>
            <span className="shrink-0 text-[11px] font-extrabold" style={{ color: accent }}>
              {r.variacion > 0 ? "+" : ""}
              {fmtNum(r.variacion)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
