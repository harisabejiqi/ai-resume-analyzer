import { useEffect, useState, type ReactNode } from "react";
import type { Analysis, JobMatch } from "../types";

interface Props {
  analysis: Analysis;
  cvScore: number;
  jobMatch: JobMatch | null;
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
      setValue(target * (1 - Math.pow(1 - t, 3)));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return value;
}

function Detail({ icon, value }: { icon: ReactNode; value: string | null }) {
  return (
    <span className="inline-flex min-w-0 items-center gap-1.5 text-sm text-surface-700">
      <span className="shrink-0 text-surface-700/70">{icon}</span>
      <span className={value ? "truncate text-surface-900" : "italic text-surface-700/70"}>
        {value ?? "Not found"}
      </span>
    </span>
  );
}

const iconProps = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  className: "h-4 w-4",
  "aria-hidden": true,
};

function tone(score: number) {
  if (score >= 70) return { ring: "text-success-500", label: "Strong" };
  if (score >= 40) return { ring: "text-warning-500", label: "Needs work" };
  return { ring: "text-danger-500", label: "Weak" };
}

function ScoreRing({ title, score, caption }: { title: string; score: number | null; caption: string }) {
  const animated = useCountUp(score ?? 0);
  const pct = Math.max(0, Math.min(100, animated));
  const t = score === null ? { ring: "text-surface-300", label: "Not scored" } : tone(score);

  return (
    <div className="flex items-center gap-4">
      <div className="relative h-28 w-28 shrink-0">
        <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
          <circle cx="50" cy="50" r="42" fill="none" strokeWidth="9" className="stroke-surface-200" />
          <circle
            cx="50"
            cy="50"
            r="42"
            fill="none"
            strokeWidth="9"
            strokeLinecap="round"
            strokeDasharray={TRACK}
            strokeDashoffset={TRACK - (TRACK * pct) / 100}
            stroke="currentColor"
            className={t.ring}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-display text-3xl font-semibold tabular-nums text-surface-900">
            {score === null ? "-" : Math.round(pct)}
          </span>
          <span className="text-[10px] uppercase tracking-wide text-surface-700">
            {score === null ? "n/a" : "/ 100"}
          </span>
        </div>
      </div>
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-surface-700">{title}</p>
        <p className={`mt-0.5 text-sm font-semibold ${t.ring}`}>{t.label}</p>
        <p className="mt-0.5 max-w-[11rem] text-xs leading-relaxed text-surface-700">{caption}</p>
      </div>
    </div>
  );
}

export default function ResultHeader({ analysis, cvScore, jobMatch }: Props) {
  return (
    <section className="flex flex-col gap-6 rounded-2xl bg-surface-0 p-6 shadow-sm ring-1 shadow-surface-900/[0.03] ring-surface-200/80 sm:flex-row sm:items-center sm:justify-between sm:p-8">
      <div className="min-w-0">
        <p className="text-xs font-medium uppercase tracking-wide text-brand-600">
          Candidate
        </p>
        <h2 className="mt-1 truncate font-display text-2xl font-semibold tracking-tight text-surface-900 sm:text-3xl">
          {analysis.name ?? "Unnamed candidate"}
        </h2>
        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2">
          <Detail
            value={analysis.email}
            icon={
              <svg {...iconProps}>
                <rect x="3" y="5" width="18" height="14" rx="2" />
                <path d="m3 7 9 6 9-6" />
              </svg>
            }
          />
          <Detail
            value={analysis.phone}
            icon={
              <svg {...iconProps}>
                <path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z" />
              </svg>
            }
          />
          <Detail
            value={
              analysis.experience_years > 0
                ? `${analysis.experience_years} years experience`
                : null
            }
            icon={
              <svg {...iconProps}>
                <rect x="3" y="7" width="18" height="13" rx="2" />
                <path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
            }
          />
          <Detail
            value={`${analysis.word_count} words`}
            icon={
              <svg {...iconProps}>
                <path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
                <path d="M14 3v6h6M8 13h8M8 17h5" />
              </svg>
            }
          />
        </div>
      </div>

      <div className="flex shrink-0 flex-col gap-5 sm:items-start lg:flex-row lg:gap-8">
        <ScoreRing
          title="CV quality"
          score={cvScore}
          caption={jobMatch ? "Your CV on its own." : "Your CV on its own. Add a job description to see a job match."}
        />
        {jobMatch && (
          <ScoreRing
            title="Job match"
            score={jobMatch.score}
            caption={
              jobMatch.score === null
                ? "Job description too short to score."
                : jobMatch.reliability === "low"
                  ? "Low reliability: short job description."
                  : "Textual similarity to this posting."
            }
          />
        )}
      </div>
    </section>
  );
}
