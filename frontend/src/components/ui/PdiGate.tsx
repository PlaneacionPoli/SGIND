"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { usePathname } from "next/navigation";
import { PdiChip } from "@/components/ui/PdiChip";
import { fetchMarcos, seleccionPdiHref, usePdiSeleccionado } from "@/lib/pdi";
import { useAuthReady } from "@/stores/auth-store";

/**
 * Exige un PDI elegido (?pdi=) antes de renderizar el módulo. Sin PDI →
 * redirige al selector. PDI desconocido o sin datos cargados → aviso, nunca
 * datos de otro ciclo. Debe ir dentro de <Suspense> (usa useSearchParams).
 */
export function PdiGate({ children }: { children: (pdi: string) => ReactNode }) {
  const pdi = usePdiSeleccionado();
  const pathname = usePathname();
  const { isAuthenticated } = useAuthReady();
  const { data: marcos, isLoading } = useQuery({
    queryKey: ["marcos", "PDI"],
    queryFn: () => fetchMarcos("PDI"),
    enabled: isAuthenticated,
  });

  if (!pdi) return <p className="text-sm text-slate-500">Redirigiendo a la selección de PDI…</p>;
  // Sin sesión, la página misma decide (p. ej. Resumen muestra login de desarrollo).
  if (!isAuthenticated) return <>{children(pdi)}</>;
  if (isLoading || !marcos) return <p className="text-sm text-slate-500">Cargando ciclo PDI…</p>;

  const marco = marcos.find((m) => m.version_id === pdi);
  if (marco?.datos_disponibles) return <>{children(pdi)}</>;

  return (
    <div className="mx-auto max-w-2xl space-y-4 rounded-2xl border border-amber-200 bg-amber-50 p-6">
      <PdiChip pdi={pdi} className="text-amber-900" />
      <h2 className="text-lg font-bold text-amber-950">
        {marco ? `${marco.nombre}: información en preparación` : `PDI no reconocido: ${pdi}`}
      </h2>
      <p className="text-sm text-amber-900">
        {marco
          ? "El catálogo de indicadores, líneas, objetivos y metas de este ciclo aún no está cargado en el sistema. Mientras tanto puedes consultar otro PDI."
          : "El ciclo indicado no existe en el registro de PDI."}
      </p>
      <Link href={seleccionPdiHref(pathname)} className="inline-block text-sm font-semibold text-blue-700 hover:underline">
        ← Volver a la selección de PDI
      </Link>
    </div>
  );
}
