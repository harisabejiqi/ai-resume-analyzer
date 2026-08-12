import type { ScoreBreakdown as BreakdownType } from "../types";
import Card from "./ui/Card";

interface Props {
  breakdown: BreakdownType;
}

const labels: Record<string, string> = {
  skills: "Skills",
  education: "Education",
  experience: "Experience",
  relevance: "Job relevance",
};

function toneFor(value: number) {
  if (value >= 70) return "bg-success-500";
  if (value >= 40) return "bg-warning-500";
  return "bg-danger-500";
}

export default function ScoreBreakdown({ breakdown }: Props) {
  const entries = Object.entries(breakdown) as [string, number][];

  return (
    <Card className="mt-4">
      <h2 className="text-sm font-medium uppercase tracking-wide text-surface-700">
        Breakdown
      </h2>
      <div className="mt-4 space-y-4">
        {entries.map(([key, value]) => (
          <div key={key}>
            <div className="mb-1.5 flex items-baseline justify-between text-sm">
              <span className="font-medium text-surface-900">
                {labels[key] ?? key}
              </span>
              <span className="tabular-nums text-surface-700">
                {Math.round(value)}%
              </span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-200">
              <div
                className={`h-full rounded-full transition-[width] duration-700 ease-out ${toneFor(value)}`}
                style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
