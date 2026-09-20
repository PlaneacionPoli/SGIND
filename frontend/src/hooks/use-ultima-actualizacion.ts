"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchExcelFiles } from "@/lib/api";

const CONSOLIDADO_NAME = "Resultados Consolidados.xlsx";
// El pipeline se ejecuta manualmente hoy (sin cron real, ver
// docs/tecnico/09-gaps-y-riesgos.md G-01) — 35 días da margen sobre la
// cadencia mensual declarada en config/settings.toml antes de marcar la
// fecha como "desactualizada".
export const DIAS_ALERTA_DESACTUALIZADO = 35;

/** Metadata del archivo consolidado que alimenta los módulos de indicadores. */
export function useUltimaActualizacion() {
  return useQuery({
    queryKey: ["excel-files-last-update"],
    queryFn: fetchExcelFiles,
    staleTime: 5 * 60 * 1000,
    select: (files) => files.find((f) => f.name === CONSOLIDADO_NAME) ?? null,
    retry: 1,
  });
}
