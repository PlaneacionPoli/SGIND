"use client";

import { CircleAlert, CircleCheck, ClipboardList } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { OMMatrizResponse } from "@/lib/types";
import type { EstadoOM } from "./utils";

/** Anillo de cobertura: indicadores en riesgo que ya tienen una OM activa. */
function Anillo({ pct }: { pct: number | null }) {
  const r = 34;
  const c = 2 * Math.PI * r;
  const valor = Math.max(0, Math.min(100, pct ?? 0));
  const color = pct === null ? "#cbd5e1" : pct >= 80 ? "#10b981" : pct >= 40 ? "#f59e0b" : "#f43f5e";
  return (
    <svg width="84" height="84" viewBox="0 0 84 84" role="img" aria-label={`Cobertura de OM ${pct ?? "sin dato"}%`} className="shrink-0">
      <circle cx="42" cy="42" r={r} fill="none" stroke="#f1f5f9" strokeWidth="9" />
      <circle cx="42" cy="42" r={r} fill="none" stroke={color} strokeWidth="9" strokeLinecap="round" strokeDasharray={`${(valor / 100) * c} ${c}`} transform="rotate(-90 42 42)" />
      <text x="42" y="47" textAnchor="middle" className="fill-slate-900 text-[17px] font-bold" style={{ fontVariantNumeric: "tabular-nums" }}>
        {pct === null ? "—" : `${Math.round(pct)}%`}
      </text>
    </svg>
  );
}

function Tarjeta({
  etiqueta,
  valor,
  detalle,
  icono: Icono,
  tono,
  destacada = false,
}: {
  etiqueta: string;
  valor: number;
  detalle: string;
  icono: LucideIcon;
  tono: "rose" | "blue" | "emerald";
  destacada?: boolean;
}) {
  const estilo = {
    rose: { icono: "bg-rose-50 text-rose-600", borde: "border-rose-200 ring-1 ring-rose-100" },
    blue: { icono: "bg-blue-50 text-blue-600", borde: "border-slate-200/80" },
    emerald: { icono: "bg-emerald-50 text-emerald-600", borde: "border-slate-200/80" },
  }[tono];
  return (
    <div className={`rounded-2xl border bg-white p-5 shadow-card ${destacada ? estilo.borde : "border-slate-200/80"}`}>
      <div className="flex items-center gap-2">
        <span className={`flex h-8 w-8 items-center justify-center rounded-lg ${estilo.icono}`}>
          <Icono className="h-4 w-4" aria-hidden />
        </span>
        <p className="text-sm font-semibold text-slate-600">{etiqueta}</p>
      </div>
      <p className="mt-3 text-4xl font-bold tracking-tight text-slate-900" style={{ fontVariantNumeric: "tabular-nums" }}>
        {valor}
      </p>
      <p className="mt-1 text-xs text-slate-500">{detalle}</p>
    </div>
  );
}

interface Props {
  kpis: OMMatrizResponse["kpis"];
  conteo: Record<EstadoOM, number>;
}

export function KpisOM({ kpis, conteo }: Props) {
  const total = conteo.sin_om + conteo.en_gestion + conteo.cerrada;
  const cobertura = total > 0 ? (conteo.en_gestion / total) * 100 : null;
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <Tarjeta
        etiqueta="Sin OM"
        valor={conteo.sin_om}
        icono={CircleAlert}
        tono="rose"
        destacada={conteo.sin_om > 0}
        detalle={`de ${total} indicadores en riesgo (${kpis.peligro ?? 0} en Peligro${kpis.alerta ? ` · ${kpis.alerta} en Alerta` : ""})`}
      />
      <Tarjeta
        etiqueta="En gestión"
        valor={conteo.en_gestion}
        icono={ClipboardList}
        tono="blue"
        detalle={kpis.avance_om_promedio != null ? `Avance promedio de las OM: ${kpis.avance_om_promedio}%` : "Sin avance reportado en Kawak"}
      />
      <Tarjeta etiqueta="Cerradas" valor={conteo.cerrada} icono={CircleCheck} tono="emerald" detalle="OM cerradas en este corte" />
      <div className="flex items-center gap-4 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-card">
        <Anillo pct={cobertura} />
        <div>
          <p className="text-sm font-semibold text-slate-600">Cobertura OM</p>
          <p className="mt-1 text-xs leading-snug text-slate-500">
            {conteo.en_gestion} de {total} indicadores en riesgo con una OM activa
          </p>
        </div>
      </div>
    </div>
  );
}
