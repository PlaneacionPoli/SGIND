"use client";

import { RotateCcw } from "lucide-react";

interface CmiFiltersProps {
  anio: number;
  corte: string;
  anios: number[];
  cortes: string[];
  onAnioChange: (anio: number) => void;
  onCorteChange: (corte: string) => void;
  onReset?: () => void;
}

export function CmiFilters({
  anio,
  corte,
  anios,
  cortes,
  onAnioChange,
  onCorteChange,
  onReset,
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
      <div className="grid gap-5 sm:grid-cols-2">
        <SegmentedGroup
          label="Año de corte"
          value={anio}
          options={anios.map((y) => ({ value: y, label: String(y) }))}
          onChange={(v) => onAnioChange(Number(v))}
        />
        <SegmentedGroup
          label="Corte semestral"
          value={corte}
          options={cortes.map((c) => ({ value: c, label: c }))}
          onChange={onCorteChange}
        />
      </div>
    </div>
  );
}

function SegmentedGroup<T extends string | number>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (v: T) => void;
}) {
  return (
    <div>
      <p className="mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-500">{label}</p>
      <div className="inline-flex flex-wrap gap-1 rounded-xl bg-slate-100 p-1">
        {options.map((opt) => {
          const active = opt.value === value;
          return (
            <button
              key={String(opt.value)}
              type="button"
              onClick={() => onChange(opt.value)}
              className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                active
                  ? "bg-poli-navy text-white shadow-md"
                  : "text-slate-600 hover:bg-white hover:text-slate-900"
              }`}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
