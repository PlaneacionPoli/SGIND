import type { LucideIcon } from "lucide-react";

interface PanelProps {
  titulo: string;
  subtitulo?: string;
  icono?: LucideIcon;
  acciones?: React.ReactNode;
  className?: string;
  /** Sin relleno interno: para tablas y listas que llegan al borde. */
  sinPadding?: boolean;
  children: React.ReactNode;
}

/** Contenedor común de todas las secciones: mismo borde, sombra, encabezado y espaciado. */
export function Panel({ titulo, subtitulo, icono: Icono, acciones, className = "", sinPadding = false, children }: PanelProps) {
  return (
    <section className={`overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-card ${className}`}>
      <header className="flex flex-wrap items-start justify-between gap-3 px-5 pb-3 pt-4">
        <div className="flex min-w-0 items-start gap-3">
          {Icono && (
            <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-poli-navy-50 text-poli-navy">
              <Icono className="h-4 w-4" aria-hidden />
            </span>
          )}
          <div className="min-w-0">
            <h3 className="text-sm font-bold tracking-tight text-slate-900">{titulo}</h3>
            {subtitulo && <p className="mt-0.5 text-xs leading-snug text-slate-500">{subtitulo}</p>}
          </div>
        </div>
        {acciones && <div className="flex flex-wrap items-center gap-2">{acciones}</div>}
      </header>
      <div className={sinPadding ? "" : "px-5 pb-5"}>{children}</div>
    </section>
  );
}

/** Estado vacío homogéneo para gráficos y listas sin datos. */
export function Vacio({ texto }: { texto: string }) {
  return <p className="rounded-xl bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">{texto}</p>;
}
