"use client";

import { useState } from "react";
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
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Evaluación de Indicadores y Métricas — Modelo CNA</h2>
        <p className="mt-1 text-slate-600">
          Politécnico Grancolombiano · Gerencia de Planeación · Medición y Mejora
        </p>
      </div>

      <div className="flex gap-2">
        {(["indicadores", "metricas"] as const).map((v) => (
          <button
            key={v}
            type="button"
            onClick={() => setVista(v)}
            className={`rounded-lg px-5 py-2 text-sm font-semibold ${
              vista === v ? "bg-poli-navy text-white" : "bg-slate-100 text-slate-600"
            }`}
          >
            {v === "indicadores" ? "Indicadores" : "Métricas"}
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
