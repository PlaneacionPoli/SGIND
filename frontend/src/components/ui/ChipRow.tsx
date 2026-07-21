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
          className="rounded-[10px] px-3 pb-3 pt-3.5 text-center"
          style={{
            background: `linear-gradient(180deg, ${chip.color}14 0%, ${chip.color}05 100%)`,
            border: `1px solid ${chip.color}30`,
            borderTopWidth: 4,
            borderTopColor: chip.color,
            boxShadow: `0 2px 8px ${chip.color}1A`,
          }}
        >
          <div className="text-[1.85rem] font-extrabold leading-none" style={{ color: chip.color }}>
            {chip.value}
          </div>
          <div className="mt-[5px] text-xs font-semibold tracking-wide text-[#4F6781]">{chip.label}</div>
        </div>
      ))}
    </div>
  );
}
