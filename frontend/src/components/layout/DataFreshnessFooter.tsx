"use client";

import { DIAS_ALERTA_DESACTUALIZADO, useUltimaActualizacion } from "@/hooks/use-ultima-actualizacion";

/**
 * Pie de página de cada pantalla del dashboard: indica cuándo se actualizó
 * por última vez el archivo consolidado que alimenta los indicadores (el
 * pipeline hoy es manual, sin cron real — ver docs/tecnico/09-gaps-y-riesgos.md G-01).
 * No se muestra en Gestión OM (datos en Postgres, no depende de este archivo).
 */
export function DataFreshnessFooter() {
  const { data: archivo, isLoading, isError } = useUltimaActualizacion();

  if (isLoading || isError || !archivo) return null;

  const modificado = new Date(archivo.modified_at);
  const diasDesactualizado = Math.floor((Date.now() - modificado.getTime()) / 86_400_000);
  const desactualizado = diasDesactualizado > DIAS_ALERTA_DESACTUALIZADO;

  const fechaTexto = modificado.toLocaleString("es-CO", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div
      className={`mt-8 flex items-center gap-1.5 border-t px-1 py-3 text-xs ${
        desactualizado ? "border-amber-200 text-amber-800" : "border-slate-200 text-slate-500"
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${desactualizado ? "bg-amber-500" : "bg-emerald-500"}`} />
      Datos actualizados: {fechaTexto}
      {desactualizado && <span className="font-medium">· revisar pipeline de datos</span>}
    </div>
  );
}
