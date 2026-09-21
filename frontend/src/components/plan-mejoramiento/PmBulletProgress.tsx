interface PmBulletProgressProps {
  meta: number | null;
  ejecucion: number | null;
  metaFmt: string;
  ejecucionFmt: string;
  color?: string;
}

/** Barra "bullet chart": compara la ejecución (barra de color) contra la
 * meta (marca vertical) en una sola pieza visual — reemplaza dos columnas
 * numéricas sueltas de Meta/Ejecución y hace visible la brecha entre ambas. */
export function PmBulletProgress({
  meta,
  ejecucion,
  metaFmt,
  ejecucionFmt,
  color = "#1A3A5C",
}: PmBulletProgressProps) {
  if (meta == null && ejecucion == null) {
    // Meta no numérica ("Línea base"…): se muestra el texto en vez de perderla.
    return metaFmt !== "—" ? (
      <span className="text-[11px] text-slate-500">Meta: {metaFmt}</span>
    ) : (
      <span className="text-xs text-slate-400">—</span>
    );
  }

  const scale = Math.max(meta ?? 0, ejecucion ?? 0, 1) * 1.15;
  const fillPct = ejecucion != null ? Math.min(100, (ejecucion / scale) * 100) : 0;
  const metaPct = meta != null ? Math.min(100, (meta / scale) * 100) : null;

  return (
    <div className="w-36">
      <div className="relative h-2 rounded-full bg-slate-100">
        <div className="h-2 rounded-full" style={{ width: `${fillPct}%`, backgroundColor: color }} />
        {metaPct != null && (
          <div
            className="absolute top-1/2 h-3 w-0.5 -translate-y-1/2 rounded-full bg-slate-700"
            style={{ left: `${metaPct}%` }}
            title={`Meta: ${metaFmt}`}
          />
        )}
      </div>
      <div className="mt-1 flex justify-between text-[10px] text-slate-500">
        <span>Ejec {ejecucionFmt}</span>
        <span>Meta {metaFmt}</span>
      </div>
    </div>
  );
}
