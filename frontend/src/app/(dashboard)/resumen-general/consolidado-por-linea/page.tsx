"use client";

import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { FlorEstrategica } from "@/components/ui/FlorEstrategica";
import { fetchResumenCompleto } from "@/lib/api";
import { STRATEGIC_LINES } from "@/lib/strategic-lines";
import { useAuthReady } from "@/stores/auth-store";

export default function ConsolidadoPorLineaPage() {
  const router = useRouter();
  const { ready, isAuthenticated } = useAuthReady();

  const resumenQuery = useQuery({
    queryKey: ["resumen-completo", "consolidado-por-linea"],
    queryFn: () => fetchResumenCompleto({ anio: 2025, vista: "consolidado", rango: true }),
    enabled: ready && isAuthenticated,
  });

  const cumplimientoPorLinea = Object.fromEntries(
    (resumenQuery.data?.fichas ?? []).map((f) => [
      STRATEGIC_LINES.find((l) => l.label.toLowerCase() === f.linea.toLowerCase())?.slug ?? f.linea,
      f.cumplimiento,
    ])
  );

  function goToLinea(slug: string) {
    router.push(`/resumen-general/consolidado-por-linea/linea/${slug}`);
  }

  function goToResumenGeneral() {
    router.push("/resumen-general");
  }

  return (
    <div className="space-y-6 animate-in fade-in-50 slide-in-from-bottom-2 duration-500">
      <div className="flex items-center justify-between gap-3 text-sm text-slate-500">
        <button
          type="button"
          onClick={goToResumenGeneral}
          className="inline-flex items-center gap-1 font-medium text-poli-navy hover:underline"
        >
          ← Resumen General
        </button>
        <span className="text-slate-300">/</span>
        <span className="font-semibold text-slate-700">Consolidado por Línea</span>
      </div>

      <div className="rounded-xl bg-gradient-to-r from-slate-900 to-slate-800 px-6 py-6 text-center text-white shadow-md">
        <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-widest text-blue-200">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          Sistema de Indicadores Institucionales
        </p>
        <h1 className="mt-2 text-3xl font-black uppercase tracking-wide text-white">
          Cierre PDI 2022-2025
        </h1>
        <p className="mt-1 text-sm text-slate-300">
          Seleccione una línea estratégica para ver Retos, Proyectos PMO e Indicadores CMI, o toque el
          centro para volver al Resumen General.
        </p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <FlorEstrategica
          onSelectLinea={goToLinea}
          onSelectCentro={goToResumenGeneral}
          cumplimientoPorLinea={cumplimientoPorLinea}
        />
      </div>
    </div>
  );
}
