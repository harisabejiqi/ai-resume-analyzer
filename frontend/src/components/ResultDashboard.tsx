import { useState, type ReactNode } from "react";
import { useLocation, Navigate, Link } from "react-router-dom";
import clsx from "clsx";
import type { AnalyzeResponse } from "../types";
import ResultHeader from "./ResultHeader";
import ScoreBreakdown from "./ScoreBreakdown";
import SkillsBadges from "./SkillsBadges";
import EducationList from "./EducationList";
import WorkExperienceList from "./WorkExperienceList";
import Suggestions from "./Suggestions";
import GrammarCheck from "./GrammarCheck";
import CvSummary from "./CvSummary";
import ReadabilityChecks from "./ReadabilityChecks";
import JobMatchPanel from "./JobMatchPanel";
import Card from "./ui/Card";

interface Tab {
  id: string;
  label: string;
  content: ReactNode;
}

export default function ResultDashboard() {
  const location = useLocation();
  const data = location.state as AnalyzeResponse | null;
  const [mode, setMode] = useState<"cv" | "job">("cv");
  const [active, setActive] = useState("breakdown");

  if (!data) {
    return <Navigate to="/" replace />;
  }

  if (!data.cv_quality) {
    return (
      <Card className="flex flex-col items-center px-6 py-12 text-center">
        <h1 className="text-base font-medium text-surface-900">Saved in an older format</h1>
        <p className="mt-1 max-w-sm text-sm text-surface-700">
          This analysis was made before CV quality and job match were scored separately.
          Upload the CV again to see the new results.
        </p>
        <Link to="/" className="mt-4 text-sm font-medium text-brand-600 hover:text-brand-700">
          Analyze a resume
        </Link>
      </Card>
    );
  }

  const { analysis, cv_quality, job_match } = data;
  const grammarCount = data.grammar?.available ? data.grammar.issue_count : 0;
  const failedChecks = cv_quality.checks.filter((c) => !c.passed).length;

  const tabs: Tab[] = [
    {
      id: "breakdown",
      label: "Score Breakdown",
      content: <ScoreBreakdown data={data} />,
    },
    {
      id: "overview",
      label: "Summary & statistics",
      content: <CvSummary summary={cv_quality.summary} statistics={cv_quality.statistics} />,
    },
    {
      id: "checks",
      label: `Readability (${failedChecks})`,
      content: <ReadabilityChecks checks={cv_quality.checks} />,
    },
    {
      id: "suggestions",
      label: `Suggestions (${cv_quality.suggestions.length})`,
      content: <Suggestions suggestions={cv_quality.suggestions} />,
    },
    {
      id: "grammar",
      label: `Grammar (${grammarCount})`,
      content: <GrammarCheck grammar={data.grammar} />,
    },
    {
      id: "profile",
      label: "Profile",
      content: (
        <div className="grid gap-4 md:grid-cols-2">
          <SkillsBadges technical={analysis.skills.technical} soft={analysis.skills.soft} />
          <EducationList education={analysis.education} />
          <div className="md:col-span-2">
            <WorkExperienceList workExperience={analysis.work_experience} />
          </div>
        </div>
      ),
    },
  ];

  const current = tabs.find((t) => t.id === active) ?? tabs[0];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl font-semibold tracking-tight text-surface-900">
          Analysis result
        </h1>
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:text-brand-700"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-4 w-4"
          >
            <polyline points="15 18 9 12 15 6" />
          </svg>
          Analyze another
        </Link>
      </div>

      <ResultHeader analysis={analysis} cvScore={cv_quality.score} jobMatch={job_match} />

      <div
        role="group"
        aria-label="Result section"
        className="inline-flex rounded-xl bg-surface-100 p-1 ring-1 ring-surface-200"
      >
        {([
          ["cv", "My CV"],
          ["job", "Job match"],
        ] as const).map(([id, label]) => (
          <button
            key={id}
            type="button"
            aria-pressed={mode === id}
            onClick={() => setMode(id)}
            className={clsx(
              "rounded-lg px-4 py-2 text-sm font-medium transition-colors sm:px-6",
              mode === id
                ? "bg-surface-0 text-brand-600 shadow-sm ring-1 ring-surface-200"
                : "text-surface-700 hover:text-surface-900",
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {mode === "job" ? (
        <JobMatchPanel
          jobMatch={job_match}
          jd={data.job_description}
          candidateYears={analysis.experience_years}
        />
      ) : (
        <section className="rounded-2xl bg-surface-0 p-4 shadow-sm ring-1 shadow-surface-900/[0.03] ring-surface-200/80 sm:p-8">
          <div
            role="tablist"
            aria-label="Analysis sections"
            className="-mx-4 flex overflow-x-auto overflow-y-hidden border-b border-surface-200 px-4 sm:mx-0 sm:px-0"
          >
            {tabs.map((t) => (
              <button
                key={t.id}
                role="tab"
                id={`tab-${t.id}`}
                aria-selected={t.id === current.id}
                aria-controls={`panel-${t.id}`}
                onClick={() => setActive(t.id)}
                className={clsx(
                  "-mb-px shrink-0 whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium transition-colors sm:px-5 sm:text-base",
                  t.id === current.id
                    ? "border-brand-600 text-brand-600"
                    : "border-transparent text-surface-700 hover:text-surface-900",
                )}
              >
                {t.label}
              </button>
            ))}
          </div>
          <div
            role="tabpanel"
            id={`panel-${current.id}`}
            aria-labelledby={`tab-${current.id}`}
            className="mt-6"
          >
            {current.content}
          </div>
        </section>
      )}
    </div>
  );
}
