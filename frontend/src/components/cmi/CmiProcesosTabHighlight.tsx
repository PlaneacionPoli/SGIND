"use client";

const HIGHLIGHTS: Record<string, string> = {
  resumen:
    "Vista global de CMI por Procesos con KPIs ejecutivos, distribución por nivel, comparativo histórico y tarjetas por tipo de proceso.",
  procesos:
    "Explora el comportamiento de procesos y unidades organizacionales, con desglose por subproceso y cumplimiento promedio.",
  listado:
    "Consulta indicadores activos, filtra por proceso y estado, abre fichas técnicas y exporta a CSV o Excel.",
  alertas:
    "Centro de alertas con indicadores en Peligro y Alerta, filtrables por proceso y severidad.",
  analisis:
    "Propuesta de acción, variación por proceso, histórico de indicadores, calidad de datos y análisis heurístico.",
};

export function CmiProcesosTabHighlight({ tab }: { tab: string }) {
  const text = HIGHLIGHTS[tab];
  if (!text) return null;
  return (
    <div className="rounded-xl border border-blue-100 bg-gradient-to-r from-blue-50/80 to-slate-50 px-5 py-4 shadow-[0_2px_8px_rgba(26,58,92,0.04)]">
      <p className="text-sm leading-relaxed text-slate-700">{text}</p>
    </div>
  );
}
