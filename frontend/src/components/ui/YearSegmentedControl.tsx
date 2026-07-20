interface YearSegmentedControlProps {
  years: number[];
  anio: number;
  rango?: boolean;
  onChange: (anio: number) => void;
  onSelectRango?: () => void;
}

export function YearSegmentedControl({ years, anio, rango = false, onChange, onSelectRango }: YearSegmentedControlProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {years.map((y) => (
        <button
          key={y}
          type="button"
          onClick={() => onChange(y)}
          className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
            !rango && anio === y
              ? "bg-poli-navy text-white shadow-sm"
              : "bg-slate-100 text-slate-600 hover:bg-slate-200"
          }`}
        >
          {y}
        </button>
      ))}
      {onSelectRango && (
        <button
          type="button"
          onClick={onSelectRango}
          className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
            rango
              ? "bg-poli-navy text-white shadow-sm"
              : "bg-slate-100 text-slate-600 hover:bg-slate-200"
          }`}
        >
          Consolidado 2022-2025
        </button>
      )}
    </div>
  );
}
