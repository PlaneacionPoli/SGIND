"use client";

import { RotateCcw } from "lucide-react";

interface CmiFiltersProps {
  anio: number;
  /** Se conservan por compatibilidad con el llamador; el corte semestral
   * (Junio/Diciembre) esta oculto por ahora — siempre se usa Diciembre. */
  corte?: string;
  anios: number[];
  cortes?: string[];
  onAnioChange: (anio: number) => void;
  onCorteChange?: (corte: string) => void;
  onReset?: () => void;
  /** "Cierre PDI 2022-2025" — resultado final por indicador (hoja Cierre PDI). */
  rango?: boolean;
  onSelectRango?: () => void;
}

export function CmiFilters({
  anio,
  anios,
  onAnioChange,
  onReset,
  rango = false,
  onSelectRango,
}: CmiFiltersProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_2px_12px_rgba(26,58,92,0.06)]">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-bold uppercase tracking-wide text-slate-700">Filtros</h3>
        {onReset && (
          <button
            type="button"
            onClick={onReset}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-poli-navy transition hover:bg-slate-50"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Restablecer
          </button>
        )}
      </div>
      <div>
        <p className="mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-500">Año de corte</p>
        <div className="inline-flex flex-wrap gap-1 rounded-xl bg-slate-100 p-1">
          {anios.map((y) => {
            const active = !rango && anio === y;
            return (
              <button
                key={y}
                type="button"
                onClick={() => onAnioChange(y)}
                className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                  active
                    ? "bg-poli-navy text-white shadow-md"
                    : "text-slate-600 hover:bg-white hover:text-slate-900"
                }`}
              >
                {y}
              </button>
            );
          })}
          {onSelectRango && (
            <button
              type="button"
              onClick={onSelectRango}
              className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                rango
                  ? "bg-poli-navy text-white shadow-md"
                  : "text-slate-600 hover:bg-white hover:text-slate-900"
              }`}
            >
              Cierre PDI 2022-2025
            </button>
          )}
        </div>
      </div>
      {/* Corte semestral (Junio/Diciembre) oculto por ahora — se usa siempre Diciembre. */}
    </div>
  );
}
