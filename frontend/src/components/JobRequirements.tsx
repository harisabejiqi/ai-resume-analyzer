import type { JobDescription } from "../types";
import Card from "./ui/Card";

interface Props {
  jd: JobDescription;
  candidateYears: number;
}

function CheckIcon({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.4"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

function SkillChip({ label, present }: { label: string; present: boolean }) {
  return (
    <span
      className={
        present
          ? "inline-flex items-center gap-1 rounded-full bg-success-100 px-2.5 py-1 text-xs font-medium text-success-500 ring-1 ring-inset ring-success-500/20"
          : "inline-flex items-center gap-1 rounded-full bg-danger-100 px-2.5 py-1 text-xs font-medium text-danger-500 ring-1 ring-inset ring-danger-500/20"
      }
    >
      {present ? (
        <CheckIcon className="h-3 w-3" />
      ) : (
        <span aria-hidden className="text-sm leading-none">
          +
        </span>
      )}
      {label}
    </span>
  );
}

export default function JobRequirements({ jd, candidateYears }: Props) {
  const { skill_match, experience_required, education_required, qualifications } =
    jd;
  const totalRequired = skill_match.matched.length + skill_match.missing.length;
  const coverage = skill_match.coverage;
  const meetsExperience =
    experience_required != null && candidateYears >= experience_required;

  return (
    <Card accent="info">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-4 w-4 text-brand-600"
            aria-hidden
          >
            <rect x="2" y="7" width="20" height="14" rx="2" />
            <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
          </svg>
          <h2 className="text-sm font-medium uppercase tracking-wide text-surface-700">
            Job requirements
          </h2>
        </div>
        {coverage != null && (
          <span className="rounded-full bg-brand-100 px-2.5 py-1 text-xs font-medium text-brand-700">
            {skill_match.matched.length}/{totalRequired} required skills ·{" "}
            {Math.round(coverage)}% match
          </span>
        )}
      </div>

      {totalRequired > 0 && (
        <div className="mt-5">
          <div className="mb-2 flex items-baseline justify-between">
            <h3 className="text-xs font-medium uppercase tracking-wide text-surface-700">
              Required skills
            </h3>
            <span className="text-xs text-surface-700">
              green = on your resume · red = missing
            </span>
          </div>
          {coverage != null && (
            <div className="mb-3 h-1.5 w-full overflow-hidden rounded-full bg-surface-200">
              <div
                className="h-full rounded-full bg-success-500 transition-[width] duration-700 ease-out"
                style={{ width: `${coverage}%` }}
              />
            </div>
          )}
          <div className="flex flex-wrap gap-2">
            {skill_match.matched.map((s) => (
              <SkillChip key={s} label={s} present />
            ))}
            {skill_match.missing.map((s) => (
              <SkillChip key={s} label={s} present={false} />
            ))}
          </div>
        </div>
      )}

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <div>
          <h3 className="text-xs font-medium uppercase tracking-wide text-surface-700">
            Experience required
          </h3>
          {experience_required != null ? (
            <div className="mt-1.5 flex items-center gap-2">
              <span className="text-sm font-medium text-surface-900">
                {experience_required}+ years
              </span>
              <span
                className={
                  meetsExperience
                    ? "inline-flex items-center gap-1 rounded-full bg-success-100 px-2 py-0.5 text-xs font-medium text-success-500"
                    : "inline-flex items-center gap-1 rounded-full bg-warning-100 px-2 py-0.5 text-xs font-medium text-warning-500"
                }
              >
                {meetsExperience ? (
                  <CheckIcon className="h-3 w-3" />
                ) : null}
                you: {candidateYears} yr{candidateYears === 1 ? "" : "s"}
              </span>
            </div>
          ) : (
            <p className="mt-1.5 text-sm text-surface-700/70">Not specified</p>
          )}
        </div>

        <div>
          <h3 className="text-xs font-medium uppercase tracking-wide text-surface-700">
            Education required
          </h3>
          {education_required.length > 0 ? (
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              {education_required.map((e) => (
                <span
                  key={e}
                  className="rounded-full bg-surface-100 px-2.5 py-1 text-xs font-medium text-surface-900 ring-1 ring-inset ring-surface-200"
                >
                  {e}
                </span>
              ))}
            </div>
          ) : (
            <p className="mt-1.5 text-sm text-surface-700/70">Not specified</p>
          )}
        </div>
      </div>

      {qualifications.length > 0 && (
        <div className="mt-5">
          <h3 className="text-xs font-medium uppercase tracking-wide text-surface-700">
            Qualifications
          </h3>
          <ul className="mt-2 space-y-2">
            {qualifications.map((q, i) => (
              <li
                key={i}
                className="flex items-start gap-2.5 text-sm leading-relaxed text-surface-900"
              >
                <span
                  aria-hidden
                  className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-400"
                />
                <span>{q}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
}
