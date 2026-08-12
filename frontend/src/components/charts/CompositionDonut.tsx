import { useEffect, useState } from "react";

export interface DonutSegment {
  label: string;
  value: number;
  color: string;
}

interface Props {
  segments: DonutSegment[];

  centerValue: number;
  centerLabel?: string;
  size?: number;
}

const R = 42;
const C = 2 * Math.PI * R;

export default function CompositionDonut({
  segments,
  centerValue,
  centerLabel = "total",
  size = 180,
}: Props) {
  const [grow, setGrow] = useState(0);

  useEffect(() => {
    let raf = 0;
    let start: number | null = null;
    const duration = 900;
    const tick = (ts: number) => {
      if (start === null) start = ts;
      const t = Math.min(1, (ts - start) / duration);
      setGrow(1 - Math.pow(1 - t, 3));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [segments]);

  const total = segments.reduce((sum, s) => sum + s.value, 0) || 1;

  const fractions = segments.map((s) => (s.value / total) * grow);
  const arcs = segments.map((segment, i) => ({
    segment,
    len: fractions[i] * C,
    start: fractions.slice(0, i).reduce((sum, f) => sum + f, 0),
  }));

  return (
    <div className="flex flex-col items-center gap-5 sm:flex-row sm:items-center sm:gap-6">
      <div className="relative shrink-0" style={{ width: size, height: size }}>
        <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
          <circle
            cx="50"
            cy="50"
            r={R}
            fill="none"
            strokeWidth="12"
            className="stroke-surface-200"
          />
          {arcs.map(({ segment, len, start }) => (
            <circle
              key={segment.label}
              cx="50"
              cy="50"
              r={R}
              fill="none"
              strokeWidth="12"
              stroke={segment.color}
              strokeDasharray={`${len} ${C - len}`}
              strokeDashoffset={-start * C}
            />
          ))}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-display text-2xl font-semibold tabular-nums text-surface-900">
            {Math.round(centerValue)}
          </span>
          <span className="text-[10px] uppercase tracking-wide text-surface-700">
            {centerLabel}
          </span>
        </div>
      </div>

      <ul className="w-full space-y-2 text-sm">
        {segments.map((s) => (
          <li key={s.label} className="flex items-center justify-between gap-3">
            <span className="flex items-center gap-2 text-surface-900">
              <span
                aria-hidden
                className="h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: s.color }}
              />
              {s.label}
            </span>
            <span className="tabular-nums text-surface-700">
              {Math.round((s.value / total) * 100)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
