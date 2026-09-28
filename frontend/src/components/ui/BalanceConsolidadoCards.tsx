import { Flag, Star, Target } from "lucide-react";
import type { ResumenMindmapLinea, ResumenTarjetasConsolidado } from "@/lib/types";

export interface PeorObjetivo {
  slug: string;
  linea: string;
  color: string;
  codigo: string;
  label: string;
  cumplimiento: number;
}

interface BalanceConsolidadoCardsProps {
  data: ResumenTarjetasConsolidado;
  alcanceGlobal: number;
  lineas: ResumenMindmapLinea[];
  peorObjetivo?: PeorObjetivo | null;
  onVerLinea?: (slug: string) => void;
  actualizadoEn?: string | null;
}

/** Reemplaza los 3 bloques de prosa del Informe Estratégico (ver
 * InformeEstrategicoConsolidado, ahora en desuso en Consolidado) por
 * tarjetas — mismos hechos, solo re-presentados: `data` viene de
 * scripts/generar_narrativa_estrategica.py (TARJETAS_CONSOLIDADO), y la
 * alerta de la tercera tarjeta se calcula en vivo a partir del mindmap
 * (peor sub-línea por debajo del umbral de alerta), no está hardcodeada. */
export function BalanceConsolidadoCards({
  data,
  alcanceGlobal,
  lineas,
  peorObjetivo,
  onVerLinea,
  actualizadoEn,
}: BalanceConsolidadoCardsProps) {
  const enMeta = alcanceGlobal >= 100;

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className="flex flex-col rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-2 flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <Target size={18} className="shrink-0 text-slate-400" />
            <div>
              <p className="text-xs font-bold uppercase tracking-wide text-slate-700">Balance Consolidado</p>
              <p className="text-[11px] text-slate-400">Ponderación global institucional</p>
            </div>
          </div>
          <span className="shrink-0 text-xl font-black text-poli-blue">{alcanceGlobal.toFixed(1)}%</span>
        </div>
        <span
          className={`mb-3 inline-block w-fit rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${
            enMeta ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"
          }`}
        >
          {enMeta ? "En meta global" : "En riesgo"}
        </span>

        <p className="mb-1.5 text-[11px] font-semibold text-slate-500">
          Distribución y desempeño por eje · {lineas.length} líneas activas
        </p>
        <div className="mb-3 flex h-2 w-full overflow-hidden rounded-full">
          {lineas.map((l) => (
            <span key={l.slug} title={l.label} className="h-full flex-1" style={{ backgroundColor: l.color }} />
          ))}
        </div>

        <div className="mb-3 flex-1 space-y-2">
          {data.balance.logros_destacados.map((item) => (
            <div
              key={item.label}
              className="flex items-center justify-between gap-2 rounded-lg bg-slate-50 px-3 py-2"
            >
              <span className="text-xs font-semibold text-slate-600">{item.label}</span>
              <span className="text-xs font-bold text-slate-800">{item.valor}</span>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between border-t border-slate-100 pt-2 text-[11px] text-slate-400">
          <span>{actualizadoEn ? `Actualizado: ${actualizadoEn}` : ""}</span>
          <span className="font-semibold text-slate-500">{data.balance.auditoria}</span>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-3 flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <Star size={18} className="shrink-0 text-amber-400" />
            <div>
              <p className="text-xs font-bold uppercase tracking-wide text-slate-700">Logros Clave en Cifras</p>
              <p className="text-[11px] text-slate-400">Impacto acumulado del cuatrienio</p>
            </div>
          </div>
          <span className="shrink-0 rounded bg-slate-800 px-2 py-0.5 text-[10px] font-bold text-white">
            {data.cifras.length} Hitos
          </span>
        </div>
        <div className="grid grid-cols-2 gap-2">
          {data.cifras.map((c) => (
            <div key={c.titulo} className="rounded-lg bg-slate-50 p-3">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">{c.titulo}</p>
              <p className="text-lg font-black leading-tight text-slate-800">{c.valor}</p>
              <p className="text-[10px] text-emerald-600">{c.detalle}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-3 flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <Flag size={18} className="shrink-0 text-pink-500" />
            <div>
              <p className="text-xs font-bold uppercase tracking-wide text-slate-700">Foco y Retos Priorizados</p>
              <p className="text-[11px] text-slate-400">Ventana 2026-2030 &amp; mitigaciones</p>
            </div>
          </div>
          <span className="shrink-0 rounded bg-slate-800 px-2 py-0.5 text-[10px] font-bold text-white">
            {data.retos_priorizados.length} Acciones
          </span>
        </div>
        <div className="mb-3 space-y-2">
          {data.retos_priorizados.map((r) => (
            <div key={r.codigo} className="flex items-start gap-2">
              <span className="mt-0.5 flex h-5 w-8 shrink-0 items-center justify-center rounded bg-poli-blue/10 text-[10px] font-bold text-poli-blue">
                {r.codigo}
              </span>
              <div>
                <p className="text-xs font-bold leading-tight text-slate-700">{r.titulo}</p>
                <p className="text-[11px] leading-snug text-slate-500">{r.detalle}</p>
              </div>
            </div>
          ))}
        </div>
        {peorObjetivo && (
          <div className="rounded-lg border border-pink-200 bg-pink-50 p-3">
            <p className="text-[10px] font-bold uppercase tracking-wide text-pink-600">
              Alerta: {peorObjetivo.codigo} {peorObjetivo.label}
            </p>
            <p className="text-xs text-pink-700">
              {peorObjetivo.linea} · {peorObjetivo.cumplimiento.toFixed(1)}% de cumplimiento
            </p>
            {onVerLinea && (
              <button
                type="button"
                onClick={() => onVerLinea(peorObjetivo.slug)}
                className="mt-2 rounded-md bg-pink-600 px-3 py-1 text-[11px] font-semibold text-white transition hover:bg-pink-700"
              >
                Ver Línea
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
