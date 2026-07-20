interface CmiMetricCardProps {
  title: string;
  value: string;
  subtitle: string;
  icon: string;
  color: string;
}

export function CmiMetricCard({ title, value, subtitle, icon, color }: CmiMetricCardProps) {
  const isLong = value.length > 10;
  return (
    <div
      className="relative overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_12px_rgba(26,58,92,0.08)] transition hover:shadow-[0_6px_20px_rgba(26,58,92,0.12)]"
      style={{ borderTopWidth: 4, borderTopColor: color }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</p>
          <p
            className={`mt-2 font-extrabold leading-tight ${isLong ? "text-lg" : "text-3xl leading-none"}`}
            style={{ color }}
          >
            {value}
          </p>
          <p className="mt-2 text-xs text-slate-500">{subtitle}</p>
        </div>
        <span
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-xl"
          style={{ backgroundColor: `${color}18` }}
        >
          {icon}
        </span>
      </div>
    </div>
  );
}
