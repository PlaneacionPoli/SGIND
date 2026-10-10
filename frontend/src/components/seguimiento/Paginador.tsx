"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

interface Props {
  /** Página actual, base 0. */
  page: number;
  pageSize: number;
  total: number;
  onPage: (page: number) => void;
  onPageSize?: (size: number) => void;
  sizes?: number[];
  /** Nombre de lo que se pagina, para el texto «Mostrando 1–25 de 264 registros». */
  etiqueta?: string;
}

/** Páginas visibles: primera, última y una ventana alrededor de la actual, con «…». */
export function ventanaPaginas(actual: number, total: number): Array<number | "…"> {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i);
  const set = new Set([0, total - 1, actual - 1, actual, actual + 1]);
  if (actual <= 2) [1, 2, 3].forEach((n) => set.add(n));
  if (actual >= total - 3) [total - 2, total - 3, total - 4].forEach((n) => set.add(n));
  const orden = Array.from(set).filter((n) => n >= 0 && n < total).sort((a, b) => a - b);
  const out: Array<number | "…"> = [];
  orden.forEach((n, i) => {
    if (i > 0 && n - orden[i - 1] > 1) out.push("…");
    out.push(n);
  });
  return out;
}

export function Paginador({ page, pageSize, total, onPage, onPageSize, sizes = [10, 25, 50, 100], etiqueta = "registros" }: Props) {
  const totalPaginas = Math.max(1, Math.ceil(total / pageSize));
  const desde = total === 0 ? 0 : page * pageSize + 1;
  const hasta = Math.min(total, (page + 1) * pageSize);
  const btn =
    "inline-flex h-8 min-w-8 items-center justify-center rounded-lg px-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-40";

  return (
    <nav aria-label="Paginación" className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-4 py-3 text-sm">
      <p className="text-slate-500">
        Mostrando <strong className="font-semibold text-slate-800">{desde}–{hasta}</strong> de{" "}
        <strong className="font-semibold text-slate-800">{total}</strong> {etiqueta}
      </p>
      <div className="flex flex-wrap items-center gap-3">
        {onPageSize && (
          <label className="flex items-center gap-2 text-slate-500">
            Filas
            <select
              value={pageSize}
              onChange={(e) => onPageSize(Number(e.target.value))}
              className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-sm text-slate-700"
            >
              {sizes.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
        )}
        <div className="flex items-center gap-1">
          <button type="button" aria-label="Página anterior" disabled={page === 0} onClick={() => onPage(page - 1)} className={`${btn} text-slate-600 hover:bg-slate-100`}>
            <ChevronLeft className="h-4 w-4" />
          </button>
          {ventanaPaginas(page, totalPaginas).map((n, i) =>
            n === "…" ? (
              <span key={`e${i}`} className="px-1 text-slate-400" aria-hidden>
                …
              </span>
            ) : (
              <button
                key={n}
                type="button"
                aria-label={`Página ${n + 1}`}
                aria-current={n === page ? "page" : undefined}
                onClick={() => onPage(n)}
                className={`${btn} ${n === page ? "bg-poli-navy text-white shadow-sm" : "text-slate-600 hover:bg-slate-100"}`}
              >
                {n + 1}
              </button>
            ),
          )}
          <button type="button" aria-label="Página siguiente" disabled={page >= totalPaginas - 1} onClick={() => onPage(page + 1)} className={`${btn} text-slate-600 hover:bg-slate-100`}>
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </nav>
  );
}
