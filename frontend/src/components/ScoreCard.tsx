import { useEffect, useState } from "react";
import type { Score } from "../types";
import Card from "./ui/Card";

interface Props {
  score: Score;
  hasJobDescription: boolean;
}

const TRACK = 264;

function useCountUp(target: number, duration = 1200) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    let raf = 0;
    let start: number | null = null;
    const tick = (ts: number) => {
      if (start === null) start = ts;
      const t = Math.min(1, (ts - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(target * eased);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return value;
}

export default function ScoreCard({ score, hasJobDescription }: Props) {
  const animated = useCountUp(score.total_score);
  const pct = Math.max(0, Math.min(100, animated));
  const offset = TRACK - (TRACK * pct) / 100;

  const ring =
    score.total_score >= 70
      ? "text-success-500"
      : score.total_score >= 40
        ? "text-warning-500"
        : "text-danger-500";

  const label =
    score.total_score >= 70
      ? "Strong"
      : score.total_score >= 40
        ? "Needs work"
        : "Weak";

  return (
    <Card className="text-center">
      <h2 className="text-sm font-medium uppercase tracking-wide text-surface-700">
        Overall score
      </h2>
      <div className="relative mx-auto mt-4 h-44 w-44">
        <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
          <circle
            cx="50"
            cy="50"
            r="42"
            fill="none"
            strokeWidth="8"
            className="stroke-surface-200"
          />
          <circle
            cx="50"
            cy="50"
            r="42"
            fill="none"
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={TRACK}
            strokeDashoffset={offset}
            className={`${ring} transition-[stroke-dashoffset] duration-100 ease-out`}
            stroke="currentColor"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-display text-4xl font-semibold tabular-nums text-surface-900">
            {Math.round(pct)}
          </span>
          <span className={`mt-0.5 text-xs font-medium ${ring}`}>{label}</span>
        </div>
      </div>
      {hasJobDescription ? (
        <p className="mt-4 text-sm text-surface-700">
          Job match:{" "}
          <span className="font-semibold text-surface-900">
            {score.match_score}%
          </span>
        </p>
      ) : (
        <p className="mt-4 text-sm text-surface-700">
          Add a job description to unlock match scoring.
        </p>
      )}
    </Card>
  );
}
