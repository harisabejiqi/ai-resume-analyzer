import { useEffect, useState } from "react";

export interface RadarDatum {
  label: string;
  value: number;
}

interface Props {
  data: RadarDatum[];
  max?: number;

  color?: string;
  size?: number;
}

const RINGS = [0.25, 0.5, 0.75, 1];

function pointOnAxis(
  cx: number,
  cy: number,
  radius: number,
  index: number,
  count: number,
  ratio: number,
) {
  const angle = (-90 + (360 / count) * index) * (Math.PI / 180);
  return [
    cx + radius * ratio * Math.cos(angle),
    cy + radius * ratio * Math.sin(angle),
  ] as const;
}

export default function RadarChart({
  data,
  max = 100,
  color = "var(--color-brand-500)",
  size = 240,
}: Props) {
  const [grow, setGrow] = useState(0);

  useEffect(() => {
    let raf = 0;
    let start: number | null = null;
    const duration = 700;
    const tick = (ts: number) => {
      if (start === null) start = ts;
      const t = Math.min(1, (ts - start) / duration);
      setGrow(1 - Math.pow(1 - t, 3));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [data]);

  const cx = size / 2;
  const cy = size / 2;
  const radius = size / 2 - 34;
  const n = data.length;

  const padX = 56;

  const valuePoints = data.map((d, i) =>
    pointOnAxis(cx, cy, radius, i, n, (Math.max(0, Math.min(max, d.value)) / max) * grow),
  );
  const polygon = valuePoints.map((p) => p.join(",")).join(" ");

  return (
    <svg
      viewBox={`${-padX} 0 ${size + padX * 2} ${size}`}
      className="h-auto w-full max-w-[340px]"
      role="img"
      aria-label={`Radar chart: ${data
        .map((d) => `${d.label} ${Math.round(d.value)}`)
        .join(", ")}`}
    >

      {RINGS.map((r) => (
        <polygon
          key={r}
          points={data
            .map((_, i) => pointOnAxis(cx, cy, radius, i, n, r).join(","))
            .join(" ")}
          fill="none"
          className="stroke-surface-200"
          strokeWidth="1"
        />
      ))}

      {data.map((d, i) => {
        const [ex, ey] = pointOnAxis(cx, cy, radius, i, n, 1);
        const [lx, ly] = pointOnAxis(cx, cy, radius + 18, i, n, 1);
        const anchor =
          Math.abs(lx - cx) < 4 ? "middle" : lx > cx ? "start" : "end";
        return (
          <g key={d.label}>
            <line
              x1={cx}
              y1={cy}
              x2={ex}
              y2={ey}
              className="stroke-surface-200"
              strokeWidth="1"
            />
            <text
              x={lx}
              y={ly}
              textAnchor={anchor}
              dominantBaseline="middle"
              className="fill-surface-700 text-[10px] font-medium"
            >
              {d.label}
            </text>
          </g>
        );
      })}

      <polygon points={polygon} fill={color} fillOpacity={0.18} stroke={color} strokeWidth="2" />
      {valuePoints.map((p, i) => (
        <circle key={i} cx={p[0]} cy={p[1]} r="3" fill={color} />
      ))}
    </svg>
  );
}
