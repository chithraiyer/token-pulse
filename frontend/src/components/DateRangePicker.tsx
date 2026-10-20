import { isoDaysAgo, todayIso } from "../lib/format";

export interface DateRange {
  start: string;
  end: string;
}

const PRESETS: { label: string; days: number }[] = [
  { label: "14d", days: 14 },
  { label: "30d", days: 30 },
  { label: "90d", days: 90 },
];

export function DateRangePicker({
  value,
  onChange,
}: {
  value: DateRange;
  onChange: (r: DateRange) => void;
}) {
  return (
    <div className="range-picker">
      <div className="range-presets">
        {PRESETS.map((p) => (
          <button
            key={p.label}
            type="button"
            onClick={() => onChange({ start: isoDaysAgo(p.days), end: todayIso() })}
          >
            {p.label}
          </button>
        ))}
      </div>
      <label>
        From
        <input
          type="date"
          value={value.start}
          max={value.end}
          onChange={(e) => onChange({ ...value, start: e.target.value })}
        />
      </label>
      <label>
        To
        <input
          type="date"
          value={value.end}
          min={value.start}
          max={todayIso()}
          onChange={(e) => onChange({ ...value, end: e.target.value })}
        />
      </label>
    </div>
  );
}
