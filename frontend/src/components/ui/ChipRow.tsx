export interface ChipItem {
  value: number | string;
  label: string;
  color: string;
}

interface ChipRowProps {
  chips: ChipItem[];
}

export function ChipRow({ chips }: ChipRowProps) {
  if (!chips.length) return null;
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
      {chips.map((chip) => (
        <div
          key={chip.label}
          className="rounded-xl border bg-gradient-to-b from-white to-slate-50 px-3 py-4 text-center shadow-sm"
          style={{ borderColor: `${chip.color}30`, borderTopWidth: 4, borderTopColor: chip.color }}
        >
          <div className="text-3xl font-extrabold leading-none" style={{ color: chip.color }}>
            {chip.value}
          </div>
          <div className="mt-1 text-xs font-semibold tracking-wide text-slate-500">{chip.label}</div>
        </div>
      ))}
    </div>
  );
}
