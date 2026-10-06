"use client";

import { useQuery } from "@tanstack/react-query";
import { usePathname, useRouter } from "next/navigation";
import { fetchMarcos, moduloHref } from "@/lib/pdi";
import { useAuthReady } from "@/stores/auth-store";

/** Cambio rápido de PDI dentro de un módulo (mantiene la ruta, cambia ?pdi=). */
export function PdiChip({ pdi, className = "" }: { pdi: string; className?: string }) {
  const { isAuthenticated } = useAuthReady();
  const pathname = usePathname();
  const router = useRouter();
  const { data: marcos } = useQuery({
    queryKey: ["marcos", "PDI"],
    queryFn: () => fetchMarcos("PDI"),
    enabled: isAuthenticated,
  });

  return (
    <label className={`inline-flex items-center gap-2 text-xs font-semibold ${className}`}>
      <span className="uppercase tracking-wider opacity-80">PDI</span>
      <select
        value={pdi}
        onChange={(e) => router.push(moduloHref(pathname, e.target.value))}
        className="rounded-full border border-current/30 bg-white/10 px-3 py-1 text-sm font-semibold [&>option]:text-slate-900"
        aria-label="Cambiar PDI"
      >
        {(marcos ?? []).map((m) => (
          <option key={m.version_id} value={m.version_id}>
            {m.nombre}
            {m.estado === "activo" ? " (vigente)" : ""}
          </option>
        ))}
        {!marcos?.some((m) => m.version_id === pdi) && <option value={pdi}>{pdi}</option>}
      </select>
    </label>
  );
}
