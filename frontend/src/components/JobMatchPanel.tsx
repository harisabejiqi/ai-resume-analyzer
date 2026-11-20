import { Link } from "react-router-dom";
import type { JobDescription, JobMatch } from "../types";
import Card from "./ui/Card";
import JobRequirements from "./JobRequirements";
import MissingKeywords from "./MissingKeywords";
import Suggestions from "./Suggestions";

interface Props {
  jobMatch: JobMatch | null;
  jd: JobDescription | null;
  candidateYears: number;
}

function evidenceTone(score: number) {
  if (score >= 60) return "bg-success-100 text-success-500";
  if (score >= 40) return "bg-warning-100 text-warning-500";
  return "bg-danger-100 text-danger-500";
}

export default function JobMatchPanel({ jobMatch, jd, candidateYears }: Props) {
  if (!jobMatch || !jd) {
    return (
      <Card className="flex flex-col items-center px-6 py-12 text-center">
        <h2 className="text-base font-medium text-surface-900">No job description</h2>
        <p className="mt-1 max-w-sm text-sm text-surface-700">
          Paste a job posting together with your CV to see how closely your CV matches it.
        </p>
        <Link
          to="/"
          className="mt-4 text-sm font-medium text-brand-600 hover:text-brand-700"
        >
          Analyze with a job description
        </Link>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl bg-surface-50 px-4 py-3 text-sm leading-relaxed text-surface-700 ring-1 ring-surface-200/80">
        {jobMatch.disclaimer}
      </div>

      {jobMatch.reliability_note && (
        <div
          role="status"
          className="rounded-xl bg-warning-100 px-4 py-3 text-sm font-medium leading-relaxed text-warning-500 ring-1 ring-inset ring-warning-500/30"
        >
          {jobMatch.reliability_note}
        </div>
      )}

      <JobRequirements jd={jd} skillMatch={jobMatch.skill_match} candidateYears={candidateYears} />

      {jobMatch.evidence.length > 0 && (
        <Card>
          <h2 className="text-sm font-medium uppercase tracking-wide text-surface-700">
            Evidence per requirement
          </h2>
          <p className="mt-1 text-xs text-surface-700/80">
            For each requirement, the line of your CV that matches it best. These
            percentages are measured differently from the job match score, so they
            are usually lower.
          </p>
          <ul className="mt-4 space-y-3">
            {jobMatch.evidence.map((e, i) => (
              <li key={i} className="rounded-lg bg-surface-50 p-4 ring-1 ring-surface-200/80">
                <div className="flex items-start gap-3">
                  <p className="min-w-0 flex-1 text-sm font-medium text-surface-900">
                    {e.requirement}
                  </p>
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold tabular-nums ${evidenceTone(e.score)}`}
                  >
                    {Math.round(e.score)}%
                  </span>
                </div>
                <p className="mt-2 border-l-2 border-brand-200 pl-3 text-sm leading-relaxed text-surface-700">
                  {e.best_chunk}
                </p>
              </li>
            ))}
          </ul>
        </Card>
      )}

      <MissingKeywords keywords={jobMatch.missing_keywords} />

      {jobMatch.suggestions.length > 0 && (
        <Suggestions title="Suggestions for this job" suggestions={jobMatch.suggestions} />
      )}
    </div>
  );
}
