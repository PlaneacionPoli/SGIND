interface KPICardProps {
  label: string;
  value: string | number;
  unit?: string;
  trend?: string;
}

export function KPICard({ label, value, unit, trend }: KPICardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-bold text-poli-navy">
        {value}
        {unit && <span className="ml-1 text-base font-normal text-slate-400">{unit}</span>}
      </p>
      {trend && <p className="mt-1 text-xs text-slate-400">{trend}</p>}
    </div>
  );
}
