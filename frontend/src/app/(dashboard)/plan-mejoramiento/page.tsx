"use client";

import { useState } from "react";
import { ClipboardList, LineChart } from "lucide-react";
import { PmIndicadoresTab } from "@/components/plan-mejoramiento/PmIndicadoresTab";
import { PmMetricasTab } from "@/components/plan-mejoramiento/PmMetricasTab";

type Vista = "indicadores" | "metricas";

/**
 * Plan de Mejoramiento — rediseñado como 2 vistas planas (Indicadores /
 * Métricas), paridad con streamlit_app/pages/plan_mejoramiento.py del legacy
 * (rediseño de sep-2026, ver docs/migration/PLAN_MIGRACION_PRIORIZADO.md
 * ítem 0). Reemplaza la vista anterior de "Indicadores CNA por cierre +
 * Acciones de Mejora", que correspondía a un diseño ya reemplazado en el
 * legacy.
 */
export default function PlanMejoramientoPage() {
  const [vista, setVista] = useState<Vista>("indicadores");

  return (
    <div className="space-y-6">
      <div className="rounded-xl bg-gradient-to-r from-slate-900 to-slate-800 p-6 text-white shadow-md">
        <p className="text-xs font-semibold uppercase tracking-widest text-blue-200">Modelo CNA</p>
        <h2 className="mt-1 text-2xl font-bold">Evaluación de Indicadores y Métricas</h2>
        <p className="mt-1 text-sm text-slate-300">
          Politécnico Grancolombiano · Gerencia de Planeación · Medición y Mejora
        </p>
      </div>

      <div className="flex gap-2">
        {(
          [
            { key: "indicadores", label: "Indicadores", Icon: ClipboardList },
            { key: "metricas", label: "Métricas", Icon: LineChart },
          ] as const
        ).map(({ key, label, Icon }) => (
          <button
            key={key}
            type="button"
            onClick={() => setVista(key)}
            className={`inline-flex items-center gap-2 rounded-lg px-5 py-2 text-sm font-semibold transition-colors ${
              vista === key
                ? "bg-poli-navy text-white shadow-sm"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {vista === "indicadores" ? <PmIndicadoresTab /> : <PmMetricasTab />}

      <p className="text-xs text-slate-400">
        Panel generado a partir de &quot;Indicadores Plan de Mejoramiento&quot; y &quot;Resultados Consolidados
        CNA – Métricas&quot; · Politécnico Grancolombiano
      </p>
    </div>
  );
}
